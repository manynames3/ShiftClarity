import {test,expect,type Page} from '@playwright/test';
import {randomBytes} from 'node:crypto';
import {writeFile} from 'node:fs/promises';
import {cognitoLogin} from '../pilot/cognito-auth';
import {totp} from '../totp';
const cloud=process.env.SHIFTCLARITY_OWNER_AWS_QA==='1';

test('owner provisions private access, Cognito enforces password change and MFA, and revocation blocks the member',async({browser})=>{
 test.skip(!cloud,'Explicitly authorized Cognito verification only; local tests cover the service boundary.');
 const ownerContext=await browser.newContext(),memberContext=await browser.newContext();
 const username='qa-workflow-'+Date.now();
 let secret='',lastCounter=0;
 const privateFile='.local/workflow-invite-qa.json';
 async function code(page:Page){
  const counter=Math.floor(Date.now()/30000);
  if(counter<=lastCounter)await page.waitForTimeout((lastCounter+1)*30000-Date.now()+300);
  lastCounter=Math.floor(Date.now()/30000);return totp(secret);
 }
 async function firstLogin(page:Page,temporary:string){
  const password='Aa1!'+randomBytes(24).toString('base64url');
  await writeFile(privateFile,JSON.stringify({username,password,temporary,totp:secret}),{mode:0o600});
  await page.goto('/auth/login');
  await page.locator('input[name=username]:visible').fill(username);
  await page.locator('input[name=password]:visible').fill(temporary);
  await page.locator('input[name=signInSubmitButton]:visible').click();
  const passwords=page.locator('input[type=password]:visible');
  await expect(passwords).toHaveCount(2);
  await passwords.nth(0).fill(password);await passwords.nth(1).fill(password);
  const submit=page.locator('input[type=submit]:visible,button[type=submit]:visible');
  await expect(submit).toHaveCount(1);
  await submit.click();
  await page.locator('input[name=userCode],input[name=authentication_code]').waitFor();
  if(await page.locator('input[name=userCode]').isVisible()){
   await page.getByText('Show secret key',{exact:true}).click();
   secret=(await page.locator('body').innerText()).match(/[A-Z2-7]{32,}/)?.[0]||'';
   expect(!!secret).toBe(true);
   await writeFile(privateFile,JSON.stringify({username,password,totp:secret}),{mode:0o600});
   await page.locator('input[name=userCode]').fill(await code(page));
   await page.locator('input[name=friendlyDeviceName]').fill('ShiftClarity isolated onboarding verification');
  }else{
   expect(!!secret).toBe(true);await page.locator('input[name=authentication_code]').fill(await code(page));
  }
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await page.waitForURL(url=>url.pathname==='/pilot/');
  await expect(page.getByRole('link',{name:'Follow-up queue',exact:true})).toBeVisible();
 }
 try{
  const owner=await ownerContext.newPage(),member=await memberContext.newPage();
  await cognitoLogin(owner,'reviewer');await owner.goto('/pilot/?view=setup');
  await expect(owner.getByRole('heading',{name:'Workspace & team',exact:true})).toBeVisible();
  await owner.getByLabel('New username',{exact:true}).fill(username);
  await owner.getByRole('checkbox',{name:'Upload exports',exact:true}).uncheck();
  const create=owner.waitForResponse(r=>r.url().endsWith('/api/v1/team')&&r.request().method()==='POST');
  await owner.getByRole('button',{name:'Create private account',exact:true}).click();
  const response=await create;expect(response.ok()).toBe(true);
  const created=await response.json();expect(!!created.temporary_password).toBe(true);
  await expect(owner.getByRole('button',{name:'Hide access details',exact:true})).toBeVisible();
  expect((await owner.locator('.workflow-secret').textContent())===created.temporary_password).toBe(true);
  await owner.getByRole('button',{name:'Hide access details',exact:true}).click();
  await firstLogin(member,created.temporary_password);
  expect((await (await member.request.get('/api/v1/session')).json()).roles).toEqual(['reviewer']);
  expect((await member.request.get('/api/v1/team')).status()).toBe(403);
  const row=owner.locator('.workflow-member').filter({hasText:username});
  await row.locator('summary').click();
  await row.getByRole('button',{name:'Reset password…',exact:true}).click();
  const reset=owner.waitForResponse(r=>r.url().includes('/reset')&&r.request().method()==='POST');
  await row.getByRole('button',{name:'Issue temporary password',exact:true}).click();
  const resetResponse=await reset;
  if(!resetResponse.ok())await writeFile('.local/workflow-owner-reset-response.json',JSON.stringify({status:resetResponse.status(),detail:await resetResponse.json()}),{mode:0o600});
  expect(resetResponse.ok()).toBe(true);
  const renewed=await resetResponse.json();
  await owner.getByRole('button',{name:'Hide access details',exact:true}).click();
  expect((await member.request.get('/api/v1/session')).status()).toBe(401);
  await firstLogin(member,renewed.temporary_password);
  // Refreshing remounts the versioned access editor after the reset.
  await owner.reload();const latest=owner.locator('.workflow-member').filter({hasText:username});
  await latest.locator('summary').click();
  await latest.getByLabel('Allow workspace access',{exact:true}).uncheck();
  await latest.getByRole('button',{name:'Save access',exact:true}).click();
  await expect(owner.getByRole('status')).toContainText('saved');
  expect((await member.request.get('/api/v1/workspace')).status()).toBe(401);
  await expect(owner.locator('.workflow-member').filter({hasText:username}).locator('summary')).toContainText('Access revoked');
  await writeFile('artifacts/workflow-live-onboarding.json',JSON.stringify({private_account_created:true,invitation_delivery:'suppressed; no email/phone attribute',password_change_required:true,totp_enrolled:true,reviewer_role_enforced:true,owner_only_team:true,password_reset_requires_change_and_mfa:true,reset_revokes_sessions:true,access_revoked:true}),{mode:0o600});
 }finally{
  const page=ownerContext.pages()[0];
  if(page)try{
   const identity=await (await page.request.get('/api/v1/session')).json();
   const response=await page.request.get('/api/v1/team');
   if(response.ok()){
    const target=(await response.json()).find((m:{actor:string})=>m.actor===username);
    if(target?.active)await page.request.post('/api/v1/team/'+username,{data:{roles:target.roles,active:false,expected_version:target.version},headers:{Origin:'https://shiftclarity.pages.dev','X-CSRF-Token':identity.csrf,'Idempotency-Key':randomBytes(16).toString('hex')}});
   }
  }catch{/* The isolated QA identity never has owner permission; report any incomplete cleanup. */}
  await memberContext.close();await ownerContext.close();
 }
});
