import type {Page} from '@playwright/test';
import {readFile,writeFile} from 'node:fs/promises';
import {totp} from '../totp';
import {cognitoLogin} from './cognito-auth';
const accountsFile=new URL('../../.local/accounts.json',import.meta.url);
type Account={username:string;password:string;totp?:string;lastCounter?:number};
export async function login(page:Page,username:string){
 if(process.env.SHIFTCLARITY_AWS_QA==='1')return cognitoLogin(page,username);
 const accounts=JSON.parse(await readFile(accountsFile,'utf8')) as Account[];
 const user=accounts.find(a=>a.username===username)!;
 async function profile(){
  await page.locator('input[name=email]').waitFor({timeout:1500}).catch(()=>{});
  if(await page.locator('input[name=email]').isVisible()){
   await page.locator('input[name=email]').fill(username+'@example.invalid');
   await page.locator('input[name=firstName]').fill('Demo');
   await page.locator('input[name=lastName]').fill(username);
   await page.getByRole('button',{name:'Submit',exact:true}).click();
  }
 }
 async function freshCode(){
  const counter=Math.floor(Date.now()/30000);
  if(user.lastCounter!==undefined&&counter<=user.lastCounter)await page.waitForTimeout((user.lastCounter+1)*30000-Date.now()+300);
  user.lastCounter=Math.floor(Date.now()/30000);
  await writeFile(accountsFile,JSON.stringify(accounts,null,2),{mode:0o600});
  return totp(user.totp!);
 }
 await page.goto('/auth/login');
 await page.locator('input[name=username]').fill(username);
 await page.locator('input[name=password]').fill(user.password);
 await page.locator('button[name=login]').click();
 const setup=page.getByRole('heading',{name:'Mobile Authenticator Setup'});
 await Promise.race([page.locator('input[name=otp]').waitFor(),setup.waitFor()]);
 if(await setup.isVisible()){
  await page.getByText('Unable to scan?',{exact:true}).click();
  const key=await page.locator('p').allTextContents();
  user.totp=key.find(t=>/^[A-Z2-7 ]{32,}$/.test(t.trim()))!.replaceAll(' ','').trim();
  await writeFile(accountsFile,JSON.stringify(accounts,null,2),{mode:0o600});
  await page.locator('input[name=totp]').fill(await freshCode());
  await page.locator('input[name=userLabel]').fill('Synthetic QA authenticator');
  await page.getByRole('button',{name:'Submit',exact:true}).click();
  await profile();
  // Enrollment itself is not accepted as MFA. Authenticate through the required OTP execution.
  await page.goto('/auth/login');
  await page.locator('input[name=username]').fill(username);
  await page.locator('input[name=password]').fill(user.password);
  await page.locator('button[name=login]').click();
 }
 if(!user.totp)throw new Error('Local test account has no recorded QA authenticator.');
 await page.locator('input[name=otp]').fill(await freshCode());
 await page.locator('button[name=login]').click();
 await profile();
 await page.waitForURL(username==='outsider'?/\/auth\/callback/:/\/pilot\//);
}
