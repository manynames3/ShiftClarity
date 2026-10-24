import {test,expect} from '@playwright/test';
import {writeFile} from 'node:fs/promises';
import {cognitoLogin} from '../pilot/cognito-auth';
const cloud=process.env.SHIFTCLARITY_CAPACITY_AWS_QA==='1';
test('declared synthetic capacity imports, reconciles and exports through the live gateway',async({page})=>{
 test.skip(!cloud,'Explicit cloud capacity verification only.');
 await cognitoLogin(page,'reviewer');
 const identity=await (await page.request.get('/api/v1/session')).json();
 const headers={Origin:'https://shiftclarity.pages.dev','X-CSRF-Token':identity.csrf,'X-Data-Classification':'synthetic'};
 const started=Date.now(),prefix='CAP'+Date.now();
 const created=await page.request.post('/api/v1/import-workbench/sessions',{headers:{...headers,'Idempotency-Key':crypto.randomUUID()},data:{facility_id:'FAC-A',service_from:'2026-10-23',service_to:'2026-10-25',source_as_of:'2026-10-28T17:00:00Z',billing_cutoff:'2026-10-27T12:00:00Z',invoice_complete:true,work_complete:true,use_registered_rates:true,expected_work_hours:'8000',expected_invoice_total:'480000.00',synthetic:true}});
 expect(created.ok()).toBe(true);
 const session=(await created.json()).id,base='/api/v1/import-workbench/sessions/'+session;
 const work=['Shift ID,Facility,Worker ID,Role,Pay Type,Shift Date,Hours,Approval Status,Approved Date'];
 const invoices=['Line ID,Invoice Number,Facility,Shift ID,Amount,Hours,Bill Rate,Status,Document Type'];
 for(let i=0;i<1000;i++){
  const id=prefix+'W'+i;work.push(`${id},FAC-A,${prefix}E${i},RN,Regular,2026-10-24,8,Approved,2026-10-25`);
  for(const part of [1,2])invoices.push(`${prefix}L${i}_${part},${prefix}INV,FAC-A,${id},240.00,4,60.00,Posted,Statement`);
 }
 for(const [category,lines] of [['work',work],['invoices',invoices]] as const){
  const upload=await page.request.post(base+'/files?category='+category+'&filename=capacity-'+category+'.csv',{headers:{...headers,'Content-Type':'application/octet-stream','Idempotency-Key':crypto.randomUUID()},data:Buffer.from(lines.join('\r\n')+'\r\n')});
  expect(upload.ok()).toBe(true);
  const id=(await upload.json()).id,state=await (await page.request.get(base)).json(),file=state.files.find((f:{id:string})=>f.id===id),table=file.table;
  const mapping=await page.request.post(base+'/files/'+id+'/mapping',{headers:{...headers,'Idempotency-Key':crypto.randomUUID()},data:{expected_version:state.version,worksheet:table.worksheet,header_row:table.header_row,mapping:table.mapping,constants:{},value_maps:table.value_maps,date_format:'ISO',decimal_format:'dot',time_unit:'hours',end_date_mode:'exclusive',confirmed:true}});
  expect(mapping.ok()).toBe(true);expect((await mapping.json()).errors).toEqual([]);
 }
 let state=await (await page.request.get(base)).json();
 const validation=await page.request.post(base+'/validate',{headers,data:{expected_version:state.version}});expect(validation.ok()).toBe(true);expect((await validation.json()).valid).toBe(true);
 state=await (await page.request.get(base)).json();expect(state.status).toBe('approved');
 const acceptStart=Date.now();
 const accepted=await page.request.post(base+'/accept',{headers,data:{expected_version:state.version,confirmed:true,acknowledge_warnings:true}});
 const acceptMs=Date.now()-acceptStart;expect(accepted.ok()).toBe(true);
 const queued=await page.request.post('/api/v1/runs',{headers:{...headers,'Idempotency-Key':crypto.randomUUID()},data:{import_id:(await accepted.json()).id}});expect(queued.ok()).toBe(true);
 const run=(await queued.json()).id;
 await expect.poll(async()=>(await (await page.request.get('/api/v1/jobs/'+run)).json()).status,{timeout:60000,intervals:[500,1000,2000]}).toBe('completed');
 const result=await page.request.get('/api/v1/workspace?run_id='+run);expect(result.ok()).toBe(true);
 const data=await result.json();expect(data.state.run.coverage.evaluated_records).toBe(1000);expect(data.state.run.totals.underbilling).toBe('40000.00');
 const reportTimes:Record<string,number>={};
 for(const format of ['xlsx','pdf']){const time=Date.now();const report=await page.request.get('/api/v1/runs/'+run+'/report.'+format);expect(report.ok()).toBe(true);reportTimes[format]=Date.now()-time;expect((await report.body()).length).toBeGreaterThan(10000);}
 await writeFile('artifacts/workflow-live-capacity.json',JSON.stringify({synthetic:true,work:1000,invoice_lines:2000,accept_ms:acceptMs,total_ms:Date.now()-started,workspace_bytes:(await result.body()).length,report_ms:reportTimes,run_id:run},null,2));
});
