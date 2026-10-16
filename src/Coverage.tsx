import type {Demo} from './domain/demo';
import type {Category,Task} from './domain/types';
import {CoverageBar,gapTitle} from './Workspace';
import {Icon,Pill,Link} from './components';
import {facilityName} from './adapters/fixtures';
import {actorLabel,displayUserText,reasonLabel} from './presentation';
import {formatDate,formatDateSpan,formatTimestamp} from './lib/format';

const categoryTitle:Record<Category,string>={evaluated_aligned:'Aligned',evaluated_flagged:'Flagged',abstained:'Unsupported',not_evaluated:'Not evaluated'};
export function Coverage({state,onRequest,canReview=true,secure=false}:{state:Demo;onRequest:(task:Task)=>void;canReview?:boolean;secure?:boolean}){
 const run=state.run;
 if(!run)return null;
 const coverage=run.coverage;
 if(coverage.received_records===0)return <div className="empty"><h1 tabIndex={-1}>No coverage is available yet</h1><p>No source records have been loaded. There is no financial evaluation to summarize.</p><Link to="?view=inputs">Load source records</Link></div>;
 const categories:Category[]=['evaluated_aligned','evaluated_flagged','abstained','not_evaluated'];
 return <>
  <div className="heading"><div><a href="?view=workspace" className="text-link" style={{marginBottom:12}}><Icon name="back"/>Review workspace <span className="muted">/ Coverage</span></a><h1 tabIndex={-1}>Know what was actually checked</h1><p>Every received record has a clear outcome, including the ones that need more evidence.</p></div></div>
  <div className="coverage-grid">{categories.map((category,index)=><section className="panel coverage-card" key={category}><h2>{categoryTitle[category]}</h2><strong className="num">{coverage.categories[category].records}<small>{coverage.categories[category].minutes/60} hours</small></strong><p>{['No discrepancy under checked rules',`Grouped into ${run.findings.length} findings`,'A reliable comparison is not available','A prerequisite is still missing'][index]}</p></section>)}</div>
  <section className="panel coverage-big"><div className="coverage-top"><div><h2>{coverage.evaluated_records} of {coverage.received_records} shifts · {coverage.evaluated_minutes/60} of {coverage.received_minutes/60} hours</h2><p>Checked coverage includes aligned and flagged records. The remaining {(coverage.received_minutes-coverage.evaluated_minutes)/60} hours were not financially evaluated; their value is not estimated.</p></div><Pill type="attention">{coverage.evaluated_records<coverage.received_records?'Partial checked coverage':'Checked within supported scope'}</Pill></div><CoverageBar run={run}/></section>
  <div className="section-title"><div><h2>{run.tasks.length} coverage task{run.tasks.length!==1?'s':''} need a different next step</h2><p>These are coverage tasks, not billing-error findings.</p></div></div>
  <div className="stack">{run.tasks.map(task=>{
   const records=run.records.filter(record=>task.shift_ids.includes(record.work.id));
   const dates=records.map(record=>record.work.service_date).sort();
   const explanation=task.reason_code==='UNSUPPORTED_COMPONENT'?'This shift cannot be safely priced using the standard hourly rate. A reviewed callback rule is needed before making a financial comparison.':task.reason_code==='TIME_APPROVAL_PENDING'?'Completed work is present, but this record has not reached approved status. It is excluded from financial evaluation until that prerequisite is met.':'The supplied evidence does not support a reliable financial conclusion. Resolve the source prerequisite before review.';
   return <section className="panel task-panel" id={task.id} key={task.id}>
    <span className="task-number"><Icon name={task.reason_code==='TIME_APPROVAL_PENDING'?'clock':'info'}/></span>
    <div><span className="eyebrow">{task.id} · {reasonLabel(task.reason_code)}</span><h3>{gapTitle(task.reason_code)}</h3><p>{explanation}</p>
     <div className="task-meta"><span>{task.shift_ids.join(', ')} · {facilityName(records[0].work.facility_id)}</span><span>{formatDateSpan(dates[0],dates.at(-1)!)} · {records.reduce((sum,record)=>sum+record.work.worked_minutes,0)/60} hours</span><span>Financial impact: unknown</span></div>
     <div className="task-actions">{task.reason_code==='UNSUPPORTED_COMPONENT'?<Link to="?view=inputs" kind="btn-small">Inspect approved rules <Icon name="arrow"/></Link>:<button className="btn btn-small" disabled={!canReview} onClick={()=>onRequest(task)}>Prepare evidence request <Icon name="arrow"/></button>}<Pill>{task.reason_code==='UNSUPPORTED_COMPONENT'?'Not a confirmed discrepancy':'Nothing will be sent'}</Pill></div>
    </div>
   </section>;
  })}</div>
  <p className="coverage-explanation"><strong>Confidence includes knowing the limits.</strong> A quiet findings queue does not mean unexamined records are correct.</p>
  <details className="panel run-details"><summary>Record-by-record coverage · {coverage.received_records} records</summary><div className="table-scroll" role="region" tabIndex={0} aria-label="Coverage by work record"><table><caption className="sr-only">Disjoint record and minute partitions</caption><thead><tr>{['Shift','Service date','Minutes','Outcome','Reason','Rule'].map(label=><th scope="col" key={label}>{label}</th>)}</tr></thead><tbody>{run.records.map(record=><tr key={record.work.id}><td>{record.work.id}</td><td>{formatDate(record.work.service_date)}</td><td>{record.work.worked_minutes}</td><td>{categoryTitle[record.category]}</td><td>{reasonLabel(record.reason_code)}</td><td>{record.rule?.id||'Not applicable'}</td></tr>)}</tbody></table></div></details>
  {state.localTasks.length>0&&<section className="panel history"><h3>{secure?'Workspace evidence tasks':'Local evidence tasks'} · Nothing sent</h3>{state.localTasks.map((event,index)=><div className="control-row" key={index}><strong>{event.owner}</strong><p>{displayUserText(event.reason)}</p><small>{actorLabel(event.actor)} · {formatTimestamp(event.timestamp,run.manifest.timezone)}</small></div>)}</section>}
 </>;
}
