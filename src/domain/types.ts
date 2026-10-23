export type Category = 'evaluated_aligned'|'evaluated_flagged'|'abstained'|'not_evaluated';
export type ReviewState = 'needs_review'|'confirmed'|'dismissed'|'evidence_requested';
export interface Work { id:string; source_revision:string; facility_id:string; worker_id:string; assignment_id:string; role:string; component:string; service_date:string; service_end_date?:string; timezone:string; worked_minutes:number; approval_state:string; recorded_at:string; approved_at:string|null; batch_id:string }
export interface Rule { id:string; contract_id:string; facility_id:string; role:string; component:string; rate:string; currency:string; effective_from:string; effective_to:string|null; state:string; source_excerpt_id:string; author_id:string; approver_id:string|null; recorded_at?:string; approved_at?:string; authorization_date?:string; supersedes:string|null }
export interface Invoice { id:string; invoice_id:string; facility_id:string; state:string; document_kind:string; amount:string; currency:string; minutes:number; unit_rate:string; shift_ids:string[]; chain_id:string|null; batch_id:string }
export interface Batch { id:string; source:string; records:number; state:string; source_as_of:string; service_from?:string; service_to_exclusive?:string; declared_complete:boolean; control_total_minutes?:number; signed_control_total?:string }
export interface Manifest { dataset_id:string; synthetic:boolean; version:string; run_id:string; as_of:string; timezone:string; currency:string; service_from:string; service_to_exclusive:string; billing_cutoff:string; invoice_source_as_of:string; invoice_coverage_complete:boolean; workspace_label:string; note:string }
export interface Excerpt { id:string; document_id:string; title?:string; lines?:string[]; label?:string; text?:string; synthetic?:boolean }
export interface Inputs { work:Work[]; invoices:Invoice[]; rules:Rule[]; batches:Batch[]; excerpts:Excerpt[]; manifest:Manifest }
export interface Allocation { line_id:string; invoice_id:string; shift_id:string; amount:string; chain_id:string|null }
export interface Evaluated { work:Work; category:Category; reason_code:string; rule?:Rule; expected_amount:string|null; invoiced_amount:string|null; discrepancy_amount:string|null; allocations:Allocation[] }
export interface Finding { id:string; dataset_id:string; reason_code:string; shift_ids:string[]; facility_id:string; rule_version_id:string; expected_amount:string; invoiced_amount:string; discrepancy_amount:string; currency:'USD'; state:ReviewState; collectibility:'unknown'; fingerprint:string }
export interface Task { id:string; shift_ids:string[]; reason_code:string; category:'abstained'|'not_evaluated'; amount:null }
export interface Partition { records:number; minutes:number; shift_ids:string[] }
export interface Run { id:string; status:'completed'; engine_version:string; calendar_version:string; fingerprint:string; manifest:Manifest; batch_ids:string[]; rule_version_ids:string[]; records:Evaluated[]; findings:Finding[]; tasks:Task[]; allocations:Allocation[]; coverage:{received_records:number;received_minutes:number;evaluated_records:number;evaluated_minutes:number;categories:Record<Category,Partition>}; totals:{expected:string; invoiced:string; underbilling:string; overbilling:string} }
export interface Event { sequence:number; action:string; reason:string; owner?:string; actor:string; timestamp:string; fingerprint:string }
export interface Review { state:ReviewState; fingerprint:string; history:Event[]; version:number }
export type Reviews = Record<string,Review>;
