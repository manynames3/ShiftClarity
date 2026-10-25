import type {Finding, Reviews, ReviewState} from './domain/types';
import {findingKey} from './domain/demo';
export type FindingWorkflowMetadata={owner:string;priority:string;age:string};
const noWorkflowMetadata:FindingWorkflowMetadata={owner:'Not assigned',priority:'Not set',age:'Not available'};
const syntheticWorkflowMetadata:Readonly<Record<string,FindingWorkflowMetadata>>={
 'FND-001':{owner:'Not assigned',priority:'Standard',age:'1 day'},
 'FND-002':{owner:'Jordan Kim',priority:'High',age:'2 days'},
};
export function findingWorkflowMetadata(f:Finding,synthetic:boolean,reviews:Reviews={},owner?:string|null):FindingWorkflowMetadata{
 const metadata=synthetic&&f.dataset_id==='sc-demo-v1'?syntheticWorkflowMetadata[f.id]||noWorkflowMetadata:noWorkflowMetadata;
 const assigned=owner===undefined?[...(reviews[findingKey(f)]?.history||[])].reverse().find(e=>e.owner)?.owner:owner;
 return assigned?{...metadata,owner:actorLabel(assigned)}:metadata;
}
export const stateLabel:Record<ReviewState,string>={needs_review:'Needs review',confirmed:'Confirmed discrepancy',dismissed:'Not a discrepancy',evidence_requested:'Evidence requested'};
const reasonLabels:Record<string,string>={APPROVAL_TIMING_NOT_ESTABLISHED:'Approval by the billing cutoff needs evidence',APPROVAL_AFTER_BILLING_CUTOFF:'Work was approved after the billing cutoff',BILLING_SCOPE_AFTER_CUTOFF:'Service scope extends beyond the billing cutoff',APPROVED_RATE_MISMATCH:'Rate mismatch',APPROVED_WORK_NOT_IN_INVOICE_EXTRACT:'Not invoiced',EXPECTED_INVOICE_AMOUNT_MISMATCH:'Invoice amount mismatch',TIME_APPROVAL_PENDING:'Time approval pending',UNSUPPORTED_COMPONENT:'Unsupported billing component',INVOICE_SOURCE_INCOMPLETE:'Invoice source is incomplete',WORK_SOURCE_INCOMPLETE:'Work source is incomplete',BILLING_CYCLE_OPEN:'Billing cutoff is still open',CONFLICTING_APPROVED_RULES:'Approved terms conflict',AMBIGUOUS_REFERENCE:'Invoice reference needs evidence',AMBIGUOUS_AGGREGATE:'Aggregate invoice reference needs evidence',CURRENCY_MISMATCH:'Currency is outside the supported scope',UNSUPPORTED_CREDIT_LINEAGE:'Credit or rebill link needs evidence',RATE_BOUNDARY_REQUIRES_SEGMENTATION:'Shift crosses a rate boundary',RETROACTIVE_RULE_APPROVAL_UNSUPPORTED:'Retroactive approval is not supported',SEPARATE_APPROVER_REQUIRED:'A different person must approve this rule.',INVALID_WORKED_MINUTES:'Worked minutes must be a nonnegative whole number.',ALIGNED:'Aligned'};
const actorLabels:Record<string,string>={'DEMO-AUTHOR':'Morgan Lee, Rule author','DEMO-APPROVER':'Dana Reyes, Approver','DEMO-REVIEWER':'Jordan Kim, Reviewer','AUTHOR-001':'Morgan Lee, Rule author','APPROVER-002':'Dana Reyes, Approver'};
export const reasonLabel=(code:string)=>reasonLabels[code]||code.toLowerCase().replaceAll('_',' ').replace(/^./,c=>c.toUpperCase());
export const actorLabel=(actor:string)=>actorLabels[actor]||actor;
export const displayActors=(text:string)=>text.replaceAll('DEMO-AUTHOR',actorLabel('DEMO-AUTHOR')).replaceAll('DEMO-APPROVER',actorLabel('DEMO-APPROVER')).replaceAll('DEMO-REVIEWER',actorLabel('DEMO-REVIEWER')).replaceAll('AUTHOR-001',actorLabel('AUTHOR-001')).replaceAll('APPROVER-002',actorLabel('APPROVER-002'));
export function displayUserText(text:string){
 const readable=displayActors(text).replaceAll('Outside RUN-001','Outside this review period');
 const leadingCode=readable.match(/^([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)(?=[:—\s])/);
 if(leadingCode&&reasonLabels[leadingCode[1]])return reasonLabel(leadingCode[1]);
 return readable.replace(/\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b/g,reasonLabel);
}
export const sourceLabel=(source:string)=>({
 'work_records.csv':'Work records (CSV)',
 'invoice_lines.csv':'Invoice lines (CSV)',
 'rate_rules.json':'Approved rate terms (JSON)',
}[source]||source.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase()));
export function formatMoney(value:string,signed=false){const negative=value.startsWith('-'),[whole,cents]=value.replace('-','').split('.');return `${negative?'-':signed?'+':''}$${whole.replace(/\B(?=(\d{3})+(?!\d))/g,',')}.${cents}`;}
export const logicalKey=findingKey;
export const reviewFor=(f:Finding,r:Reviews)=>r[logicalKey(f)]||{state:'needs_review' as const,fingerprint:f.fingerprint,history:[],version:1};
export const titleFor=(f:Finding,synthetic=true)=>f.reason_code==='APPROVED_WORK_NOT_IN_INVOICE_EXTRACT'?'Approved work not invoiced':f.reason_code==='APPROVED_RATE_MISMATCH'?(synthetic?'Rate change not reflected':'Invoice rate differs from approved terms'):'Invoice amount differs';
