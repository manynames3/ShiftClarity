import {useState} from 'react';
import type {FormEvent} from 'react';
import type {PilotController} from './ServerApp';
import {PanelHead} from './components';
export function RuleAuthoring({pilot}:{pilot:PilotController}){
 const [title,setTitle]=useState(''),[text,setText]=useState(''),[source,setSource]=useState(''),[rate,setRate]=useState(''),[date,setDate]=useState(''),[prior,setPrior]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false);
 const rules=pilot.catalog.rules,draft=pilot.approval?.draft||pilot.state.draft;
 async function submit(e:FormEvent,action:'source'|'draft'){
  e.preventDefault();setBusy(true);
  try{if(action==='source'){await pilot.source(title,text);setTitle('');setText('');setNotice('Synthetic source registered. It does not approve a rate.');}
   else{await pilot.propose(prior,source,rate,date);setNotice('Draft saved for a different person to approve.');}
  }catch(error){setNotice((error as Error).message);}finally{setBusy(false);}
 }
 return <section className="panel rule-authoring"><PanelHead title="Prepare a source-linked amendment" detail="Only fictional source text. An independent account must approve every proposed version."/><div className="authoring-grid">
  <form onSubmit={e=>void submit(e,'source')}><h3>Register a synthetic excerpt</h3><label htmlFor="source-title">Source title</label><input id="source-title" value={title} onChange={e=>setTitle(e.target.value)} minLength={3} maxLength={200} required/><label htmlFor="source-text">Fictional agreement text</label><textarea id="source-text" value={text} onChange={e=>setText(e.target.value)} minLength={10} maxLength={2000} required/><p className="muted">No names, contact details, patient or clinical information. Text is stored privately and treated as evidence.</p><button className="btn" disabled={busy}>Save synthetic source</button></form>
  <form onSubmit={e=>void submit(e,'draft')}><h3>Propose an immutable rate version</h3><label htmlFor="prior-rule">Approved predecessor</label><select id="prior-rule" value={prior} onChange={e=>setPrior(e.target.value)} required><option value="">Choose a version</option>{rules.map(r=><option key={r.id} value={r.id}>{r.id}</option>)}</select><label htmlFor="source-ref">Source excerpt</label><select id="source-ref" value={source} onChange={e=>setSource(e.target.value)} required><option value="">Choose evidence</option>{pilot.catalog.excerpts.map(e=><option key={e.id} value={e.id}>{e.title||e.label||e.id}</option>)}</select><label htmlFor="proposed-rate">Hourly rate · USD</label><input id="proposed-rate" inputMode="decimal" value={rate} onChange={e=>setRate(e.target.value)} pattern="[0-9]{1,8}(\.[0-9]{1,4})?" required/><label htmlFor="effective-date">Effective service date</label><input id="effective-date" type="date" value={date} onChange={e=>setDate(e.target.value)} required/><button className="btn btn-primary" disabled={busy||draft.state==='pending_approval'}>Submit for independent approval</button>{draft.state==='pending_approval'&&<p className="muted">Review or reject the current pending draft before proposing another.</p>}</form>
 </div><p role="status">{notice}</p></section>;
}
