import {useEffect,useState} from 'react';
import type {Run,Reviews,Category,Finding} from './domain/types';
import {facilityName} from './adapters/fixtures';
import {Icon,Link} from './components';
import {findingWorkflowMetadata,formatMoney,reasonLabel,reviewFor,stateLabel,titleFor} from './presentation';
import Decimal from 'decimal.js';
export function CoverageBar({run}:{run:Run}){
 const categories:Category[]=['evaluated_aligned','evaluated_flagged','abstained','not_evaluated'],names=['aligned','flagged','unsupported','not evaluated'];
 return <><div className="coverage-bar" role="img" aria-label={categories.map((c,i)=>run.coverage.categories[c].records+' '+names[i]).join(', ')}>{categories.map((c,i)=><span key={c} className={'seg-'+['a','f','u','n'][i]} style={{flex:run.coverage.categories[c].records}}/>)}</div><div className="coverage-legend">{categories.map((c,i)=><span key={c}><i className={'dot '+['','f','u','n'][i]}/>{run.coverage.categories[c].records} {names[i]}</span>)}</div></>;
}
type SortKey='difference'|'facility'|'state';
export function Workspace({run,reviews,initialScope='review',onShortcuts,onReport,onOpenFinding,loading=false,error}:{run:Run;reviews:Reviews;initialScope?:'review'|'all';onShortcuts?:()=>void;onReport?:()=>void;onOpenFinding?:(finding:Finding)=>void;loading?:boolean;error?:string}){
 const [facility,setFacility]=useState('all'),[search,setSearch]=useState(''),[scope,setScope]=useState(initialScope),[activeFindingId,setActiveFindingId]=useState<string|null>(null),[sort,setSort]=useState<{key:SortKey;direction:'asc'|'desc'}>({key:'difference',direction:'desc'});
 const stateRank=(value:string)=>({needs_review:0,evidence_requested:1,confirmed:2,dismissed:3}[value]??4);
 const compareImpact=(a:Finding,b:Finding)=>new Decimal(b.discrepancy_amount).abs().comparedTo(new Decimal(a.discrepancy_amount).abs());
 const needsReview=(f:Finding)=>['needs_review','evidence_requested'].includes(reviewFor(f,reviews).state);
 const open=run.findings.filter(needsReview).sort(compareImpact);
 const matches=run.findings.filter(f=>(facility==='all'||f.facility_id===facility)&&(titleFor(f)+' '+f.id+' '+facilityName(f.facility_id)+' '+f.reason_code).toLowerCase().includes(search.trim().toLowerCase()));
 const sorted=matches.filter(f=>scope==='all'||needsReview(f)).sort((a,b)=>{
  const tie=()=>compareImpact(a,b)||a.id.localeCompare(b.id);
  if(sort.key==='facility')return (sort.direction==='asc'?1:-1)*facilityName(a.facility_id).localeCompare(facilityName(b.facility_id))||tie();
  if(sort.key==='state')return (sort.direction==='asc'?1:-1)*(stateRank(reviewFor(a,reviews).state)-stateRank(reviewFor(b,reviews).state))||tie();
  return (sort.direction==='desc'?1:-1)*compareImpact(a,b)||stateRank(reviewFor(a,reviews).state)-stateRank(reviewFor(b,reviews).state);
 });
 useEffect(()=>{const handler=(event:KeyboardEvent)=>{
  const target=event.target;if(target instanceof HTMLElement&&(target.matches('input,textarea,select,[contenteditable="true"]')||target.closest('dialog')))return;
  if(event.key==='Enter'&&target instanceof HTMLElement&&target.closest('a,button'))return;
  if(document.querySelector('dialog[open]'))return;
  if(event.key==='j'||event.key==='k'){
   if(!sorted.length)return;
   event.preventDefault();const current=sorted.findIndex(f=>f.id===activeFindingId),direction=event.key==='j'?1:-1,index=current<0?(direction>0?0:sorted.length-1):(current+direction+sorted.length)%sorted.length;
   const next=sorted[index];setActiveFindingId(next.id);const row=document.querySelector<HTMLElement>('[data-finding-id="'+CSS.escape(next.id)+'"]');if(typeof row?.scrollIntoView==='function')row.scrollIntoView({block:'nearest'});
  }else if(event.key==='Enter'){
   const focused=sorted.find(f=>f.id===activeFindingId)||sorted[0];if(focused){event.preventDefault();onOpenFinding?.(focused);}
  }
 };window.addEventListener('keydown',handler);return()=>window.removeEventListener('keydown',handler);},[activeFindingId,sorted,onOpenFinding]);
 const c=run.coverage,totalUnderbilling=run.findings.reduce((total,f)=>f.discrepancy_amount.startsWith('-')?total:total.plus(f.discrepancy_amount),new Decimal(0)).toFixed(2),affectedShifts=new Set(run.findings.flatMap(f=>f.shift_ids)).size;
 const sortBy=(key:SortKey)=>setSort(current=>({key,direction:current.key===key?(current.direction==='asc'?'desc':'asc'):key==='difference'?'desc':'asc'}));
 const sortState=(key:SortKey)=>sort.key===key?(sort.direction==='asc'?'ascending':'descending'):'none';
 const categories:Category[]=['evaluated_aligned','evaluated_flagged','abstained','not_evaluated'];
 return <div className="workspace-overview">
  <div className="overview-main">
   <section className="workspace-heading" aria-label="Review summary">
    <div className="impact-summary"><h1 tabIndex={-1}>{c.evaluated_records?formatMoney(new Decimal(totalUnderbilling).eq(0)&&new Decimal(run.totals.overbilling).gt(0)?run.totals.overbilling:totalUnderbilling,true):'Not estimated'}</h1><h2>{new Decimal(totalUnderbilling).eq(0)&&new Decimal(run.totals.overbilling).gt(0)?'Potential overbilling':'Potential underbilling'}</h2><p>{run.findings.length} finding{run.findings.length===1?'':'s'}, {affectedShifts} shift{affectedShifts===1?'':'s'}, collection unknown</p></div>
    <div className="review-next">{open[0]&&<><Link to={'?view=evidence&id='+open[0].id} kind="btn-primary">Review next finding <Icon name="arrow"/></Link><p>Review findings against the approved terms, work records and invoice evidence.</p></>}<div className="overview-utilities">{onReport&&<button className="btn btn-quiet report-trigger" onClick={onReport}><Icon name="download"/>Download report</button>}<Link to="?view=inputs" kind="btn-quiet">Run details</Link><button className="shortcut-help" type="button" aria-label="Keyboard shortcuts" onClick={onShortcuts}>?</button></div></div>
   </section>
   <section className="finding-overview" aria-label="Findings" aria-busy={loading}>
    <div className="overview-tools">
     <div className="finding-tabs" role="group" aria-label="Finding scope"><button type="button" className={scope==='review'?'active':''} aria-pressed={scope==='review'} onClick={()=>setScope('review')}>Needs review <span>{open.length}</span></button><button type="button" className={scope==='all'?'active':''} aria-pressed={scope==='all'} onClick={()=>setScope('all')}>All findings <span>{run.findings.length}</span></button></div>
     <div className="finding-filters"><label className="select-like"><span className="sr-only">Facility</span><select aria-label="Facility" value={facility} onChange={e=>setFacility(e.target.value)}><option value="all">All facilities</option>{[...new Set(run.records.map(r=>r.work.facility_id))].sort().map(id=><option key={id} value={id}>{facilityName(id)}</option>)}</select></label><label className="search-field"><Icon name="search"/><input aria-label="Search findings" placeholder="Search findings" value={search} onChange={e=>setSearch(e.target.value)}/></label></div>
    </div>
    {loading&&<div className="table-state" role="status">Refreshing findings. The last completed result remains available.</div>}{error&&<div className="table-state table-state-error" role="alert"><strong>Latest run could not be refreshed.</strong> Showing the completed findings from {run.id}; review actions are paused.</div>}
    <table role="table" className="finding-table overview-findings"><caption className="sr-only">Financial findings for human review</caption><thead className="sr-only" role="rowgroup"><tr role="row">{['Finding','Facility','Work affected','Difference','Owner','Priority','Age','State','Open'].map((label,index)=><th key={label} role="columnheader" scope="col" aria-sort={index===1?sortState('facility'):index===3?sortState('difference'):index===7?sortState('state'):undefined}>{label}</th>)}</tr></thead><tbody role="rowgroup">{sorted.map(f=>{
     const rows=run.records.filter(r=>f.shift_ids.includes(r.work.id)),review=reviewFor(f,reviews),metadata=findingWorkflowMetadata(f,run.manifest.synthetic),hours=rows.reduce((sum,r)=>sum+r.work.worked_minutes,0)/60;
     return <tr role="row" key={f.id} className={open[0]?.id===f.id?'finding-featured':''} data-finding-id={f.id} data-keyboard-active={activeFindingId===f.id||undefined}>
      <td role="cell" className="overview-finding-title"><small>{f.id} · {reasonLabel(f.reason_code)}</small><a className="finding-open" aria-current={activeFindingId===f.id?'true':undefined} href={'?view=evidence&id='+f.id}><strong>{titleFor(f)}</strong></a></td>
      <td role="cell" data-label="Facility" className="overview-facility"><strong>{facilityName(f.facility_id)}</strong><span className="sr-only">Standard RN · {rows[0]?.rule?.contract_id}</span></td>
      <td role="cell" data-label="Work affected" className="overview-work"><strong>{f.shift_ids.length} shifts / {hours} hours</strong><small>Approved work</small></td>
      <td role="cell" data-label="Difference" className="overview-amount">{formatMoney(f.discrepancy_amount,true)}<small>{f.discrepancy_amount.startsWith('-')?'Potential overbilling':'Potential underbilling'}</small></td>
      <td role="cell" data-label="Owner" className="overview-owner"><span className="owner-avatar" aria-hidden="true">{metadata.owner==='Not assigned'?'—':metadata.owner.split(' ').slice(0,2).map(part=>part[0]).join('')}</span><span><strong>{metadata.owner}</strong><small>{metadata.owner==='Not assigned'?'Review owner':'Reviewer'}</small></span></td>
      <td role="cell" data-label="Priority" className="overview-priority"><small>Priority</small><strong>{metadata.priority}</strong></td>
      <td role="cell" data-label="Age" className="overview-age"><small>Age</small><strong>{metadata.age}</strong></td>
      <td role="cell" data-label="State" className={'overview-state state-'+review.state}><strong><i aria-hidden="true"/>{stateLabel[review.state]}</strong><small>Status</small></td>
      <td role="cell" data-label="Open" className="overview-open"><a aria-label={'Inspect '+f.id} href={'?view=evidence&id='+f.id}><Icon name="arrow"/></a></td>
     </tr>;
    })}</tbody></table>
    {!sorted.length&&<div className="empty"><h3>{run.findings.length?'No findings match these filters':'No discrepancies found in the checked records'}</h3><p>{run.findings.length?'Review coverage is unchanged.':'Some records still need evidence.'}</p>{(search||facility!=='all'||scope==='review'&&run.findings.length>0)&&<button className="btn" onClick={()=>{setFacility('all');setSearch('');setScope('all');}}>Clear filters</button>}</div>}
    <div className="finding-list-footer"><div className="finding-sorts"><span>Sort by</span>{(['facility','difference','state'] as const).map(key=><button type="button" key={key} className={sort.key===key?'active':''} aria-label={'Sort by '+key} onClick={()=>sortBy(key)}>{key[0].toUpperCase()+key.slice(1)}{sort.key===key&&<span aria-hidden="true">{sort.direction==='asc'?' ↑':' ↓'}</span>}</button>)}</div><div className="table-footer"><span role="status">{sorted.length} matching finding{sorted.length!==1?'s':''} · Review coverage unchanged</span><span>Potential amounts are not confirmed adjustments.</span></div>{run.manifest.dataset_id==='sc-demo-v1'&&<p className="workflow-disclosure">Owner, priority and age are illustrative only; they do not affect calculations.</p>}</div>
   </section>
  </div>
  <aside className="workspace-coverage" aria-label="Shift coverage"><h2>Shift coverage</h2><div className="coverage-ratio"><strong>{c.evaluated_records}</strong><span>/ {c.received_records}</span></div><p className="coverage-unit">shifts checked</p><div className="coverage-hours"><strong>{c.evaluated_minutes/60}</strong><span>/ {c.received_minutes/60}</span></div><p className="coverage-unit">hours checked</p><a className="coverage-gap-link" href="?view=coverage"><strong>{run.tasks.length}</strong> coverage gaps <Icon name="arrow"/></a><div className="alignment-summary"><h3>Shift alignment</h3><ul>{categories.map((category,index)=><li key={category}><i className={'alignment-dot dot-'+index}/><strong>{c.categories[category].records}</strong><span>{['aligned','flagged','unsupported','not evaluated'][index]}</span></li>)}</ul></div><p className="coverage-verification">{c.evaluated_records} of {c.received_records} shifts rule-checked</p><p className="coverage-limit">Unchecked records have no financial estimate.</p><a className="text-link" href="?view=coverage">Explore coverage <Icon name="arrow"/></a></aside>
  <div className="overview-support two-col">
   <section className="support-section" aria-labelledby="context-heading">
    <header className="support-heading"><h3 id="context-heading">Needs more context</h3><p>These records have no financial estimate.</p></header>
    <div className="context-list">{run.tasks.map(t=><a className="context-row" key={t.id} href={'?view=coverage#'+t.id}><span className="context-icon"><Icon name={t.reason_code==='TIME_APPROVAL_PENDING'?'clock':'info'}/></span><span className="context-copy"><strong>{gapTitle(t.reason_code)}</strong><small>{t.shift_ids.length} shift{t.shift_ids.length>1?'s':''} · {run.records.filter(r=>t.shift_ids.includes(r.work.id)).reduce((sum,r)=>sum+r.work.worked_minutes,0)/60} hours</small></span><Icon name="chevron"/></a>)}</div>
    <a className="text-link support-action" href="?view=coverage">View coverage gaps <Icon name="arrow"/></a>
   </section>
   <section className="support-section" aria-labelledby="sources-heading">
    <header className="support-heading"><h3 id="sources-heading">Review sources</h3><p>The records and approved terms used in this run.</p></header>
    <ul className="source-summary">{[['Work records',c.received_records+' records · Validated'],['Posted invoice lines',(run.allocations.length?new Set(run.allocations.map(a=>a.line_id)).size:0)+' lines · Validated'],['Approved rule versions',run.rule_version_ids.length+' versions · '+new Set(run.records.map(r=>r.work.facility_id)).size+(new Set(run.records.map(r=>r.work.facility_id)).size===1?' facility':' facilities')]].map(([title,detail])=><li key={title}><span className="source-icon"><Icon name="check"/></span><span><strong>{title}</strong><small>{detail}</small></span></li>)}</ul>
    <a className="text-link support-action" href="?view=inputs">Inspect sources <Icon name="arrow"/></a>
   </section>
  </div>
 </div>;
}
export function gapTitle(reason:string){return ({UNSUPPORTED_COMPONENT:'Callback terms are outside this rule set',TIME_APPROVAL_PENDING:'A time approval is still pending',INVOICE_SOURCE_INCOMPLETE:'Invoice source is incomplete',WORK_SOURCE_INCOMPLETE:'Work source is incomplete',BILLING_CYCLE_OPEN:'The billing cutoff has not passed',CONFLICTING_APPROVED_RULES:'Approved terms conflict',AMBIGUOUS_REFERENCE:'Invoice references need evidence',CURRENCY_MISMATCH:'Currency is outside supported USD scope'} as Record<string,string>)[reason]||reasonLabel(reason);}
