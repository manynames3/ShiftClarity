import {it,expect,vi} from 'vitest';
import {act,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import type {PilotController} from './ServerApp';
import {initialDemo} from './domain/demo';
import {freshInputs,draftRule} from './adapters/fixtures';

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
  decide,approve:noop,task:noop,importFile:noop,export:noop,logout:noop,source:noop,propose:noop};
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
  expect(screen.getByRole('status')).toHaveTextContent('saved on the server');
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
 }finally{
  view.unmount();history.replaceState({},'',originalUrl);
  if(show)Object.defineProperty(prototype,'showModal',show);else delete (prototype as unknown as Record<string,unknown>).showModal;
  if(close)Object.defineProperty(prototype,'close',close);else delete (prototype as unknown as Record<string,unknown>).close;
 }
});
