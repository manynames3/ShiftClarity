import {useEffect,useState} from 'react';
import App from './App';
import type {Demo} from './domain/demo';
import type {Finding,Task,Rule,Excerpt} from './domain/types';
import {Logo} from './components';

type Session={actor:string;roles:string[];csrf:string;synthetic:true};
type Catalog={rules:Rule[];excerpts:Excerpt[]};
type Snapshot={state:Demo;version:number;catalog:Catalog};
export interface PilotController {
 state:Demo;version:number;catalog:Catalog;session:Session;members:string[];
 decide:(f:Finding,action:string,reason:string,owner:string,version:number)=>Promise<void>;
 approve:(action:'approve'|'reject',reason:string)=>Promise<void>;
 task:(t:Task,reason:string,owner:string)=>Promise<void>;
 importFile:(file:File)=>Promise<void>;
 export:()=>Promise<void>;logout:()=>Promise<void>;
 source:(title:string,text:string)=>Promise<void>;
 propose:(supersedes:string,source_excerpt_id:string,rate:string,effective_from:string)=>Promise<void>;
}

export default function ServerApp(){
 const [session,setSession]=useState<Session|null>(null),[snapshot,setSnapshot]=useState<Snapshot|null>(null);
 const [members,setMembers]=useState<string[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState('');
 async function request<T>(path:string,body?:unknown,raw=false):Promise<T>{
  const response=await fetch(path,{method:body===undefined?'GET':'POST',credentials:'same-origin',
   headers:body===undefined?{}:{'Content-Type':'application/json','X-CSRF-Token':session?.csrf||'','Idempotency-Key':crypto.randomUUID(),'X-Data-Classification':'synthetic'},
   ...(body===undefined?{}:{body:raw?String(body):JSON.stringify(body)})});
  if(!response.ok){
   if(response.status===401){setSession(null);setSnapshot(null);}
   const problem=await response.json().catch(()=>({detail:'Request failed.'}));
   throw new Error(problem.detail||'Request failed.');
  }
  return response.json() as Promise<T>;
 }
 async function refresh(){setSnapshot(await request<Snapshot>('/api/v1/workspace'));}
 useEffect(()=>{document.title='ShiftClarity · Synthetic pilot';let live=true;
  void (async()=>{try{
   const response=await fetch('/api/v1/session',{credentials:'same-origin'});
   if(response.status===401)return;
   if(!response.ok)throw new Error('Sign-in service is unavailable.');
   const identity=await response.json() as Session;
   const [workspace,people]=await Promise.all([fetch('/api/v1/workspace'),fetch('/api/v1/members')]);
   if(!workspace.ok||!people.ok)throw new Error('Workspace is unavailable.');
   const data=await workspace.json() as Snapshot,accounts=await people.json() as {actor:string}[];
   if(live){setSession(identity);setSnapshot(data);setMembers(accounts.map(m=>m.actor));}
  }catch(e){if(live)setError((e as Error).message);}finally{if(live)setLoading(false);}})();
  return()=>{live=false;};
 },[]);
 async function write(path:string,body:unknown){
  try{await request<Snapshot>(path,body);await refresh();}catch(e){await refresh().catch(()=>{});throw e;}
 }
 async function importFile(file:File){
  if(file.size>1024*1024)throw new Error('File exceeds the 1 MiB limit.');
  if(!file.name.toLowerCase().endsWith('.json'))throw new Error('Choose a normalized JSON bundle.');
  const imported=await request<{id:string;status:string;help?:string}>('/api/v1/imports',await file.text(),true);
  await refresh();
  if(imported.status!=='validated')throw new Error((imported.help||'Import rejected. Check the template, source controls and registered versions.')+' The prior completed run is retained.');
  const job=await request<{id:string}>('/api/v1/runs',{import_id:imported.id});
  for(let i=0;i<60;i++){
   await new Promise(resolve=>setTimeout(resolve,500));
   const status=await request<{status:string}>('/api/v1/jobs/'+job.id);
   if(status.status==='completed'){await refresh();return;}
   if(status.status==='failed'){await refresh();throw new Error('Run failed; the previous completed result was retained.');}
  }
  throw new Error('The run is still queued. Refresh to check its result; it will continue on the server.');
 }
 if(loading)return <main className="sign-in"><Logo/><h1>Opening your workspace</h1><p role="status">Checking your sign-in…</p></main>;
 if(!session||!snapshot)return <main className="sign-in"><Logo/><div className="eyebrow">Synthetic pilot · Sample workspace</div><h1>Every shift.<br/>Clearly aligned.</h1><p>Sign in with your own demonstration account to review fictional staffing records. Decisions and approved rule versions are saved in your workspace.</p><a className="btn btn-primary" href="/auth/login">Sign in to your workspace</a>{error&&<p role="alert" className="error">{error}</p>}<p className="muted">Individual accounts · Authenticator verification · Synthetic records only</p><a className="text-link" href="/demo/">Open the standalone demo</a></main>;
 const controller:PilotController={
  ...snapshot,session,members,
  decide:(f,action,reason,owner,version)=>write('/api/v1/findings/'+f.id+'/decisions',{action,reason,owner:owner||null,expected_fingerprint:f.fingerprint,expected_version:version,run_id:snapshot.state.run!.id}),
  approve:(action,reason)=>write('/api/v1/rules/'+snapshot.state.draft.id+'/approval',{action,reason,expected_version:snapshot.version}),
  task:(t,reason,owner)=>write('/api/v1/tasks',{task_id:t.id,reason,owner,run_id:snapshot.state.run!.id}),
  importFile,
  source:(title,text)=>write('/api/v1/documents',{title,text,synthetic:true}),
  propose:(supersedes,source_excerpt_id,rate,effective_from)=>write('/api/v1/rules/drafts',{supersedes,source_excerpt_id,rate,effective_from,expected_version:snapshot.version}),
  export:async()=>{
   const response=await fetch('/api/v1/runs/'+snapshot.state.run!.id+'/review-export');
   if(!response.ok)throw new Error('Export unavailable. Refresh your sign-in and run.');
   const url=URL.createObjectURL(await response.blob()),link=document.createElement('a');
   link.href=url;link.download='ShiftClarity-reviewed-findings.csv';link.click();URL.revokeObjectURL(url);
  },
  logout:async()=>{const result=await request<{logout_url:string}>('/auth/logout',{});setSession(null);setSnapshot(null);location.assign(result.logout_url);}
 };
 return <App pilot={controller}/>;
}
