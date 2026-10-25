import Decimal from 'decimal.js';
import type {Demo} from './demo';
import {findingKey,safeCell} from './demo';
import {reasonLabel,stateLabel} from '../presentation';

export type ReportCell=string|number|null;
export interface ReportTable {name:string;headers:string[];rows:ReportCell[][]}
export const reportLimit='Potential differences are not recovered revenue, payment evidence or confirmed invoice adjustments. Unevaluated work has no financial estimate.';

// Read completed engine results; exporting never recalculates or changes a review.
export function billingReport(state:Demo,includeNotes=false,generatedAt=new Date().toISOString()){
 const run=state.run;if(!run)throw new Error('No completed run to export.');
 const findings=run.findings.map(f=>{
  const review=state.reviews[findingKey(f)];
  return {...f,review_state:review?.fingerprint===f.fingerprint?review.state:'needs_review' as const};
 });
 const confirmed=(over:boolean)=>findings.filter(f=>f.review_state==='confirmed'&&new Decimal(f.discrepancy_amount).lt(0)===over).reduce((total,f)=>total.plus(new Decimal(f.discrepancy_amount).abs()),new Decimal(0)).toNumber();
 const evaluated=run.records.filter(r=>r.category==='evaluated_aligned'||r.category==='evaluated_flagged');
 const billed=evaluated.reduce((total,r)=>total.plus(r.invoiced_amount!),new Decimal(0)).toNumber();
 const amount=(value:string|null)=>value===null?null:new Decimal(value).toNumber();
 const tables:ReportTable[]=[
  {name:'Overview',headers:['Measure','Value'],rows:[
   ['Report','Contract-to-invoice review'],['Data boundary',run.manifest.synthetic?'Fictional records only':'User-supplied local preview; not independently verified'],
   ['Run reference',run.id],['Report generated (UTC)',generatedAt],['Service from (inclusive)',run.manifest.service_from],['Service to (exclusive)',run.manifest.service_to_exclusive],
   ['Source current through',run.manifest.invoice_source_as_of],['Billing cutoff',run.manifest.billing_cutoff],['Result freshness',state.stale?'STALE - previous completed run retained; rerun validated evidence':'Current completed run'],
   ['Records received',run.coverage.received_records],['Records evaluated',run.coverage.evaluated_records],['Hours received',run.coverage.received_minutes/60],['Hours evaluated',run.coverage.evaluated_minutes/60],
   ['Expected on evaluated work (USD)',amount(run.totals.expected)],['Net invoiced on evaluated work (USD)',billed],['All posted invoice lines, including unchecked work (USD)',amount(run.totals.invoiced)],
   ['Potential underbilling before review exclusions (USD)',amount(run.totals.underbilling)],['Potential overbilling before review exclusions (USD)',amount(run.totals.overbilling)],
   ['Reviewer-confirmed underbilling difference (USD)',confirmed(false)],['Reviewer-confirmed overbilling difference (USD)',confirmed(true)],
   ['Findings',findings.length],...Object.entries(stateLabel).map(([status,label]):ReportCell[]=>[label,findings.filter(f=>f.review_state===status).length]),['Coverage tasks',run.tasks.length],
   ['Reviewer notes included',includeNotes?'Yes - explicitly requested':'No'],['Worker identities','Omitted'],['Method','Expected = exact approved hourly rate x worked minutes / 60; compare signed posted invoice allocations.'],
   ['Coverage declaration',run.manifest.invoice_coverage_complete?'Declared complete; not independently verified':'Incomplete - missing invoices cannot be treated as underbilling'],['Limit',reportLimit],['Calculation engine',run.engine_version]
  ]},
  {name:'Findings',headers:['Finding','Facility','Review state','Review basis','Affected work records','Rate version','Expected USD','Net invoiced USD','Difference USD','Collectibility'],rows:findings.map(f=>[f.id,f.facility_id,stateLabel[f.review_state],reasonLabel(f.reason_code),f.shift_ids.length,f.rule_version_id,amount(f.expected_amount),amount(f.invoiced_amount),amount(f.discrepancy_amount),'Not established'])},
  {name:'Work calculations',headers:['Work reference','Facility','Service date','Role','Hourly component','Minutes','Hours','Coverage','Review basis','Rate version','Rate USD per hour','Expected USD','Net invoiced USD','Difference USD','Work approval event date','Approved status observed at','Source batch','Source revision'],rows:run.records.map(r=>[r.work.id,r.work.facility_id,r.work.service_date,r.work.role,r.work.component,r.work.worked_minutes,r.work.worked_minutes/60,reasonLabel(r.category),reasonLabel(r.reason_code),r.rule?.id||'',r.rule?amount(r.rule.rate):null,amount(r.expected_amount),amount(r.invoiced_amount),amount(r.discrepancy_amount),r.work.approved_at?(r.work.approval_date_only?r.work.approved_at.slice(0,10):r.work.approved_at):'Unknown',r.work.approval_observed_at?(r.work.approval_observation_date_only?r.work.approval_observed_at.slice(0,10):r.work.approval_observed_at):'Not supplied',r.work.batch_id,r.work.source_revision])},
  {name:'Invoice allocations',headers:['Work reference','Invoice reference','Line reference','Signed allocated USD','Credit/rebill chain'],rows:run.allocations.map(a=>[a.shift_id,a.invoice_id,a.line_id,amount(a.amount),a.chain_id||''])},
  {name:'Rate terms',headers:['Rate version','Contract reference','Facility','Role','Hourly component','Rate USD per hour','Effective from','Effective to (exclusive)','Source authorized',run.manifest.synthetic?'System approved at':'Declared authorization date',run.manifest.synthetic?'Author account':'Declared author reference',run.manifest.synthetic?'Approver account':'Declared approver reference','Evidence reference'],rows:state.inputs.rules.map(r=>[r.id,r.contract_id,r.facility_id,r.role,r.component,amount(r.rate),r.effective_from,r.effective_to||'',r.authorization_date||(r.approved_at||'').slice(0,10),run.manifest.synthetic?r.approved_at||'':r.authorization_date||(r.approved_at||'').slice(0,10),r.author_id,r.approver_id||'',r.source_excerpt_id])},
  {name:'Source references',headers:['Batch reference','Source','Records','Source as of','Coverage declaration'],rows:state.inputs.batches.map(b=>[b.id,b.source,b.records,b.source_as_of,b.declared_complete?'Declared complete':'Incomplete'])},
  {name:'Review history',headers:['Finding','Sequence','Action','Account','Recorded at','Task owner','Reason'],rows:run.findings.flatMap(f=>(state.reviews[findingKey(f)]?.history||[]).map(e=>[f.id,e.sequence,e.action,e.actor,e.timestamp,e.owner||'',includeNotes?e.reason:'(notes omitted)']))},
  {name:'Coverage gaps',headers:['Task','Work reference','Coverage','Reason','Financial estimate'],rows:run.tasks.flatMap(t=>t.shift_ids.map(id=>[t.id,id,reasonLabel(t.category),reasonLabel(t.reason_code),'No estimate applied']))}
 ];
 if(!run.manifest.synthetic)tables.push({name:'Invoice source lines',headers:['Invoice','Line reference','Facility','Posting status','Document kind','Signed amount USD','Minutes','Hourly rate USD','Billing scope','Source batch'],rows:state.inputs.invoices.map(l=>[l.invoice_id,l.id,l.facility_id,l.state,l.document_kind,amount(l.amount),l.minutes,amount(l.unit_rate),l.billing_basis||'hourly',l.batch_id])});
 if(run.non_hourly_lines?.length)tables.push({name:'Non-hourly invoice lines',headers:['Invoice','Line reference','Facility','Posting status','Signed amount USD','Comparison'],rows:run.non_hourly_lines.map(l=>[l.invoice_id,l.id,l.facility_id,l.state,amount(l.amount),'Outside hourly scope; no difference estimated'])});
 return {runId:run.id,generatedAt,synthetic:run.manifest.synthetic,stale:state.stale,notesIncluded:includeNotes,findingWork:Object.fromEntries(findings.map(f=>[f.id,f.shift_ids])),tables};
}
export type BillingReport=ReturnType<typeof billingReport>;

export function reportCsv(report:BillingReport){
 return '\uFEFF'+report.tables.map(table=>[
  [table.name],table.headers,...table.rows
 ].map(row=>row.map(value=>typeof value==='number'?String(value):safeCell(value===null?'':value)).join(',')).join('\r\n')).join('\r\n\r\n')+'\r\n';
}
