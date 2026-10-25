import {it,expect} from 'vitest';
import {execFileSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {buildLocalBundle,parseCsv,suggestMapping,type Kind,type LocalPeriod} from './local-tables';
it('browser and private-server adapters agree on financial semantics for the varied fixture',()=>{
 const sources=(['work','invoices','rates'] as Kind[]).map(kind=>{const table=parseCsv(kind+'.csv',readFileSync('public/examples/agency-evaluation/'+kind+'.csv','utf8'),'a'.repeat(64)),config=suggestMapping(table,kind);config.confirmed=true;return {kind,table,config};});
 const period:LocalPeriod={from:'2026-10-05',to:'2026-10-11',asOf:'2026-10-14T00:00:00Z',cutoff:'2026-10-13T00:00:00Z',workComplete:true,invoiceComplete:true,workHours:'69',invoiceTotal:'3501.00',author:'AUTHOR-1',approver:'APPROVER-2'};
 const local=buildLocalBundle(sources,period).inputs,server=JSON.parse(execFileSync('python3',['tests/adoption-normalize.py'],{encoding:'utf8'}));
 const select=(rows:Record<string,unknown>[],keys:string[])=>rows.map(row=>Object.fromEntries(keys.map(key=>[key,typeof row[key]==='string'&&String(row[key]).includes('T00:00:00')?Date.parse(String(row[key])):row[key]??null]))).sort((a,b)=>String(a.id).localeCompare(String(b.id)));
 for(const [kind,keys] of Object.entries({work:['id','facility_id','worker_id','role','component','service_date','worked_minutes','approval_state','approved_at','approval_observed_at'],invoices:['id','invoice_id','facility_id','state','document_kind','amount','currency','minutes','unit_rate','shift_ids','chain_id','billing_basis'],rates:['id','contract_id','facility_id','role','component','rate','currency','effective_from','effective_to','authorization_date','supersedes']}))expect(select(local[(kind==='rates'?'rules':kind) as 'work'] as unknown as Record<string,unknown>[],keys)).toEqual(select(server[kind],keys));
});
