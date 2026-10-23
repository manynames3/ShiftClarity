import {useState} from 'react';
import {displayUserText} from './presentation';

export function ReportDownloads({runId,stale}:{runId:string;stale:boolean}){
 const [notes,setNotes]=useState(false),[busy,setBusy]=useState(''),[error,setError]=useState('');
 async function download(format:'xlsx'|'pdf'){
  setBusy(format);setError('');
  try{
   const response=await fetch('/api/v1/runs/'+encodeURIComponent(runId)+'/report.'+format+'?include_notes='+notes,{credentials:'same-origin'});
   if(!response.ok){const body=await response.json().catch(()=>null);throw new Error(body?.detail||'Report unavailable. Refresh your session and try again.');}
   const url=URL.createObjectURL(await response.blob()),a=document.createElement('a');a.href=url;a.download='ShiftClarity-billing-review.'+format;a.click();window.setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch(e){setError((e as Error).message);}finally{setBusy('');}
 }
 return <section className="report-downloads" aria-label="Download billing review"><div><h2>Share the evidence</h2><p>Current review: all findings, decisions and coverage gaps. Download before moving to another period. Worker identities and reviewer notes are omitted by default.</p>{stale&&<p className="error">Reports will label these retained results as stale.</p>}<label><input type="checkbox" checked={notes} onChange={e=>setNotes(e.target.checked)}/>Include reviewer notes I’m authorized to share</label></div><div className="report-actions"><button className="btn" disabled={!!busy} onClick={()=>void download('xlsx')}>{busy==='xlsx'?'Preparing Excel…':'Download Excel'}</button><button className="btn btn-primary" disabled={!!busy} onClick={()=>void download('pdf')}>{busy==='pdf'?'Preparing PDF…':'Download PDF'}</button></div>{error&&<p className="error" role="alert">{displayUserText(error)}</p>}</section>;
}
