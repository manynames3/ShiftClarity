import Decimal from 'decimal.js';
import type { Inputs, Work, Rule, Invoice, Run, Evaluated, Finding, Allocation, Category, Partition } from './types';
const D = Decimal.clone({precision:40,rounding:Decimal.ROUND_HALF_UP});
export const moneyPattern = /^-?(0|[1-9]\d*)\.\d{2}$/;
export const ratePattern = /^(0|[1-9]\d*)(\.\d{1,4})?$/;
export class InputError extends Error { constructor(public reason:string, public row:string) { super(`${row}: ${reason}`); } }
export function expected(minutes:number,rate:string):string {
  if(!Number.isSafeInteger(minutes)||minutes<0) throw new InputError('INVALID_WORKED_MINUTES','work');
  if(!ratePattern.test(rate)) throw new InputError('INVALID_RATE','rule');
  return new D(minutes).div(60).mul(rate).toFixed(2);
}
export function sum(values:string[]):string { return values.reduce((a,v)=>a.plus(v),new D(0)).toFixed(2); }
export function difference(a:string,b:string):string { return new D(a).minus(b).toFixed(2); }
export function signed(v:string):string { return new D(v).gte(0)?`+${v}`:v; }
// The local demo retains exact evidence; the server supplies Node's standard SHA-256 encoder.
let encodeFingerprint=(value:string)=>value;
export function setFingerprintEncoder(encode:(value:string)=>string){encodeFingerprint=encode;}
export function evidenceFingerprint(value:unknown,prefix=''){return encodeFingerprint(prefix+canonical(value));}
export function canonical(value:unknown):string {
  if(Array.isArray(value))return `[${value.map(canonical).join(',')}]`;
  if(value!==null && typeof value==='object')return `{${Object.entries(value).filter(([,v])=>v!==undefined).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>`${JSON.stringify(k)}:${canonical(v)}`).join(',')}}`;
  return JSON.stringify(typeof value==='string'?value.trim().replace(/\s+/g,' '):value);
}
function unique<T extends {id:string}>(rows:T[]):T[] {
  const byId=new Map<string,T>();
  for(const r of rows){if(!r.id)throw new InputError('MISSING_ID','input');const old=byId.get(r.id);if(old&&canonical(old)!==canonical(r))throw new InputError('CONFLICTING_SOURCE_REVISION',r.id);byId.set(r.id,r);}
  return [...byId.values()].sort((a,b)=>a.id.localeCompare(b.id));
}
function validDate(value:string){return /^\d{4}-\d{2}-\d{2}$/.test(value)&&!Number.isNaN(Date.parse(value))&&new Date(value).toISOString().slice(0,10)===value;}
export function selectRule(w:Work,rules:Rule[]):Rule[] {
  return rules.filter(r=>r.state==='approved'&&r.facility_id===w.facility_id&&r.role===w.role&&r.component===w.component&&r.effective_from<=w.service_date&&(!r.effective_to||w.service_date<r.effective_to)&&!rules.some(next=>next.state==='approved'&&next.supersedes===r.id&&next.facility_id===r.facility_id&&next.role===r.role&&next.component===r.component&&next.effective_from<=w.service_date));
}
export function reconcile(raw:Inputs):Run {
  const work=unique(raw.work), invoices=unique(raw.invoices), rules=unique(raw.rules), batches=unique(raw.batches);
  const nonHourly=invoices.filter(l=>l.billing_basis==='non_hourly');
  for(const w of work){
    if(!Number.isSafeInteger(w.worked_minutes)||w.worked_minutes<0)throw new InputError('INVALID_WORKED_MINUTES',w.id);
    if(w.approved_at&&(Number.isNaN(Date.parse(w.approved_at))||Date.parse(w.approved_at)>Date.parse(raw.manifest.as_of)||w.approved_at.slice(0,10)<w.service_date))throw new InputError('INVALID_WORK_APPROVAL',w.id);
    if(w.approval_observed_at&&(Number.isNaN(Date.parse(w.approval_observed_at))||Date.parse(w.approval_observed_at)>Date.parse(raw.manifest.as_of)||w.approval_observed_at.slice(0,10)<w.service_date))throw new InputError('INVALID_APPROVAL_OBSERVATION',w.id);
    if(!validDate(w.service_date)||!w.facility_id||!w.worker_id||!w.assignment_id||!w.source_revision||!w.role||!w.component)throw new InputError('INVALID_WORK_RECORD',w.id);
  }
  for(const r of rules){
    if(!ratePattern.test(r.rate)||!validDate(r.effective_from)||(r.effective_to&&(!validDate(r.effective_to)||r.effective_to<=r.effective_from))||(r.authorization_date&&!validDate(r.authorization_date)))throw new InputError('INVALID_RULE',r.id);
    if(r.state==='approved'&&(!r.approved_at||Number.isNaN(Date.parse(r.approved_at))||!r.author_id||!r.approver_id||r.approver_id===r.author_id||!raw.excerpts.some(e=>e.id===r.source_excerpt_id)))throw new InputError('INVALID_RULE_APPROVAL',r.id);
  }
  for(const l of invoices){
    if(!moneyPattern.test(l.amount)||!ratePattern.test(l.unit_rate)||!Number.isSafeInteger(l.minutes)||l.minutes<0)throw new InputError('INVALID_INVOICE_LINE',l.id);
    if(l.billing_basis!==undefined&&!['hourly','non_hourly'].includes(l.billing_basis))throw new InputError('INVALID_BILLING_BASIS',l.id);
    if(l.billing_basis==='non_hourly'&&(l.currency!=='USD'||l.minutes!==0||!new D(l.unit_rate).isZero()||l.shift_ids.length))throw new InputError('INVALID_NON_HOURLY_LINE',l.id);
    if((l.document_kind==='credit'&&new D(l.amount).gt(0))||(l.document_kind!=='credit'&&new D(l.amount).lt(0)))throw new InputError('INVALID_INVOICE_SIGN',l.id);
  }
  const m=raw.manifest;
  if(m.currency!=='USD'||[m.as_of,m.billing_cutoff,m.invoice_source_as_of].some(t=>Number.isNaN(Date.parse(t))))throw new InputError('INVALID_MANIFEST','manifest');
  const selected=new Map(work.map(w=>[w.id,selectRule(w,rules)]));
  const blockers=new Map<string,string>(); const allocations:Allocation[]=[];
  for(const l of invoices.filter(l=>l.state==='posted'&&l.billing_basis!=='non_hourly')){
    const refs=[...new Set(l.shift_ids)].sort(), matched=refs.map(id=>work.find(w=>w.id===id));
    let reason='';
    if(!refs.length||matched.some(w=>!w)||refs.length!==l.shift_ids.length)reason='AMBIGUOUS_REFERENCE';
    else if(matched.some(w=>w!.facility_id!==l.facility_id))reason='AMBIGUOUS_REFERENCE';
    else if(l.currency!=='USD')reason='CURRENCY_MISMATCH';
    else if(!['invoice','debit','credit'].includes(l.document_kind))reason='UNSUPPORTED_INVOICE_COMPONENT';
    else if(l.document_kind==='credit'&&(!l.chain_id||!invoices.some(original=>original.state==='posted'&&original.document_kind!=='credit'&&original.chain_id===l.chain_id&&original.facility_id===l.facility_id&&original.currency===l.currency&&canonical([...original.shift_ids].sort())===canonical(refs))))reason='UNSUPPORTED_CREDIT_LINEAGE';
    else if(l.chain_id&&invoices.some(other=>other.chain_id===l.chain_id&&(other.facility_id!==l.facility_id||other.currency!==l.currency||canonical([...other.shift_ids].sort())!==canonical(refs))))reason='AMBIGUOUS_REFERENCE';
    else if(refs.length>1){
      const ws=matched as Work[], rs=ws.map(w=>selected.get(w.id)!);
      if(rs.some(r=>r.length!==1)||new Set(rs.map(r=>r[0]?.rate)).size!==1||new Set(ws.map(w=>`${w.component}/${w.role}`)).size!==1||ws.reduce((a,w)=>a+w.worked_minutes,0)!==l.minutes||l.minutes===0)reason='AMBIGUOUS_AGGREGATE';
    }
    if(reason){for(const w of work.filter(w=>w.facility_id===l.facility_id&&(!refs.length||refs.includes(w.id)||matched.some(x=>!x))))blockers.set(w.id,reason);continue;}
    const ws=matched as Work[];
    const shares=ws.map(w=>({line_id:l.id,invoice_id:l.invoice_id,shift_id:w.id,amount:refs.length===1?l.amount:new D(l.amount).mul(w.worked_minutes).div(l.minutes).toFixed(2),chain_id:l.chain_id}));
    if(sum(shares.map(a=>a.amount))!==l.amount){for(const w of ws)blockers.set(w.id,'AMBIGUOUS_AGGREGATE');continue;}
    allocations.push(...shares);
  }
  
  const invoiceBatches=batches.filter(b=>b.source.startsWith('invoice')||invoices.some(l=>l.batch_id===b.id));
  const sourceComplete=m.invoice_coverage_complete&&invoiceBatches.length>0&&invoiceBatches.every(b=>b.declared_complete&&Date.parse(b.source_as_of)>=Date.parse(m.billing_cutoff)&&!!b.service_from&&!!b.service_to_exclusive&&b.service_from<=m.service_from&&b.service_to_exclusive>=m.service_to_exclusive)&&Date.parse(m.invoice_source_as_of)>=Date.parse(m.billing_cutoff);
  const records:Evaluated[]=work.map(w=>{
    const time=batches.find(b=>b.id===w.batch_id);
    const base={work:w,expected_amount:null,invoiced_amount:null,discrepancy_amount:null,allocations:allocations.filter(a=>a.shift_id===w.id)};
    if(w.approval_state!=='approved'||(!w.approved_at&&!w.approval_observed_at))return {...base,category:'not_evaluated',reason_code:'TIME_APPROVAL_PENDING'};
    if(!time?.declared_complete||w.service_date<m.service_from||w.service_date>=m.service_to_exclusive||(time.service_from&&w.service_date<time.service_from)||(time.service_to_exclusive&&w.service_date>=time.service_to_exclusive))return {...base,category:'not_evaluated',reason_code:'WORK_SOURCE_INCOMPLETE'};
    if(blockers.has(w.id))return {...base,category:'abstained',reason_code:blockers.get(w.id)!};
    const rs=selected.get(w.id)!;
    if(!['standard','overtime','holiday','weekend','on_call','callback'].includes(w.component))return {...base,category:'abstained',reason_code:'UNSUPPORTED_COMPONENT'};
    if(!rs.length)return {...base,category:'abstained',reason_code:'UNSUPPORTED_COMPONENT'};
    if(rs.length!==1)return {...base,category:'abstained',reason_code:'CONFLICTING_APPROVED_RULES'};
    const rule=rs[0];
    if((rule.authorization_date||rule.approved_at!.slice(0,10))>w.service_date)return {...base,category:'abstained',reason_code:'RETROACTIVE_RULE_APPROVAL_UNSUPPORTED'};
    if(rule.currency!=='USD')return {...base,category:'abstained',reason_code:'CURRENCY_MISMATCH'};
    const endDate=w.service_end_date;
    if(endDate&&rules.some(r=>r.state==='approved'&&r.facility_id===w.facility_id&&r.role===w.role&&r.component===w.component&&r.effective_from>w.service_date&&r.effective_from<=endDate))return {...base,category:'abstained',reason_code:'RATE_BOUNDARY_REQUIRES_SEGMENTATION'};
    const approval=w.approved_at||w.approval_observed_at!,dateOnly=w.approved_at?w.approval_date_only:w.approval_observation_date_only,latestApproval=dateOnly?Math.min(Date.parse(approval.slice(0,10)+'T23:59:59.999Z'),Date.parse(m.as_of)):Date.parse(approval);
    if(latestApproval>Date.parse(m.billing_cutoff))return {...base,category:'not_evaluated',reason_code:dateOnly||!w.approved_at?'APPROVAL_TIMING_NOT_ESTABLISHED':'APPROVAL_AFTER_BILLING_CUTOFF'};
    if(Date.parse(m.billing_cutoff)<Date.parse(m.service_to_exclusive+'T00:00:00Z'))return {...base,category:'not_evaluated',reason_code:'BILLING_SCOPE_AFTER_CUTOFF'};
    if(!sourceComplete)return {...base,category:'not_evaluated',reason_code:'INVOICE_SOURCE_INCOMPLETE'};
    if(!base.allocations.length&&Date.parse(m.as_of)<Date.parse(m.billing_cutoff))return {...base,category:'not_evaluated',reason_code:'BILLING_CYCLE_OPEN'};
    const exp=expected(w.worked_minutes,rule.rate), billed=sum(base.allocations.map(a=>a.amount)), delta=difference(exp,billed);
    const ratesDiffer=base.allocations.some(a=>!new D(invoices.find(l=>l.id===a.line_id)!.unit_rate).eq(rule.rate));
    return {...base,rule,expected_amount:exp,invoiced_amount:billed,discrepancy_amount:delta,category:delta==='0.00'?'evaluated_aligned':'evaluated_flagged',reason_code:delta==='0.00'?'ALIGNED':!base.allocations.length?'APPROVED_WORK_NOT_IN_INVOICE_EXTRACT':ratesDiffer?'APPROVED_RATE_MISMATCH':'EXPECTED_INVOICE_AMOUNT_MISMATCH'};
  });
  const groups=new Map<string,Evaluated[]>();
  for(const r of records.filter(r=>r.category==='evaluated_flagged')){
    const key=`${r.work.facility_id}/${r.rule!.id}/${r.reason_code}/${new D(r.discrepancy_amount!).isNegative()?'over':'under'}`;
    groups.set(key,[...(groups.get(key)||[]),r]);
  }
  const findings:Finding[]=[...groups.values()].map((rs,i)=>({id:`FND-${String(i+1).padStart(3,'0')}`,dataset_id:m.dataset_id,reason_code:rs[0].reason_code,shift_ids:rs.map(r=>r.work.id),facility_id:rs[0].work.facility_id,rule_version_id:rs[0].rule!.id,expected_amount:sum(rs.map(r=>r.expected_amount!)),invoiced_amount:sum(rs.map(r=>r.invoiced_amount!)),discrepancy_amount:sum(rs.map(r=>r.discrepancy_amount!)),currency:'USD',state:'needs_review',collectibility:'unknown',fingerprint:evidenceFingerprint({reason_code:rs[0].reason_code,invoices:invoices.filter(l=>l.state==='posted'&&l.shift_ids.some(id=>rs.some(r=>r.work.id===id))).map(({batch_id,...l})=>({...l,unit_rate:new D(l.unit_rate).toFixed(4),shift_ids:[...l.shift_ids].sort()})),records:rs.map(r=>({id:r.work.id,revision:r.work.source_revision,facility:r.work.facility_id,worker:r.work.worker_id,assignment:r.work.assignment_id,date:r.work.service_date,minutes:r.work.worked_minutes,approval:r.work.approval_state,approved_at:r.work.approved_at,approval_observed_at:r.work.approval_observed_at,approval_date_only:r.work.approval_date_only,approval_observation_date_only:r.work.approval_observation_date_only,rule:r.rule,allocations:r.allocations})),excerpt:raw.excerpts.filter(e=>rs.some(r=>r.rule!.source_excerpt_id===e.id)),complete:sourceComplete,cutoff:m.billing_cutoff},'ev1:')}));
  const categories=Object.fromEntries((['evaluated_aligned','evaluated_flagged','abstained','not_evaluated'] as Category[]).map(c=>{const rs=records.filter(r=>r.category===c);return[c,{records:rs.length,minutes:rs.reduce((s,r)=>s+r.work.worked_minutes,0),shift_ids:rs.map(r=>r.work.id)}];})) as Record<Category,Partition>;
  const taskGroups=new Map<string,Evaluated[]>();
  for(const r of records.filter(r=>['abstained','not_evaluated'].includes(r.category)))taskGroups.set(r.reason_code,[...(taskGroups.get(r.reason_code)||[]),r]);
  const taskOrder=[...taskGroups.values()].sort((a,b)=>a[0].work.id.localeCompare(b[0].work.id));
  const tasks=taskOrder.map((rs,i)=>({id:`GAP-${String(i+1).padStart(3,'0')}`,shift_ids:rs.map(r=>r.work.id),reason_code:rs[0].reason_code,category:rs[0].category as 'abstained'|'not_evaluated',amount:null}));
  const evaluated=records.filter(r=>r.expected_amount!==null);
  return {id:m.run_id,status:'completed',engine_version:'sc-engine-1.1.0',calendar_version:m.synthetic?'sc-demo-calendar-v1':'explicit-components-v1',fingerprint:evidenceFingerprint({work,invoices,rules,batches,manifest:m}),manifest:{...m},batch_ids:batches.map(b=>b.id),rule_version_ids:rules.filter(r=>r.state==='approved').map(r=>r.id),records,findings,tasks,allocations,...(nonHourly.length?{non_hourly_lines:nonHourly}:{}),coverage:{received_records:work.length,received_minutes:work.reduce((s,w)=>s+w.worked_minutes,0),evaluated_records:evaluated.length,evaluated_minutes:evaluated.reduce((s,r)=>s+r.work.worked_minutes,0),categories},totals:{expected:sum(evaluated.map(r=>r.expected_amount!)),invoiced:sum(invoices.filter(l=>l.state==='posted'&&['invoice','debit','credit'].includes(l.document_kind)&&l.currency==='USD').map(l=>l.amount)),underbilling:sum(findings.filter(f=>new D(f.discrepancy_amount).gt(0)).map(f=>f.discrepancy_amount)),overbilling:sum(findings.filter(f=>new D(f.discrepancy_amount).lt(0)).map(f=>new D(f.discrepancy_amount).abs().toFixed(2)))}};
}
