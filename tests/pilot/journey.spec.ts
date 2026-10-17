import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {readFile} from 'node:fs/promises';
import {login} from './auth';
test.describe.configure({mode:'serial'});

test('actual identity provider requires authenticator and persists a decision after reload',async({page})=>{
 await login(page,'reviewer');
 await expect(page.getByRole('heading',{name:'Potential underbilling',exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Reset demo'})).toHaveCount(0);
 const before=await (await page.request.get('/api/v1/workspace')).json(),finding=before.state.run.findings.find((f:any)=>f.id==='FND-002');
 expect(finding).toBeTruthy();
 const prior=Object.values(before.state.reviews).find((review:any)=>review.fingerprint===finding.fingerprint) as {state:string}|undefined;
 await page.goto('/pilot/?view=evidence&id=FND-002');
 await page.locator('#main h1').waitFor();
 if(prior?.state==='needs_review'||!prior){
  await page.getByRole('button',{name:'Confirm discrepancy',exact:true}).click();
  await page.getByLabel('Review reason').fill('Approved work and posted invoice checked against the fictional agreement.');
  await page.getByRole('button',{name:'Save review',exact:true}).click();
  await expect(page.locator('.toast[role="status"]')).toContainText('saved on the server');
 }else if(prior.state!=='confirmed'){
  await page.getByRole('button',{name:'Reopen for review'}).click();
  await page.getByLabel('Review reason').fill('Reopened this fictional finding for a repeat verification.');
  await page.getByRole('button',{name:'Save review',exact:true}).click();
  await expect(page.locator('.toast[role="status"]')).toContainText('saved on the server');
  await page.getByRole('button',{name:'Confirm discrepancy',exact:true}).click();
  await page.getByLabel('Review reason').fill('Approved work and posted invoice checked against the fictional agreement.');
  await page.getByRole('button',{name:'Save review',exact:true}).click();
  await expect(page.locator('.toast[role="status"]')).toContainText('saved on the server');
 }
 await page.reload();
 await expect(page.getByRole('button',{name:'Reopen for review'})).toBeVisible();
 await expect(page.locator('.history .event').filter({hasText:'Jordan Kim, Reviewer'}).last()).toBeVisible();
 const after=await (await page.request.get('/api/v1/workspace')).json(),persisted=Object.values(after.state.reviews).find((review:any)=>review.fingerprint===finding.fingerprint) as {state:string}|undefined;
 expect(persisted?.state).toBe('confirmed');
});

test('real upload produces a durable run and private source with no demo controls',async({page})=>{
 await login(page,'reviewer');
 const apiTrail:string[]=[];
 page.on('response',async response=>{const path=new URL(response.url()).pathname;if(/^\/api\/v1\/(imports|runs|jobs\/)/.test(path)){const body=await response.json().catch(()=>({}));apiTrail.push(`${path} ${response.status()} ${body.status||body.help||''}`);}});
 page.on('requestfailed',request=>{const path=new URL(request.url()).pathname;if(/^\/api\/v1\/(imports|runs|jobs\/)/.test(path))apiTrail.push(`${path} failed: ${request.failure()?.errorText||'unknown'}`);});
 await page.goto('/pilot/?view=inputs');
 await expect(page.getByText('Demo scenarios',{exact:true})).toHaveCount(0);
 await expect(page.getByText('Try your own records',{exact:false})).toHaveCount(0);
 await page.getByRole('button',{name:'Import synthetic snapshot',exact:true}).click();
 await page.getByLabel('Synthetic snapshot bundle').setInputFiles('examples/synthetic-healthcare-staffing/bundle.json');
 try{await expect(page.locator('.toast[role="status"]')).toContainText('Validated snapshot published',{timeout:45000});}catch(error){throw new Error(`${String(error)}\nAPI journey: ${apiTrail.join(' → ')||'(no import/run/job request observed)'}`);}
 await expect(page.getByText('Server import history',{exact:true})).toBeVisible();
 const response=await page.request.get('/api/v1/workspace');
 const saved=await response.json();
 expect(saved.state.run.id).toMatch(/^RUN-[a-f0-9]{32}$/);
 expect(saved.state.run.totals.underbilling).toBe('1760.00');
 await page.reload();
 await expect(page.getByText(saved.state.run.id,{exact:false}).first()).toBeVisible();
 const download=await page.getByText('Download private source').first().getAttribute('href');
 expect((await page.request.get(download!)).status()).toBe(200);
});

test('authenticated read-only account cannot review or import',async({page})=>{
 await login(page,'observer');
 await page.goto('/pilot/?view=evidence&id=FND-001');
 await expect(page.getByRole('button',{name:'Reopen for review'})).toBeDisabled();
 await page.goto('/pilot/?view=inputs');
 await expect(page.getByRole('button',{name:'Import synthetic snapshot',exact:true})).toBeDisabled();
 expect((await page.request.get('/api/v1/template')).status()).toBe(403);
});

test('rejected upload explains the field limit, retains the run and disables stale decisions',async({page})=>{
 await login(page,'reviewer');
 const before=await (await page.request.get('/api/v1/workspace')).json();
 const bundle=JSON.parse(await readFile('examples/synthetic-healthcare-staffing/bundle.json','utf8'));
 bundle.work[0].patient_name='SENSITIVE-CANARY';
 await page.goto('/pilot/?view=inputs');
 await page.getByRole('button',{name:'Import synthetic snapshot',exact:true}).click();
 await page.getByLabel('Synthetic snapshot bundle').setInputFiles({name:'rejected.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bundle))});
 await expect(page.getByRole('dialog')).toContainText('Remove fields outside the template');
 await expect(page.getByRole('dialog')).not.toContainText('SENSITIVE-CANARY');
 await page.getByRole('button',{name:'Cancel',exact:true}).click();
 await page.goto('/pilot/?view=evidence&id=FND-001');
 await expect(page.getByRole('button',{name:'Reopen for review'})).toBeDisabled();
 const after=await (await page.request.get('/api/v1/workspace')).json();
 expect(after.state.run).toEqual(before.state.run);
 await page.goto('/pilot/?view=inputs');
 await page.getByRole('button',{name:'Import synthetic snapshot',exact:true}).click();
 await page.getByLabel('Synthetic snapshot bundle').setInputFiles('examples/synthetic-healthcare-staffing/bundle.json');
 await expect(page.locator('.toast[role="status"]')).toContainText('Validated snapshot published',{timeout:40000});
});

test('author and separate approver use distinct MFA accounts without role simulation',async({page})=>{
 await login(page,'author');
 await page.goto('/pilot/?view=rules');
 await expect(page.getByText('DEMO role simulation',{exact:false})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Approve rule',exact:false})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Sign out',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Sign out',exact:true}).first().click();
 if(process.env.SHIFTCLARITY_AWS_QA!=='1')await page.getByRole('button',{name:'Logout',exact:true}).click();
 await page.waitForURL('**/pilot/');
 await expect(page.getByRole('link',{name:'Sign in to your workspace',exact:true})).toBeVisible();
 await login(page,'approver');
 await page.goto('/pilot/?view=rules');
 await page.getByLabel('I inspected the source, effective date and supersession.').check();
 await page.getByRole('button',{name:'Approve rule',exact:false}).click();
 await expect(page.getByText('Approved new version',{exact:true})).toBeVisible();
 await page.reload();
 await expect(page.getByText('Approved new version',{exact:true})).toBeVisible();
});

test('unassigned organization is denied after verified MFA',async({page})=>{
 await login(page,'outsider');
 await expect(page.locator('body')).toContainText('no workspace membership');
});

test('author registers fictional evidence and proposes a new version for a separate account',async({page})=>{
 await login(page,'author');
 await page.goto('/pilot/?view=inputs');
 const workspace=await (await page.request.get('/api/v1/workspace')).json();
 const predecessor=workspace.state.draft;
 const effective=new Date(`${predecessor.effective_from}T00:00:00.000Z`);
 effective.setUTCDate(effective.getUTCDate()+1);
 const effectiveDate=effective.toISOString().slice(0,10);
 const effectiveLabel=new Date(`${effectiveDate}T00:00:00.000Z`).toLocaleDateString('en-US',{timeZone:'UTC',month:'long',day:'numeric',year:'numeric'});
 await page.getByLabel('Source title').fill('Fictional next amendment');
 await page.getByLabel('Fictional agreement text').fill(`Standard RN rate USD 70.00 per hour from ${effectiveLabel}. Replaces the selected synthetic predecessor.`);
 await page.getByRole('button',{name:'Save synthetic source'}).click();
 await expect(page.locator('.rule-authoring')).toContainText('Synthetic source registered');
 await page.getByLabel('Approved predecessor').selectOption(predecessor.id);
 await page.getByLabel('Source excerpt',{exact:true}).selectOption({label:'Fictional next amendment'});
 await page.getByLabel('Hourly rate · USD',{exact:true}).fill('70.00');
 await page.getByLabel('Effective service date').fill(effectiveDate);
 await page.getByRole('button',{name:'Submit for independent approval'}).click();
 await expect(page.locator('.rule-authoring')).toContainText('Draft saved');
 await page.reload();
 await expect(page.getByRole('button',{name:'Submit for independent approval'})).toBeDisabled();
 expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'artifacts/'+(process.env.SHIFTCLARITY_AWS_QA==='1'?'aws':'pilot')+'-screenshots/authoring-390.png',fullPage:true});
});

test('secure routes remain accessible and fit desktop/mobile',async({page})=>{
 const errors:string[]=[];
 page.on('pageerror',error=>errors.push(error.message));
 await login(page,'reviewer');
 for(const width of [1440,1280,1024,390,320]){
  await page.setViewportSize({width,height:width===1440?1000:width>=1024?900:844});
  for(const view of ['workspace','evidence','inputs','rules','coverage']){
   await page.goto('/pilot/?view='+view);
   await page.locator('#main h1').waitFor();
   if(view==='inputs')await expect(page.locator('.pilot-details')).toHaveAttribute('aria-busy','false');
   await page.evaluate(()=>document.fonts.ready);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}px ${view} exceeds the viewport`).toBe(true);
   if(width===1440)expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
   await page.screenshot({path:'artifacts/'+(process.env.SHIFTCLARITY_AWS_QA==='1'?'aws':'pilot')+'-screenshots/'+view+'-'+width+'.png',fullPage:true});
  }
 }
 expect(errors).toEqual([]);
});
