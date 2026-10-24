import {it,expect,vi} from 'vitest';
import {act,render,screen} from '@testing-library/react';
import ServerApp from './ServerApp';
import {initialDemo} from './domain/demo';
import {freshInputs,draftRule} from './adapters/fixtures';
it('ignores a late period response after the reviewer returns to the already loaded run',async()=>{
 const previous=location.href;history.replaceState({},'','/pilot/?view=workspace&run=RUN-ONE');
 const state=initialDemo(freshInputs(),draftRule);state.run!.id='RUN-ONE';
 const snapshot={state,version:1,latest_run_id:'RUN-ONE',cases:[],catalog:{rules:state.inputs.rules,excerpts:state.inputs.excerpts},approval:{version:1,draft:state.draft,ruleHistory:[],approvedFutureRules:[]}};
 const second=structuredClone(snapshot);second.state.run!.id='RUN-TWO';
 let finish!:(response:Response)=>void;const delayed=new Promise<Response>(resolve=>{finish=resolve;});
 const response=(data:unknown)=>new Response(JSON.stringify(data),{status:200});
 vi.stubGlobal('fetch',vi.fn((input:RequestInfo|URL)=>{
  const path=String(input);
  if(path.includes('run_id=RUN-TWO'))return delayed;
  if(path.startsWith('/api/v1/workspace'))return Promise.resolve(response(snapshot));
  if(path==='/api/v1/session')return Promise.resolve(response({actor:'REVIEWER',roles:['reviewer'],csrf:'test',synthetic:true}));
  if(path==='/api/v1/members')return Promise.resolve(response([{actor:'REVIEWER'}]));
  return Promise.resolve(response({settings:{label:'Synthetic agency',default_facility:'FAC-A',version:1},team:{members:2,approvers:1,importers:1},has_import:true,has_review:true,provisioning_available:false}));
 }));
 const view=render(<ServerApp/>);
 try{
  await screen.findByRole('heading',{name:'+$1,760.00'});
  act(()=>{history.pushState({},'','/pilot/?view=workspace&run=RUN-TWO');window.dispatchEvent(new PopStateEvent('popstate'));});
  expect(screen.getByRole('heading',{name:'Opening your workspace'})).toBeInTheDocument();
  act(()=>{history.pushState({},'','/pilot/?view=workspace&run=RUN-ONE');window.dispatchEvent(new PopStateEvent('popstate'));});
  expect(screen.getByRole('heading',{name:'+$1,760.00'})).toBeInTheDocument();
  await act(async()=>{finish(response(second));});
  expect(document.querySelector('.footnote')).toHaveTextContent('RUN-ONE');
  expect(new URL(location.href).searchParams.get('run')).toBe('RUN-ONE');
 }finally{view.unmount();vi.unstubAllGlobals();history.replaceState({},'',previous);}
});
