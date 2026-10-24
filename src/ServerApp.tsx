import {useEffect,useRef,useState} from 'react';
import App from './App';
import type {Demo} from './domain/demo';
import type {Finding,Task,Rule,Excerpt} from './domain/types';
import {Logo} from './components';

export type Agency={settings:{label:string;default_facility:string;version:number};team:{members:number;approvers:number;importers:number};has_import:boolean;has_review:boolean;provisioning_available:boolean};
type Session={actor:string;roles:string[];csrf:string;synthetic:true};
type Catalog={rules:Rule[];excerpts:Excerpt[]};
export type FollowupCase={id:string;kind:'finding'|'coverage';facility_id:string;service_from:string;service_to_exclusive:string;reason_code:string;work_ids:string[];last_run_id:string;source_ref:string;selected_source_ref?:string;amount:string|null;status:string;owner:string|null;correction_reference:string|null;verified_run_id:string|null;version:number;updated_at:string};
type ApprovalContext=Pick<Demo,'draft'|'ruleHistory'|'approvedFutureRules'>&{version:number};
type Snapshot={state:Demo;version:number;catalog:Catalog;cases:FollowupCase[];latest_run_id:string;approval:ApprovalContext};
export interface PilotController {
 state:Demo;version:number;catalog:Catalog;session:Session;members:string[];cases:FollowupCase[];latest_run_id:string;
 selectRun:(runId:string)=>Promise<void>;agency?:Agency;approval?:ApprovalContext;
 decide:(f:Finding,action:string,reason:string,owner:string,version:number)=>Promise<void>;
 approve:(action:'approve'|'reject',reason:string)=>Promise<void>;
 task:(t:Task,reason:string,owner:string)=>Promise<void>;
 importFile:(file:File,onProgress?:(message:string)=>void)=>Promise<void>;
 export:()=>Promise<void>;logout:()=>Promise<void>;
 source:(title:string,text:string)=>Promise<void>;
 propose:(supersedes:string,source_excerpt_id:string,rate:string,effective_from:string)=>Promise<void>;
 api:<T>(path:string,body?:unknown,method?:'POST'|'DELETE')=>Promise<T>;
 uploadTable:(session:string,category:string,file:File)=>Promise<void>;
 runImport:(importId:string,onProgress?:(message:string)=>void)=>Promise<void>;
 refresh:()=>Promise<void>;
}

export default function ServerApp(){
 const loadedRun=useRef('');
 const [navigationError,setNavigationError]=useState('');
 const [session,setSession]=useState<Session|null>(null),[snapshot,setSnapshot]=useState<Snapshot|null>(null);
 const [agency,setAgency]=useState<Agency>();
 const [members,setMembers]=useState<string[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState('');
 async function request<T>(path:string,body?:unknown,raw=false,method?:'POST'|'DELETE'):Promise<T>{
  const verb=method||(body===undefined?'GET':'POST');
  const response=await fetch(path,{method:verb,credentials:'same-origin',
   headers:verb==='GET'?{}:{'Content-Type':'application/json','X-CSRF-Token':session?.csrf||'','Idempotency-Key':crypto.randomUUID(),'X-Data-Classification':'synthetic'},
   ...(body===undefined?{}:{body:raw?String(body):JSON.stringify(body)})});
  if(!response.ok){
   if(response.status===401){setSession(null);setSnapshot(null);setError('Your sign-in expired. Sign in to return to this review and check its latest saved state.');}
   const problem=await response.json().catch(()=>({detail:'Request failed.'}));
   throw new Error(problem.detail||'Request failed.');
  }
  return response.json() as Promise<T>;
 }
 const workspacePath=(runId=new URL(location.href).searchParams.get('run'))=>'/api/v1/workspace'+(runId?'?run_id='+encodeURIComponent(runId):'');
 async function refresh(){const selected=new URL(location.href).searchParams.get('run');const [next,people,organization]=await Promise.all([request<Snapshot>(workspacePath(selected)),request<{actor:string}[]>('/api/v1/members'),request<Agency>('/api/v1/agency')]);if(new URL(location.href).searchParams.get('run')===selected)setSnapshot(next);setMembers(people.map(m=>m.actor));setAgency(organization);}
 async function selectRun(runId:string){
  const previousUrl=location.href;
  const next=await request<Snapshot>(workspacePath(runId));
  if(location.href!==previousUrl)return;
  const url=new URL(location.href);url.searchParams.set('run',runId);url.searchParams.set('view','workspace');url.searchParams.delete('id');
  loadedRun.current=runId;setNavigationError('');history.pushState({},'',url);setSnapshot(next);window.dispatchEvent(new PopStateEvent('popstate'));
 }
 useEffect(()=>{if(!session)return;let active=true;const change=()=>{
  const runId=new URL(location.href).searchParams.get('run');if(!runId)return;if(runId===loadedRun.current){setLoading(false);setNavigationError('');return;}
  setLoading(true);setNavigationError('');void request<Snapshot>(workspacePath(runId)).then(next=>{if(active&&new URL(location.href).searchParams.get('run')===runId){loadedRun.current=runId;setSnapshot(next);}}).catch(e=>{if(active&&new URL(location.href).searchParams.get('run')===runId)setNavigationError((e as Error).message);}).finally(()=>{if(active&&new URL(location.href).searchParams.get('run')===runId)setLoading(false);});
 };window.addEventListener('popstate',change);return()=>{active=false;window.removeEventListener('popstate',change);};},[session,snapshot?.state.run?.id]);
 useEffect(()=>{document.title='ShiftClarity · Synthetic pilot';let live=true;
  void (async()=>{try{
   const response=await fetch('/api/v1/session',{credentials:'same-origin'});
   if(response.status===401)return;
   if(!response.ok)throw new Error('Sign-in service is unavailable.');
   const identity=await response.json() as Session;
   const [workspace,people,organization]=await Promise.all([fetch(workspacePath()),fetch('/api/v1/members'),fetch('/api/v1/agency')]);
   if(!workspace.ok||!people.ok)throw new Error('Workspace is unavailable.');
   const data=await workspace.json() as Snapshot,accounts=await people.json() as {actor:string}[];
   if(live){const url=new URL(location.href);url.searchParams.set('run',data.state.run!.id);loadedRun.current=data.state.run!.id;history.replaceState({},'',url);setSession(identity);setSnapshot(data);setMembers(accounts.map(m=>m.actor));setAgency(await organization.json() as Agency);}
  }catch(e){if(live)setError((e as Error).message);}finally{if(live)setLoading(false);}})();
  return()=>{live=false;};
 },[]);
 async function write(path:string,body:unknown){
  try{await request<Snapshot>(path,body);await refresh();}catch(e){await refresh().catch(()=>{});throw e;}
 }
 async function importFile(file:File,onProgress?:(message:string)=>void){
  if(file.size>1024*1024)throw new Error('File exceeds the 1 MiB limit.');
  if(!file.name.toLowerCase().endsWith('.json'))throw new Error('Choose a normalized JSON bundle.');
  onProgress?.('Uploading and validating the synthetic snapshot…');
  const imported=await request<{id:string;status:string;help?:string}>('/api/v1/imports',await file.text(),true);
  await refresh();
  if(imported.status!=='validated')throw new Error((imported.help||'Import rejected. Check the template, source controls and registered versions.')+' The prior completed run is retained.');
  onProgress?.('Source checks passed. Calculating findings…');
  await runImport(imported.id,onProgress);
 }
 async function runImport(importId:string,onProgress?:(message:string)=>void){
  onProgress?.('The review is running. Your previous result remains available.');
  const job=await request<{id:string}>('/api/v1/runs',{import_id:importId});
  for(let i=0;i<60;i++){
   await new Promise(resolve=>setTimeout(resolve,500));
   const status=await request<{status:string}>('/api/v1/jobs/'+job.id);
   if(status.status==='completed'){await selectRun(job.id);return;}
   if(status.status==='failed'){await refresh();throw new Error('Run failed; the previous completed result was retained.');}
  }
  throw new Error('The run is still queued. Refresh to check its result; it will continue on the server.');
 }
 if(loading)return <main className="sign-in"><Logo/><h1>Opening your workspace</h1><p role="status">Checking your sign-in…</p></main>;
 if(navigationError)return <main className="sign-in"><Logo/><h1>Review could not be opened</h1><p role="alert">{navigationError}</p><a className="btn" href="/pilot/">Open latest completed review</a></main>;
 if(!session||!snapshot)return <main className="sign-in"><Logo/><div className="eyebrow">Synthetic pilot · Sample workspace</div><h1>Every shift.<br/>Clearly aligned.</h1><p>Sign in with your own demonstration account to review fictional staffing records. Decisions and approved rule versions are saved in your workspace.</p><a className="btn btn-primary" href={'/auth/login?return_to='+encodeURIComponent(location.pathname+location.search+location.hash)}>Sign in to your workspace</a>{error&&<p role="alert" className="error">{error}</p>}<p className="muted">Individual accounts · Authenticator verification · Synthetic records only</p><a className="text-link" href="/demo/">Open the standalone demo</a></main>;
 const controller:PilotController={
  ...snapshot,session,members,agency,
  api:(path,body,method)=>request(path,body,false,method),refresh,runImport,selectRun,
  uploadTable:async(identifier,category,file)=>{
   if(file.size>2*1024*1024)throw new Error('Each file must be at most 2 MiB.');
   const response=await fetch('/api/v1/import-workbench/sessions/'+identifier+'/files?category='+encodeURIComponent(category)+'&filename='+encodeURIComponent(file.name),{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/octet-stream','X-CSRF-Token':session.csrf,'X-Data-Classification':'synthetic','Idempotency-Key':crypto.randomUUID()},body:file});
   if(!response.ok){const problem=await response.json().catch(()=>({detail:'File upload failed.'}));throw new Error(file.name+': '+problem.detail);}
  },
  decide:(f,action,reason,owner,version)=>write('/api/v1/findings/'+f.id+'/decisions',{action,reason,owner:owner||null,expected_fingerprint:f.fingerprint,expected_version:version,run_id:snapshot.state.run!.id}),
  approve:(action,reason)=>write('/api/v1/rules/'+snapshot.approval.draft.id+'/approval',{action,reason,expected_version:snapshot.approval.version}),
  task:(t,reason,owner)=>write('/api/v1/tasks',{task_id:t.id,reason,owner,run_id:snapshot.state.run!.id}),
  importFile,
  source:(title,text)=>write('/api/v1/documents',{title,text,synthetic:true}),
  propose:(supersedes,source_excerpt_id,rate,effective_from)=>write('/api/v1/rules/drafts',{supersedes,source_excerpt_id,rate,effective_from,expected_version:snapshot.approval.version}),
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
