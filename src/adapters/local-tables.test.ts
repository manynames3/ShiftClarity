import {readFileSync} from 'node:fs';
import {describe,it,expect} from 'vitest';
import {parseCsv,suggestMapping,buildLocalBundle,decimalValue,LocalImportError,type Kind,type LocalPeriod} from './local-tables';
import {reconcile} from '../domain/engine';
const period:LocalPeriod={from:'2026-10-05',to:'2026-10-11',asOf:'2026-10-14T00:00:00Z',cutoff:'2026-10-13T00:00:00Z',workComplete:true,invoiceComplete:true,workHours:'69',invoiceTotal:'3501.00',author:'AUTHOR-1',approver:'APPROVER-2'};
function sources(){return (['work','invoices','rates'] as Kind[]).map(kind=>{const table=parseCsv(kind+'.csv',readFileSync('public/examples/agency-evaluation/'+kind+'.csv','utf8'),'a'.repeat(64)),config=suggestMapping(table,kind);config.confirmed=true;return {kind,table,config};});}
describe('local agency exports',()=>{
 it('reconciles varied work, missing billing, credits, fees and evidence gaps against independent expected values',()=>{
  const result=buildLocalBundle(sources(),period),run=reconcile(result.inputs);
  expect(run.coverage).toMatchObject({received_records:8,evaluated_records:6,received_minutes:4140,evaluated_minutes:3240});
  expect(run.totals).toEqual({expected:'3912.00',invoiced:'3501.00',underbilling:'460.00',overbilling:'24.00'});
  expect(run.tasks.map(t=>t.reason_code)).toEqual(['TIME_APPROVAL_PENDING','UNSUPPORTED_COMPONENT']);
  expect(run.non_hourly_lines).toHaveLength(1);expect(run.allocations.filter(a=>a.shift_id==='W6').map(a=>a.amount)).toEqual(['-720.00','720.00','700.00']);
  expect(result.inputs.manifest.synthetic).toBe(false);expect(result.warnings).toHaveLength(2);
 });
 it('never estimates differences from incomplete exports',()=>{const run=reconcile(buildLocalBundle(sources(),{...period,invoiceComplete:false}).inputs);expect(run.findings).toEqual([]);expect(run.coverage.evaluated_records).toBe(0);});
 it('fails the whole import with row corrections rather than dropping invalid lines',()=>{const s=sources();s[0].table.rows[0].values[6]='7.3333';s[0].config.unit='hours';s[0].config.columns.hours='Rounded quantity';s[0].table.headers[6]='Rounded quantity';expect(()=>buildLocalBundle(s,period)).toThrow(LocalImportError);});
 it('rejects mismatched time units before calculation',()=>{const s=sources();s[0].config.unit='hours';expect(()=>buildLocalBundle(s,period)).toThrow('labeled in minutes');});
 it('requires an independent control total match and distinct supplied approval identities',()=>{expect(()=>buildLocalBundle(sources(),{...period,invoiceTotal:'3476.00'})).toThrow('Independent signed');expect(()=>buildLocalBundle(sources(),{...period,approver:'AUTHOR-1'})).toThrow('distinct');});
 it('does not reinterpret weekly totals as service dates or names as worker IDs',()=>{const t=parseCsv('weekly.csv',readFileSync('public/examples/agency-evaluation/avionte-style-weekly-summary.csv','utf8'));const map=suggestMapping(t,'work');expect(map.columns.service_date).toBeUndefined();expect(map.columns.worker_id).toBeUndefined();expect(()=>parseCsv('personal.csv','CandidateName,PhoneNumber\nPerson,555')).toThrow('Remove personal');});
 it('leaves ambiguous invoice-to-work joins as evidence gaps',()=>{const s=sources();const line=s[1].table.rows[0];line.values[3]='UNKNOWN';const run=reconcile(buildLocalBundle(s,period).inputs);expect(run.records.find(r=>r.work.id==='W1')?.expected_amount).toBeNull();});
 it('supports quoted multiline semicolon CSV and decimal commas without guessing',()=>{const t=parseCsv('export.csv','ID;Amount;Note\r\nA;"1.234,50";"first\nsecond"\r\n');expect(t.rows[0]).toEqual({number:2,values:['A','1.234,50','first\nsecond']});expect(decimalValue('1.234,50','comma',2).toFixed(2)).toBe('1234.50');expect(()=>decimalValue('1234.567','dot',2)).toThrow('precision');});
 it('retains physical source rows through quoted newlines and a selected report header',()=>{const t=parseCsv('report.csv','Fictional report\n\nID;Amount;Note\nA;1;"first\nsecond"\nB;2;last\n','',3);expect(t.headers).toEqual(['ID','Amount','Note']);expect(t.rows.map(r=>r.number)).toEqual([4,6]);expect(()=>parseCsv('report.csv','Title\n\nID,Amount\nA,1','',2)).toThrow('header row is blank');});
 it('bounds and validates malformed files',()=>{expect(()=>parseCsv('x.csv','ID,Amount\nA,"unclosed')).toThrow('unclosed');expect(()=>parseCsv('x.csv','ID,Amount\nA,1,2')).toThrow('same number');expect(()=>parseCsv('x.csv','ID,id\nA,B')).toThrow('unique');expect(()=>parseCsv('x.csv','ID\n'+('x'.repeat(2001)))).toThrow('2,000');});
});

it('retains an explicitly unsupported hourly component without forcing a guessed policy',()=>{const s=sources();s[0].table.rows[0].values[4]='ORIENTATION';s[0].config.values.component.ORIENTATION='unsupported';const run=reconcile(buildLocalBundle(s,period).inputs);expect(run.records.find(r=>r.work.id==='W1')).toMatchObject({category:'abstained',reason_code:'UNSUPPORTED_COMPONENT',expected_amount:null});});

it('accounts for repeated identical rate rows without treating row lineage as conflicting terms',()=>{const s=sources();s[2].table.rows.push({...s[2].table.rows[0],number:6});const result=buildLocalBundle(s,period);expect(result.inputs.rules).toHaveLength(4);expect(result.warnings.some(w=>w.includes('1 identical repeated record'))).toBe(true);expect(reconcile(result.inputs).totals.underbilling).toBe('460.00');});

it('does not reinterpret a numeric Excel rate as a thousands-formatted text rate',()=>{const s=sources();s[2].config.decimal='comma';s[2].table.rows[0].values[5]='12.125';s[2].table.numeric={2:['Contract Rate']};for(const row of s[2].table.rows.slice(1))row.values[5]=row.values[5].replace('.',',');expect(buildLocalBundle(s,period).inputs.rules[0].rate).toBe('12.1250');});

it('requires a closed service period before calling a complete extract missing billing',()=>{expect(()=>buildLocalBundle(sources(),{...period,cutoff:'2026-10-06T00:00:00Z'})).toThrow('service period ends');});
