import type {Page} from '@playwright/test';
import {readFile,writeFile} from 'node:fs/promises';
import {totp} from '../totp';
const file=new URL('../../.local/aws-accounts.json',import.meta.url);
type Account={username:string;password:string;totp?:string;lastCounter?:number};
export async function cognitoLogin(page:Page,username:string){
 const accounts=JSON.parse(await readFile(file,'utf8')) as Account[];
 const user=accounts.find(account=>account.username===username);
 if(!user)throw Error('No authorized private AWS test account');
 async function code(){
  if(!user!.totp)throw Error('No enrolled test authenticator');
  const counter=Math.floor(Date.now()/30000);
  if(user!.lastCounter!==undefined&&counter<=user!.lastCounter)await page.waitForTimeout((user!.lastCounter+1)*30000-Date.now()+300);
  user!.lastCounter=Math.floor(Date.now()/30000);
  await writeFile(file,JSON.stringify(accounts,null,2),{mode:0o600});
  return totp(user!.totp);
 }
 await page.goto('/auth/login');
 await page.locator('input[name=username]:visible').fill(user.username);
 await page.locator('input[name=password]:visible').fill(user.password);
 await page.locator('input[name=signInSubmitButton]:visible').click();
 await page.locator('input[name=userCode],input[name=authentication_code]').waitFor();
 if(await page.locator('input[name=userCode]').isVisible()){
  await page.getByText('Show secret key',{exact:true}).click();
  const secret=await page.locator('body').innerText();
  user.totp=secret.match(/[A-Z2-7]{32,}/)?.[0];
  if(!user.totp)throw Error('Cognito enrollment did not expose a valid authenticator');
  await writeFile(file,JSON.stringify(accounts,null,2),{mode:0o600});
  await page.locator('input[name=userCode]').fill(await code());
  await page.locator('input[name=friendlyDeviceName]').fill('ShiftClarity '+username+' test authenticator');
 }else{
  await page.locator('input[name=authentication_code]').fill(await code());
 }
 await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await page.waitForURL(username==='outsider'?/execute-api.*\/auth\/callback/:/execute-api.*\/pilot\//);
}
