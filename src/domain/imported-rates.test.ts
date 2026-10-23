import {describe,it,expect} from 'vitest';
import {freshInputs} from '../adapters/fixtures';
import {reconcile} from './engine';
import {approveRateBatch} from './rate-approval';

describe('explicit imported hourly terms',()=>{
 for(const component of ['standard','overtime','holiday','weekend','on_call','callback'])it(component+' evaluates only against an explicit approved matching rate',()=>{
  const inputs=freshInputs();
  const work=inputs.work[0],rate=inputs.rules.find(r=>r.id==='RULE-001-V2')!;
  work.role='LPN';work.component=component;
  rate.role='LPN';rate.component=component;
  const row=reconcile(inputs).records.find(r=>r.work.id===work.id)!;
  expect(row.expected_amount).toBe('650.00');
  inputs.rules=inputs.rules.filter(r=>r.id!==rate.id);
  expect(reconcile(inputs).records.find(r=>r.work.id===work.id)!.expected_amount).toBeNull();
 });
 it('retains actual approval time while independently attesting historical authorization',()=>{
  const inputs=freshInputs();const rate=inputs.rules.find(r=>r.id==='RULE-001-V2')!;
  rate.approved_at='2026-10-23T12:00:00Z';
  expect(reconcile(inputs).records.find(r=>r.work.id==='S001')!.reason_code).toBe('RETROACTIVE_RULE_APPROVAL_UNSUPPORTED');
  rate.authorization_date='2026-10-03';
  expect(reconcile(inputs).records.find(r=>r.work.id==='S001')!.expected_amount).toBe('650.00');
  expect(rate.approved_at).toBe('2026-10-23T12:00:00Z');
 });
 it('batch approval denies self-approval and conflicting intervals',()=>{
  const inputs=freshInputs();const original=inputs.rules[0];
  const candidate={...original,id:'NEW-RATE',author_id:'IMPORTER',approver_id:null,state:'pending_approval'};
  expect(()=>approveRateBatch([candidate],[],[candidate.source_excerpt_id],'IMPORTER','2026-10-23T12:00:00Z')).toThrow(/different person/);
  expect(()=>approveRateBatch([candidate],inputs.rules,[candidate.source_excerpt_id],'APPROVER','2026-10-23T12:00:00Z')).toThrow(/Conflicting/);
 });
});
