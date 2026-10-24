import {test,expect,type Page} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {readFileSync} from 'node:fs';
import {cognitoLogin} from '../pilot/cognito-auth';

const cloud=process.env.SHIFTCLARITY_MVP_AWS_QA==='1';
async function rendered(page:Page){
 await page.evaluate(()=>document.fonts.ready);
 await expect.poll(()=>page.locator('img:visible').evaluateAll(images=>images.every(image=>(image as HTMLImageElement).complete&&(image as HTMLImageElement).naturalWidth>0))).toBe(true);
}

test('nontechnical evaluator imports XLSX, confirms mappings, obtains independent approval and reviews the real result',async({browser})=>{
 const sessions=cloud?null:JSON.parse(readFileSync('.local/mvp-browser-sessions.json','utf8'));
 const profileName=cloud?'Live work export '+Date.now():'Monthly work export';
 const evaluator=await browser.newContext(),approver=await browser.newContext();
 try{
  if(!cloud)for(const [context,actor] of [[evaluator,'MVP-IMPORTER'],[approver,'MVP-APPROVER']] as const)await context.addCookies([{name:'sc_session',value:sessions[actor].token,url:'http://127.0.0.1:5196'}]);
  const page=await evaluator.newPage(),other=await approver.newPage();
  if(cloud){await cognitoLogin(page,'reviewer');await cognitoLogin(other,'approver');}
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto('/pilot/?view=import');
  await expect(page.getByRole('heading',{name:'Start a billing review'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Create review',exact:true})).toBeVisible();
  await rendered(page);
  await page.screenshot({path:'artifacts/mvp-onboarding.png'});
  await page.getByLabel('These work records cover the whole').check();
  await page.getByLabel('These invoice/statement records include').check();
  await page.getByLabel('I will use fictional').check();
  await page.getByRole('button',{name:'Create review',exact:true}).click();
  await expect(page).toHaveURL(/session=SES-/);
  const sessionURL=page.url();
  for(const [kind,label] of [['rates','Contract rates'],['work','Approved work'],['invoices','Invoices & statements']]){
   await page.getByLabel('Upload '+label,{exact:true}).setInputFiles('public/examples/spreadsheets/'+kind+'.xlsx');
   await expect(page.getByRole('heading',{name:kind+'.xlsx',exact:true})).toBeVisible();
  }
  await rendered(page);
  await page.screenshot({path:'artifacts/mvp-upload.png',fullPage:true});
  await page.locator('.mapping-card').first().evaluate(node=>node.scrollIntoView({block:'start'}));
  await page.screenshot({path:'artifacts/mvp-mapping.png'});
  for(const theme of ['dark','light']){
   await page.getByRole('button',{name:theme==='dark'?'Use dark mode':'Use light mode',exact:true}).click();
   expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
  }
  for(const kind of ['rates','work','invoices']){
   const card=page.locator('.mapping-card').filter({has:page.getByRole('heading',{name:kind+'.xlsx',exact:true})});
   await card.getByLabel('I checked the columns').check();
   await card.getByRole('button',{name:'Confirm mapping for '+kind+'.xlsx',exact:true}).click();
   await expect(card.getByText('Review or change the confirmed mapping',{exact:true})).toBeVisible();
  }
  const workCard=page.locator('.mapping-card').filter({has:page.getByRole('heading',{name:'work.xlsx',exact:true})});
  await workCard.getByLabel('Save verified mapping as').fill(profileName);
  await workCard.getByRole('button',{name:'Save mapping profile'}).click();
  await expect(workCard.getByLabel('Profile for work.xlsx')).toContainText(profileName);
  await workCard.getByText('Review or change the confirmed mapping',{exact:true}).click();
  await workCard.getByRole('combobox',{name:'Date convention',exact:true}).selectOption('MDY');
  await expect(page.getByRole('button',{name:'Validate all sources',exact:true})).toBeDisabled();
  await expect(workCard.getByRole('button',{name:'Save mapping profile'})).toBeDisabled();
  await workCard.getByRole('combobox',{name:'Date convention',exact:true}).selectOption('ISO');
  await workCard.getByLabel('I checked the columns').check();
  await workCard.getByRole('button',{name:'Confirm mapping for work.xlsx',exact:true}).click();
  const validated=page.waitForResponse(response=>response.url().endsWith('/validate')&&response.request().method()==='POST');
  await page.getByRole('button',{name:'Validate all sources',exact:true}).click();
  expect((await validated).ok()).toBe(true);
  await expect(page.getByText('Checking all sources and rate versions…',{exact:true})).toHaveCount(0);
  const newRates=page.getByRole('heading',{name:'Review the new contract rate versions'});
  if(!cloud||await newRates.isVisible()){
   await expect(newRates).toBeVisible();
   await expect(page.getByRole('button',{name:'Approve these rate versions'})).toHaveCount(0);
   await other.goto(sessionURL);
   const approverActor=(await (await other.request.get('/api/v1/session')).json()).actor;
   await other.getByLabel('Independent rate review reason').fill('Inspected the fictional source file, hourly rates and historical authorization dates.');
   await other.getByLabel('I inspected the rates').check();
   await other.getByRole('button',{name:'Approve these rate versions'}).click();
   await expect(other.getByText('Approved by '+approverActor+' at',{exact:false})).toBeVisible();
   await page.getByRole('button',{name:'Refresh status'}).click();
  }
  await page.getByLabel('I confirm the mappings, source totals').check();
  await page.getByRole('button',{name:'Accept sources',exact:true}).click();
  await page.getByRole('button',{name:'Run billing review',exact:true}).click();
  await expect(page).toHaveURL(/view=workspace(?:&|$)/);
  await expect(page.getByRole('heading',{name:'+$200.00',exact:true})).toBeVisible();
  await expect(page.locator('.mvp-summary')).toContainText('6 / 8');
  const firstRun=new URL(page.url()).searchParams.get('run')!;
  if(cloud)await page.getByRole('button',{name:/^All findings/}).click();
  await page.getByRole('link',{name:'Rate change not reflected',exact:true}).click();
  if(cloud&&await page.getByRole('button',{name:'Reopen for review'}).isVisible()){
   await page.getByRole('button',{name:'Reopen for review'}).click();
   await page.getByLabel('Review reason',{exact:true}).fill('Repeat verification of the same fictional billing period.');
   await page.getByRole('button',{name:'Save review',exact:true}).click();
   await page.getByRole('link',{name:'Rate change not reflected',exact:true}).click();
  }
  await page.getByRole('button',{name:'Confirm discrepancy',exact:true}).click();
  await page.getByLabel('Review reason',{exact:true}).fill('Fictional rate and posted invoice evidence checked.');
  await page.getByRole('button',{name:'Save review',exact:true}).click();
  await expect(page.getByRole('row',{name:/Rate change not reflected/})).toContainText('Confirmed discrepancy');
  if(cloud){
   await page.reload();
   await expect(page.getByRole('row',{name:/Rate change not reflected/})).toContainText('Confirmed discrepancy');
   const source=await (await page.request.get('/api/v1/import-workbench/sessions/'+new URL(sessionURL).searchParams.get('session'))).json();
   const denied=await page.request.post('/api/v1/import-workbench/sessions',{data:source.period,headers:{Origin:new URL(sessionURL).origin}});
   expect(denied.status()).toBe(403);
   const original=await page.request.get('/api/v1/import-workbench/sessions/'+source.id+'/files/'+source.files[0].id+'/source');
   expect(original.ok()).toBe(true);
   expect(await original.body()).toEqual(readFileSync('public/examples/spreadsheets/rates.xlsx'));
   expect(original.headers()['cache-control']).toContain('no-store');
   const workFile=source.files.find((file:{category:string})=>file.category==='work');
   expect((await other.request.get('/api/v1/import-workbench/sessions/'+source.id+'/files/'+workFile.id+'/source')).status()).toBe(403);
   const identity=(await (await other.request.get('/api/v1/session')).json());
   const roleDenied=await other.request.post('/api/v1/import-workbench/sessions',{data:source.period,headers:{Origin:new URL(sessionURL).origin,'X-CSRF-Token':identity.csrf,'Idempotency-Key':'denied-live-import-'+Date.now()}});
   expect(roleDenied.status()).toBe(403);
  }
  await page.getByRole('button',{name:'Download report',exact:true}).click();
  for(const [label,extension] of [['Download Excel','xlsx'],['Download PDF','pdf']]){
   const pending=page.waitForEvent('download');await page.getByRole('button',{name:label,exact:true}).click();
   const download=await pending;expect(await download.failure()).toBeNull();
   await download.saveAs('artifacts/reports/'+(cloud?'live-':'')+'browser-billing-review.'+extension);
  }
  await page.getByRole('dialog',{name:'Download billing review'}).getByRole('button',{name:'Cancel',exact:true}).click();
  await page.getByRole('button',{name:'Use dark mode',exact:true}).click();
  expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
  await page.getByRole('button',{name:'Use light mode',exact:true}).click();
  await expect(page.locator('.toast')).toBeHidden({timeout:7000});
  await page.getByRole('heading',{name:'+$200.00',exact:true}).focus();
  await page.evaluate(()=>window.scrollTo(0,0));
  await rendered(page);
  await page.screenshot({path:'artifacts/mvp-workspace.png',fullPage:true});
  await page.goto(sessionURL);
  await expect(page.getByRole('heading',{name:'rates.xlsx',exact:true})).toBeVisible();
  for(const width of [1440,390,320]){
   await page.setViewportSize({width,height:1000});
   await rendered(page);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBe(width);
   expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
   if(width===390)await page.screenshot({path:'artifacts/mvp-import-mobile.png'});
  }
  // Reuse the verified XLSX-header profile for a CSV export in another billing period.
  await page.setViewportSize({width:1440,height:1000});
  await page.goto('/pilot/?view=import');
  await page.getByLabel('Period starts',{exact:true}).fill('2026-10-11');
  await page.getByLabel('Period ends (inclusive)',{exact:true}).fill('2026-10-20');
  await page.getByLabel('Files current through (UTC)',{exact:true}).fill('2026-10-22T17:00');
  await page.getByLabel('Billing cutoff (UTC)',{exact:true}).fill('2026-10-22T12:00');
  await page.getByLabel('These work records cover the whole').check();
  await page.getByLabel('These invoice/statement records include').check();
  await page.getByLabel('I will use fictional').check();
  await page.getByRole('button',{name:'Create review',exact:true}).click();
  await expect(page).toHaveURL(/session=SES-/);
  const nextPeriodURL=page.url();expect(nextPeriodURL).not.toBe(sessionURL);
  for(const [kind,label] of [['rates','Contract rates'],['work','Approved work'],['invoices','Invoices & statements']]){
   const content=readFileSync('public/examples/spreadsheets/'+(kind==='rates'?'rates':'period-2-'+kind)+'.csv','utf8');
   await page.getByLabel('Upload '+label,{exact:true}).setInputFiles({name:kind+'.csv',mimeType:'text/csv',buffer:Buffer.from(content)});
   const card=page.locator('.mapping-card').filter({has:page.getByRole('heading',{name:kind+'.csv',exact:true})});
   if(kind==='work'){
    const profile=card.getByLabel('Profile for work.csv');
    await profile.selectOption({label:profileName+' · v1'});
    await expect(card.getByRole('combobox',{name:'Worksheet',exact:true})).toHaveValue('CSV');
    await expect(card.getByLabel('Map RG for component',{exact:true})).toHaveValue('');
    await card.getByLabel('Map RG for component',{exact:true}).selectOption('standard');
   }
   await card.getByLabel('I checked the columns').check();
   await card.getByRole('button',{name:'Confirm mapping for '+kind+'.csv',exact:true}).click();
  }
  await page.getByRole('button',{name:'Validate all sources',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Review the new contract rate versions'})).toHaveCount(0);
  await page.getByLabel('I confirm the mappings, source totals').check();
  await page.getByRole('button',{name:'Accept sources',exact:true}).click();
  await page.getByRole('button',{name:'Run billing review',exact:true}).click();
  await expect(page).toHaveURL(/view=workspace(?:&|$)/);
  await expect(page.getByRole('row',{name:/Rate change not reflected/})).toContainText('Needs review');
  await expect(page.locator('.mvp-summary')).toContainText('0 / 1');
  const secondRun=new URL(page.url()).searchParams.get('run')!;expect(secondRun).not.toBe(firstRun);
  await page.getByRole('link',{name:'Rate change not reflected',exact:true}).click();
  const followup=page.getByRole('region',{name:'Case follow-up'});
  await expect(followup).toBeVisible();
  await expect(followup.getByRole('combobox',{name:'Case owner',exact:true})).toBeVisible();
  await followup.getByRole('combobox',{name:'Case owner',exact:true}).selectOption(cloud?'DEMO-APPROVER':'MVP-APPROVER');
  await followup.getByLabel('Follow-up reason',{exact:true}).fill('Independent billing colleague owns the next follow-up.');
  await followup.getByRole('button',{name:'Save follow-up',exact:true}).click();
  await expect(followup.getByRole('status')).toContainText('saved');
  await expect(page.locator('.review-panel')).toContainText(cloud?'Dana Reyes':'MVP-APPROVER');
  await page.getByRole('link',{name:'Follow-up queue',exact:true}).click();
  await page.getByRole('combobox',{name:'Show',exact:true}).selectOption('team');
  await expect(page.locator('.workflow-list')).toContainText(cloud?'Dana Reyes':'MVP-APPROVER');
  await page.getByRole('link',{name:'Period history',exact:true}).click();
  const firstPeriod=page.locator('.workflow-list>li').filter({hasText:firstRun});
  await firstPeriod.getByRole('button',{name:'Open review'}).click();
  await expect(page).toHaveURL(new RegExp('run='+firstRun));
  await page.getByRole('button',{name:/^All findings/}).click();
  await expect(page.getByRole('row',{name:/Rate change not reflected/})).toContainText('Confirmed discrepancy');
  expect((await page.request.get('/api/v1/runs/'+firstRun+'/report.xlsx')).ok()).toBe(true);
  expect((await page.request.get('/api/v1/runs/'+firstRun+'/report.pdf')).ok()).toBe(true);
  // Another reviewer opens the newer run without changing the first browser's period.
  await other.goto('/pilot/?view=workspace&run='+secondRun);
  await expect(other.getByRole('heading',{name:'+$200.00',exact:true})).toBeVisible();
  await page.reload();await page.getByRole('button',{name:/^All findings/}).click();
  await expect(page).toHaveURL(new RegExp('run='+firstRun));
  await expect(page.getByRole('row',{name:/Rate change not reflected/})).toContainText('Confirmed discrepancy');
  await page.goto('/pilot/?view=followup');
  for(const width of [1440,390,320]){
   await page.setViewportSize({width,height:1000});
   await page.getByRole('combobox',{name:'Show',exact:true}).selectOption('team');
   await expect(page.locator('.workflow-list>li').first()).toBeVisible();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBe(width);
   expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
   await page.screenshot({path:'artifacts/workflow-queue-'+width+'.png',fullPage:true});
  }
  if(!cloud){
   await page.goto('/pilot/?view=setup');
   await expect(page.getByRole('heading',{name:'Workspace & team',exact:true})).toBeVisible();
   await page.getByLabel('Workspace name',{exact:true}).fill('Fictional Agency QA');
   await page.getByRole('button',{name:'Save defaults',exact:true}).click();
   await expect(page.getByRole('status')).toContainText('saved');
   expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBe(320);
   await page.screenshot({path:'artifacts/workflow-setup-mobile.png',fullPage:true});
  }
  // Close the loop: record an actual correction reference, reuse registered rates, rerun, and inspect the retained case.
  await page.setViewportSize({width:1440,height:1000});
  await page.goto('/pilot/?view=evidence&id=FND-001&run='+firstRun);
  const correction=page.getByRole('region',{name:'Case follow-up'});
  await correction.getByRole('combobox',{name:'Next action',exact:true}).selectOption('record_correction');
  await correction.getByLabel('Corrected invoice reference',{exact:true}).fill('INV-CORRECTED-QA');
  await correction.getByLabel('Follow-up reason',{exact:true}).fill('Corrected the fictional original invoice in the source billing system.');
  await correction.getByRole('button',{name:'Save follow-up',exact:true}).click();
  await expect(correction.getByRole('status')).toContainText('saved');
  await page.goto('/pilot/?view=import');
  await page.getByLabel('Reuse registered approved rates').check();
  await page.getByLabel('These work records cover the whole').check();
  await page.getByLabel('These invoice/statement records include').check();
  await page.getByLabel('I will use fictional').check();
  await page.getByRole('button',{name:'Create review',exact:true}).click();
  await expect(page).toHaveURL(/session=SES-/);
  await expect(page.getByLabel('Upload Contract rates',{exact:true})).toHaveCount(0);
  for(const [kind,label] of [['work','Approved work'],['invoices','Invoices & statements']]){
   let content=readFileSync('public/examples/spreadsheets/'+kind+'.csv','utf8');
   if(kind==='invoices')content=content.replaceAll(',600,10,60,',',650,10,65,');
   await page.getByLabel('Upload '+label,{exact:true}).setInputFiles({name:kind+'-corrected.csv',mimeType:'text/csv',buffer:Buffer.from(content)});
   const card=page.locator('.mapping-card').filter({has:page.getByRole('heading',{name:kind+'-corrected.csv',exact:true})});
   await card.getByLabel('I checked the columns').check();
   await card.getByRole('button',{name:'Confirm mapping for '+kind+'-corrected.csv',exact:true}).click();
  }
  await page.getByRole('button',{name:'Validate all sources',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Review the new contract rate versions'})).toHaveCount(0);
  await page.getByLabel('I confirm the mappings, source totals').check();
  await page.getByRole('button',{name:'Accept sources',exact:true}).click();
  await page.getByRole('button',{name:'Run billing review',exact:true}).click();
  await expect(page.getByRole('heading',{name:'+$0.00',exact:true})).toBeVisible();
  await expect(page.locator('.mvp-summary')).toContainText('6 / 8');
  await page.getByRole('link',{name:'Follow-up queue',exact:true}).click();
  await page.getByRole('combobox',{name:'Show',exact:true}).selectOption('team');
  await page.getByRole('combobox',{name:'Status',exact:true}).selectOption('resolved');
  const resolved=page.locator('.workflow-list>li').filter({hasText:'FAC-A'}).filter({hasText:'Oct 1–10, 2026'});
  await expect(resolved).toContainText('Aligned / evidence supplied');
  await resolved.getByRole('button',{name:'Follow up',exact:true}).click();
  await expect(page.getByRole('region',{name:'Case follow-up'})).toContainText('INV-CORRECTED-QA');
  await page.getByRole('region',{name:'Case follow-up'}).getByText(/Follow-up history/).click();
  await expect(page.getByRole('region',{name:'Case follow-up'})).toContainText('aligned on rerun');
  await page.screenshot({path:'artifacts/workflow-resolved-case.png',fullPage:true});
  for(const width of [1440,390,320]){
   await page.setViewportSize({width,height:1000});
   for(const theme of ['dark','light']){
    await page.getByRole('button',{name:theme==='dark'?'Use dark mode':'Use light mode',exact:true}).click();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBe(width);
    expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
    if(width===390)await page.screenshot({path:'artifacts/workflow-case-mobile-'+theme+'.png',fullPage:true});
   }
  }
  if(cloud){
   await cognitoLogin(page,'reviewer','/pilot/?view=history&run='+firstRun);
   await expect(page.getByRole('heading',{name:'Period history',exact:true})).toBeVisible();
   expect(new URL(page.url()).searchParams.get('run')).toBe(firstRun);
  }
  expect(errors).toEqual([]);
 }finally{await evaluator.close();await approver.close();}
});
