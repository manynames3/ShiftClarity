import {it,expect} from 'vitest';
import {freshInputs} from '../adapters/fixtures';
import {reconcile} from './engine';
it('retains non-hourly charges without allocating them or suppressing hourly findings',()=>{
 const input=freshInputs(),baseline=reconcile(input);
 const fee={...input.invoices[0],id:'FEE-1',invoice_id:'INV-FEE',billing_basis:'non_hourly' as const,amount:'75.00',minutes:0,unit_rate:'0.0000',shift_ids:[],chain_id:null};
 input.invoices.push(fee);input.batches[1].records++;input.batches[1].signed_control_total=(Number(input.batches[1].signed_control_total)+75).toFixed(2);
 const result=reconcile(input);
 expect(result.findings.map(f=>[f.reason_code,f.discrepancy_amount])).toEqual(baseline.findings.map(f=>[f.reason_code,f.discrepancy_amount]));
 expect(result.allocations.some(a=>a.line_id==='FEE-1')).toBe(false);
 expect(Number(result.totals.invoiced)).toBe(Number(baseline.totals.invoiced)+75);
});
it('rejects a non-hourly classification that still carries hourly allocations',()=>{
 const input=freshInputs();const wrong={...input.invoices[0],billing_basis:'non_hourly' as const};input.invoices[0]=wrong;
 expect(()=>reconcile(input)).toThrow('INVALID_NON_HOURLY_LINE');
});
it('distinguishes observed source approval from an unknown approval event timestamp',()=>{
 const input=freshInputs();input.work[0]={...input.work[0],approved_at:null,...{approval_observed_at:input.manifest.billing_cutoff}};
 expect(reconcile(input).records.find(r=>r.work.id===input.work[0].id)?.category).toBe('evaluated_flagged');
 input.work[0].approval_state='pending';expect(reconcile(input).records.find(r=>r.work.id===input.work[0].id)?.reason_code).toBe('TIME_APPROVAL_PENDING');
});
it('cannot use a future reported-status observation as approval evidence',()=>{
 const input=freshInputs();input.work[0]={...input.work[0],approved_at:null,...{approval_observed_at:'2099-01-01T00:00:00Z'}};
 expect(()=>reconcile(input)).toThrow('INVALID_APPROVAL_OBSERVATION');
});

it('includes outside-hourly lines and observed approval provenance in the report',async()=>{
 const {initialDemo}=await import('./demo'),{billingReport}=await import('./report'),{draftRule}=await import('../adapters/fixtures');
 const input=freshInputs();input.work[0].approved_at=null;input.work[0].approval_observed_at=input.manifest.as_of;
 input.invoices.push({...input.invoices[0],id:'FEE-ONLY',billing_basis:'non_hourly',amount:'25.00',minutes:0,unit_rate:'0.0000',shift_ids:[],chain_id:null});
 const report=billingReport(initialDemo(input,draftRule));
 expect(report.tables.find(t=>t.name==='Non-hourly invoice lines')?.rows[0]).toContain(25);
 const calculation=report.tables.find(t=>t.name==='Work calculations')!;expect(calculation.headers.slice(14,16)).toEqual(['Work approval event date','Approved status observed at']);expect(calculation.rows.find(row=>row[0]===input.work[0].id)?.slice(14,16)).toEqual(['Unknown',input.manifest.as_of]);
});

it('rejects future or invalid original work approval evidence',()=>{const input=freshInputs();input.work[0].approved_at='2099-01-01T00:00:00Z';expect(()=>reconcile(input)).toThrow('INVALID_WORK_APPROVAL');input.work[0].approved_at='not-a-date';expect(()=>reconcile(input)).toThrow('INVALID_WORK_APPROVAL');});

it('does not call approval after the billing cutoff missing billing',()=>{const input=freshInputs();const w=input.work.find(w=>w.id==='S005')!;w.approved_at=input.manifest.billing_cutoff;input.manifest.as_of='2026-10-14T00:00:00Z';w.approved_at='2026-10-13T00:00:00Z';expect(reconcile(input).records.find(r=>r.work.id===w.id)?.expected_amount).toBeNull();});
it('labels own-file rate approvals as declarations rather than authenticated accounts',async()=>{const {initialDemo}=await import('./demo'),{billingReport}=await import('./report'),{draftRule}=await import('../adapters/fixtures');const i=freshInputs();i.manifest.synthetic=false;const t=billingReport(initialDemo(i,draftRule)).tables.find(t=>t.name==='Rate terms')!;expect(t.headers).not.toContain('System approved at');expect(t.headers).toContain('Declared approver reference');});

it('treats a same-day date-only approval as unknown by a midday cutoff',()=>{const input=freshInputs(),w=input.work[0];w.approved_at='2026-10-12T00:00:00Z';w.approval_date_only=true;expect(reconcile(input).records.find(r=>r.work.id===w.id)).toMatchObject({reason_code:'APPROVAL_TIMING_NOT_ESTABLISHED',expected_amount:null});w.approved_at='2026-10-11T00:00:00Z';expect(reconcile(input).records.find(r=>r.work.id===w.id)?.expected_amount).not.toBeNull();});

it('requires evidence of approval by cutoff when status was observed only afterwards',()=>{const input=freshInputs();input.work[0].approved_at=null;input.work[0].approval_observed_at=input.manifest.as_of;expect(reconcile(input).records.find(r=>r.work.id===input.work[0].id)?.reason_code).toBe('APPROVAL_TIMING_NOT_ESTABLISHED');});
