import {reconcile,canonical,difference,sum} from './engine';
import {validateRateApproval} from './rate-approval';
import type {Inputs,Rule,Run,Reviews,Review,Finding,Event} from './types';
export const findingKey=(f:Finding)=>`${f.dataset_id}/${f.facility_id}/${f.rule_version_id}/${f.reason_code}/${f.discrepancy_amount.startsWith('-')?'over':'under'}`;
export interface Demo { inputs:Inputs; run:Run|null; reviews:Reviews; stale:boolean; error:string|null; importState:'validated'|'quarantined'|'failed'; draft:Rule; ruleHistory:Event[]; approvedFutureRules:Rule[]; localTasks:Event[] }
export function initialDemo(inputs:Inputs,draft:Rule):Demo {return {inputs:structuredClone(inputs),run:reconcile(inputs),reviews:{},stale:false,error:null,importState:'validated',draft:structuredClone(draft),ruleHistory:[],approvedFutureRules:[],localTasks:[]};}
function nextEvent(history:Event[],action:string,reason:string,fingerprint:string,timestamp:string,actor='DEMO-REVIEWER',owner?:string):Event{return {sequence:history.length+1,action,reason:reason.trim(),owner,actor,timestamp,fingerprint};}
export function publish(state:Demo,inputs:Inputs,context?:{actor:string;timestamp:string}):Demo {
 try {
  const run=reconcile(inputs),reviews:Reviews={...state.reviews};
  for(const f of run.findings){const key=findingKey(f);
    const predecessor=state.run?.findings.find(prior=>prior.dataset_id===f.dataset_id&&prior.facility_id===f.facility_id&&prior.shift_ids.some(id=>f.shift_ids.includes(id)));
    const old=reviews[key]||(predecessor?reviews[findingKey(predecessor)]:undefined);if(old&&old.fingerprint!==f.fingerprint)reviews[key]={state:'needs_review',fingerprint:f.fingerprint,version:old.version+1,history:[...old.history,nextEvent(old.history,'reopened','Underlying evidence changed; review required again.',f.fingerprint,context?.timestamp||run.manifest.as_of,context?.actor||'DEMO-REVIEWER')]};}
  return {...state,inputs:structuredClone(inputs),run,reviews,stale:false,error:null,importState:'validated'};
 }catch(error){return {...state,stale:!!state.run,error:error instanceof Error?error.message:'Validation failed',importState:'failed'};}
}
export function decide(state:Demo,f:Finding,action:'confirm'|'dismiss'|'request_evidence'|'reopen',reason:string,owner?:string,expectedVersion?:number,context?:{actor:string;timestamp:string}):Demo {
 if(!state.run||state.stale)throw new Error('Refresh validated evidence before reviewing stale results.');
 const current=state.run.findings.find(x=>findingKey(x)===findingKey(f));
 if(!current||current.fingerprint!==f.fingerprint)throw new Error('Evidence changed. Refresh before recording a decision.');
 const key=findingKey(f),old:Review=state.reviews[key]||{state:'needs_review',fingerprint:f.fingerprint,history:[],version:1};
 if(expectedVersion!==undefined&&old.version!==expectedVersion)throw new Error('Review version conflict. Refresh this finding.');
 if(reason.trim().length<3||reason.length>2000)throw new Error('Enter a reason between 3 and 2,000 characters.');
 if(action==='request_evidence'&&!owner?.trim())throw new Error('Choose an owner for the local evidence task.');
 const event=nextEvent(old.history,action,reason,f.fingerprint,context?.timestamp||state.run.manifest.as_of,context?.actor||'DEMO-REVIEWER',owner);
 return {...state,reviews:{...state.reviews,[key]:{state:({confirm:'confirmed',dismiss:'dismissed',request_evidence:'evidence_requested',reopen:'needs_review'} as const)[action],fingerprint:f.fingerprint,history:[...old.history,event],version:old.version+1}},localTasks:action==='request_evidence'?[...state.localTasks,event]:state.localTasks};
}
export function approveRule(state:Demo,actor:string,authorized=false,timestamp?:string,reason?:string):Demo {
 const d=state.draft;
 if(actor===d.author_id)throw new Error('SEPARATE_APPROVER_REQUIRED — a different person must approve this rule.');
 if(!authorized&&actor!=='DEMO-APPROVER')throw new Error('Demo approver role required.');
 if(d.state!=='pending_approval')throw new Error('Only a pending rule may be approved.');
 if(!state.inputs.excerpts.some(e=>e.id===d.source_excerpt_id)||!d.effective_from||!d.supersedes)throw new Error('Source, interval and predecessor required.');
 const allRules=[...state.inputs.rules,...state.approvedFutureRules];
 validateRateApproval(d,actor,allRules,state.inputs.excerpts.map(e=>e.id));
 const approved:Rule={...d,id:d.id.replace('-DRAFT',''),state:'approved',approver_id:actor,recorded_at:state.inputs.manifest.as_of,approved_at:timestamp||state.inputs.manifest.as_of};
 return {...state,draft:approved,approvedFutureRules:[...state.approvedFutureRules,approved],ruleHistory:[...state.ruleHistory,nextEvent(state.ruleHistory,'rule_approved',reason||'Source reviewed; independent approval. Outside RUN-001.',canonical(approved),timestamp||state.inputs.manifest.as_of,actor)]};
}
export function rejectRule(state:Demo,actor:string,reason:string,authorized=false,timestamp?:string):Demo {
 if((!authorized&&actor!=='DEMO-APPROVER')||actor===state.draft.author_id)throw new Error('Separate demo approver required.');
 if(reason.trim().length<3)throw new Error('A rejection reason is required.');
 if(state.draft.state!=='pending_approval')throw new Error('Only a pending rule may be rejected.');
 return {...state,draft:{...state.draft,state:'rejected'},ruleHistory:[...state.ruleHistory,nextEvent(state.ruleHistory,'rule_rejected',reason,canonical(state.draft),timestamp||state.inputs.manifest.as_of,actor)]};
}
export type Scenario='canonical'|'incomplete'|'partial'|'changed'|'failed'|'empty';
export function scenarioInputs(baseline:Inputs,scenario:Scenario):Inputs {
 const inputs=structuredClone(baseline);
 if(scenario==='incomplete'){inputs.manifest.run_id='RUN-INCOMPLETE';inputs.manifest.invoice_coverage_complete=false;inputs.batches[1].declared_complete=false;inputs.batches[1].state='incomplete';}
 if(scenario==='changed'){inputs.manifest.run_id='RUN-002';inputs.invoices[0].amount='590.00';inputs.batches[1].signed_control_total=sum(inputs.invoices.map(l=>l.amount));}
 if(scenario==='failed'){inputs.work[0].worked_minutes=-60;inputs.manifest.run_id='RUN-FAILED';}
 if(scenario==='partial'){
  inputs.manifest.run_id='RUN-PARTIAL';for(const l of inputs.invoices.filter(l=>l.shift_ids.some(id=>['S001','S002','S003','S004'].includes(id)))){l.amount='650.00';l.unit_rate='65.0000';}
  for(const id of ['S005','S006'])inputs.invoices.push({id:`DEMO-${id}`,invoice_id:'INV-DEMO-ALIGNED',facility_id:'FAC-002',state:'posted',document_kind:'invoice',amount:'780.00',currency:'USD',minutes:720,unit_rate:'65.0000',shift_ids:[id],chain_id:null,batch_id:'BATCH-INV-001'});
  inputs.batches[1].signed_control_total=sum(inputs.invoices.map(l=>l.amount));inputs.batches[1].records=inputs.invoices.length;
 }
 if(scenario==='empty'){inputs.manifest.run_id='RUN-EMPTY';inputs.manifest.invoice_coverage_complete=false;inputs.work=[];inputs.invoices=[];inputs.rules=[];inputs.batches=[];}
 return inputs;
}
export function safeCell(value:string){const protectedValue=/^[\s\u0000-\u001f]*[=+\-@]/.test(value)?`'${value}`:value;return `"${protectedValue.replaceAll('"','""')}"`;}
export function exportReviews(state:Demo):string {
 if(!state.run)throw new Error('No completed run to export.');
 const r=state.run;
 const header=['finding_id','run_id','dataset_id','source_batch_ids','rule_version_id','shift_ids','expected_usd','invoiced_usd','signed_discrepancy_usd','decision','reason','reviewer','coverage_limitations','as_of','engine_version','collectibility'];
 const rows=r.findings.flatMap(f=>{const review=state.reviews[findingKey(f)];if(!review||review.state==='needs_review')return [];const e=review.history.at(-1)!;return [[f.id,r.id,r.manifest.dataset_id,r.batch_ids.join(';'),f.rule_version_id,f.shift_ids.join(';'),f.expected_amount,f.invoiced_amount,`${f.discrepancy_amount.startsWith('-')?'':'+'}${f.discrepancy_amount}`,review.state,e.reason.replace(/[\u0000-\u001f]/g,' '),e.actor,`Synthetic only; ${r.coverage.evaluated_records}/${r.coverage.received_records} records checked; ${r.tasks.length} coverage tasks; ${state.stale?'STALE prior run; ':''}no payment evidence`,r.manifest.as_of,r.engine_version,'unknown']];});
 return [header,...rows].map(row=>row.map(safeCell).join(',')).join('\r\n')+'\r\n';
}
