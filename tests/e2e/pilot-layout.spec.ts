import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {initialDemo} from '../../src/domain/demo';
import {parseCustom} from '../../src/adapters/custom';

test('signed-in pilot header fits desktop and mobile with visible account actions',async({page})=>{
 const inputs=parseCustom(readFileSync('examples/synthetic-healthcare-staffing/bundle.json','utf8'));
 const draft=JSON.parse(readFileSync('handoff/data/synthetic/draft_rule.json','utf8'));
 const state=initialDemo(inputs,draft);
 await page.route('**/api/v1/session',route=>route.fulfill({json:{actor:'DEMO-REVIEWER',roles:['reviewer','importer'],csrf:'layout-test-only',synthetic:true}}));
 await page.route('**/api/v1/workspace',route=>route.fulfill({json:{state,version:1,catalog:{rules:state.inputs.rules,excerpts:state.inputs.excerpts}}}));
 await page.route('**/api/v1/members',route=>route.fulfill({json:[{actor:'DEMO-REVIEWER'}]}));
 for(const width of [1920,1505,1440,1280,1024,390,320]){
  await page.setViewportSize({width,height:900});
  await page.goto('/pilot/');
  await expect(page.getByRole('button',{name:'Sign out',exact:true})).toBeVisible();
  await page.evaluate(()=>document.fonts.ready);
  const bounds=await page.evaluate(()=>({viewport:innerWidth,width:document.documentElement.scrollWidth,
   outside:[...document.querySelectorAll('.topbar *')].filter(el=>el.getBoundingClientRect().right>innerWidth+1).map(el=>el.className)}));
  expect.soft(bounds.width,`${width}px pilot header: ${bounds.outside.join(', ')}`).toBeLessThanOrEqual(bounds.viewport);
  if(width>1000){
   const nav=page.getByRole('navigation',{name:'Application navigation',exact:true});
   await expect(nav).toBeVisible();
   const navigation=await nav.boundingBox(),account=await page.locator('.top-right').boundingBox();
   expect(navigation!.x+navigation!.width,`${width}px navigation overlaps account actions`).toBeLessThanOrEqual(account!.x);
  }
  if([1505,390].includes(width))await page.screenshot({path:`artifacts/pilot-header-${width}.png`,fullPage:true});
 }
});
