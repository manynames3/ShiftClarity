import {useEffect,useState} from 'react';
import type {PilotController} from './ServerApp';
import {PanelHead,Pill} from './components';
import {RuleAuthoring} from './RuleAuthoring';
import {formatDate,formatTimestamp} from './lib/format';
type Import={id:string;status:string;diagnostic:string|null;created_at:string;expires_at:string};
type Audit={sequence:number;actor:string;action:string;resource:string;created_at:string};
export function PilotDetails({pilot}:{pilot:PilotController}){
 const [imports,setImports]=useState<Import[]>([]),[events,setEvents]=useState<Audit[]>([]),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 useEffect(()=>{let live=true;setLoading(true);setError('');void (async()=>{try{
  const responses=await Promise.all([fetch('/api/v1/imports'),fetch('/api/v1/audit')]);
  if(responses.some(r=>!r.ok))throw new Error('Sign in again to view import history.');
  const [batches,audit]=await Promise.all(responses.map(r=>r.json()));
  if(live){setImports(batches);setEvents(audit);}
 }catch(e){if(live)setError((e as Error).message);}finally{if(live)setLoading(false);}})();return()=>{live=false;};},[pilot.version]);
 return <div className="stack pilot-details" aria-busy={loading}>
  {pilot.session.roles.includes('author')&&<RuleAuthoring pilot={pilot}/>}
  <section className="panel"><PanelHead title="Server import history" detail="Each accepted bundle is a complete source selection. Repeated content is reused."/>{loading?<p className="empty">Loading server import history…</p>:error?<p className="empty">Import history is unavailable.</p>:imports.length?<div className="table-wrap"><table><thead><tr><th>Import</th><th>Status</th><th>Retention</th><th>Source</th></tr></thead><tbody>{imports.map(batch=><tr key={batch.id}><td className="mono">{batch.id}</td><td><Pill type={batch.status==='validated'?'ok':'attention'}>{batch.status}</Pill>{batch.diagnostic&&<small>{batch.diagnostic}</small>}</td><td>{formatDate(batch.expires_at)}</td><td>{batch.status==='validated'&&pilot.session.roles.includes('importer')?<a className="text-link" href={'/api/v1/imports/'+batch.id+'/source'} download>Download private source</a>:'—'}</td></tr>)}</tbody></table></div>:<p className="empty">No additional snapshots imported. Included sources are fictional.</p>}</section>
  <section className="panel"><PanelHead title="Account and review record" detail="Permissions come from your verified identity and server membership."/><div className="history"><p><strong>{pilot.session.actor}</strong> · {pilot.session.roles.join(', ')||'Read only'}</p>{!loading&&events.slice(0,12).map(event=><div className="event" key={event.sequence}><i className="eventdot"/><div><strong>{event.action.replaceAll('_',' ')}</strong><small>{event.actor} · {formatTimestamp(event.created_at)}</small><p className="mono">{event.resource}</p></div></div>)}</div></section>{error&&<p className="error" role="alert">{error}</p>}
 </div>;
}
