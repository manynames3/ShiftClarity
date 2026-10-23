import {it,expect,vi} from 'vitest';
import {act,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import type {PilotController} from './ServerApp';
import {initialDemo} from './domain/demo';
import {freshInputs,draftRule} from './adapters/fixtures';

it('provides a global sign-out action to persistent pilot users',async()=>{
 const originalUrl=location.href;
 history.replaceState({},'','/pilot/?view=rules');
 const state=initialDemo(freshInputs(),draftRule),noop=async()=>{},logout=vi.fn(noop);
 const pilot:PilotController={state,version:1,catalog:{rules:state.inputs.rules,excerpts:state.inputs.excerpts},
  session:{actor:'DEMO-REVIEWER',roles:['reviewer'],csrf:'test-only',synthetic:true},members:['DEMO-REVIEWER'],
  decide:noop,approve:noop,task:noop,importFile:noop,export:noop,logout,source:noop,propose:noop,api:async<T,>()=>({} as T),uploadTable:noop,runImport:noop,refresh:noop};
 const view=render(<App pilot={pilot}/>);
 try{await userEvent.setup().click(screen.getByRole('button',{name:'Sign out'}));expect(logout).toHaveBeenCalledOnce();}
 finally{view.unmount();history.replaceState({},'',originalUrl);}
});

it('keeps a delayed server review visibly pending and prevents a duplicate submission',async()=>{
 const originalUrl=location.href;
 const prototype=HTMLDialogElement.prototype;
 const show=Object.getOwnPropertyDescriptor(prototype,'showModal'),close=Object.getOwnPropertyDescriptor(prototype,'close');
 Object.defineProperty(prototype,'showModal',{configurable:true,value:function(){this.open=true;}});
 Object.defineProperty(prototype,'close',{configurable:true,value:function(){this.open=false;}});
 history.replaceState({},'','/pilot/?view=evidence&id=FND-001');
 const state=initialDemo(freshInputs(),draftRule);
 let finish!:()=>void;
 const pending=new Promise<void>(resolve=>{finish=resolve;});
 const decide=vi.fn(()=>pending),noop=async()=>{};
 const pilot:PilotController={state,version:1,catalog:{rules:state.inputs.rules,excerpts:state.inputs.excerpts},
  session:{actor:'DEMO-REVIEWER',roles:['reviewer'],csrf:'test-only',synthetic:true},members:['DEMO-REVIEWER'],
  decide,approve:noop,task:noop,importFile:noop,export:noop,logout:noop,source:noop,propose:noop,api:async<T,>()=>({} as T),uploadTable:noop,runImport:noop,refresh:noop};
 const view=render(<App pilot={pilot}/>);
 try{
  const user=userEvent.setup();
  await user.click(screen.getByRole('button',{name:'Confirm discrepancy'}));
  await user.type(screen.getByLabelText('Review reason'),'Checked the fictional agreement and approved hours.');
  await user.click(screen.getByRole('button',{name:'Save review'}));
  const saving=screen.getByRole('button',{name:'Saving…'});
  expect(saving).toBeDisabled();
  expect(screen.getByRole('status')).toHaveTextContent('Saving the review record');
  await user.click(saving);
  expect(decide).toHaveBeenCalledTimes(1);
  await act(async()=>{finish();await pending;});
  expect(screen.getByText('Review record saved on the server. Nothing was sent.').closest('[role=status]')).toBeInTheDocument();
  expect(window.location.search).toBe('?view=workspace&scope=all');
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
 }finally{
  view.unmount();history.replaceState({},'',originalUrl);
  if(show)Object.defineProperty(prototype,'showModal',show);else delete (prototype as unknown as Record<string,unknown>).showModal;
  if(close)Object.defineProperty(prototype,'close',close);else delete (prototype as unknown as Record<string,unknown>).close;
 }
});
