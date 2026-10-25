import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {readFileSync} from 'node:fs';
const fixture='public/examples/agency-evaluation/';
async function configure(page:import('@playwright/test').Page){
 await page.getByRole('button',{name:'Load realistic fictional files',exact:true}).click();
 for(const name of ['work.csv','invoices.csv','rates.csv'])await page.getByRole('button',{name:'Confirm '+name+' mapping',exact:true}).click();
 await page.getByLabel('I’m authorized to test these minimized records, and I checked the supplied rate terms and declarations.').check();
}
async function publish(page:import('@playwright/test').Page){await page.getByRole('button',{name:'Validate files locally',exact:false}).click();await expect(page.getByText('$460.00',{exact:true})).toBeVisible();await page.getByLabel('I checked the counts, totals and evidence limits.').check();await page.getByRole('button',{name:'Open findings & report',exact:false}).click();}
test('prospect imports their own exports, reviews both directions, and downloads a traceable report without sending records',async({page},info)=>{
 const requests:string[]=[];page.on('request',r=>requests.push(r.method()+' '+r.url()+' '+(r.postData()||'')));
 await page.goto('/demo/?view=files');
 for(const kind of ['work','invoices','rates']){const text=readFileSync(fixture+kind+'.csv','utf8').replaceAll('C101','OWN-CANARY-42');await page.getByLabel('Local '+({work:'Approved work',invoices:'Posted invoices & credits',rates:'Approved contract rates'}[kind]),{exact:true}).setInputFiles({name:kind+'.csv',mimeType:'text/csv',buffer:Buffer.from(text)});await expect(page.locator('.local-mapping').filter({hasText:kind+'.csv'})).toBeVisible();}
 await page.getByLabel('Period starts',{exact:true}).fill('2026-10-05');await page.getByLabel('Period ends (inclusive)',{exact:true}).fill('2026-10-11');await page.getByLabel('Files current through (UTC)',{exact:true}).fill('2026-10-14T00:00');await page.getByLabel('Billing cutoff (UTC)',{exact:true}).fill('2026-10-13T00:00');await page.getByLabel('Rate author reference',{exact:true}).fill('AUTHOR-1');await page.getByLabel('Independent approver reference',{exact:true}).fill('APPROVER-2');
 await page.getByLabel('Work exports include all records for this facility and service period.').check();await page.getByLabel('Invoice exports include all posted lines, credits and rebills through this cutoff for the same scope.').check();await page.getByLabel('Independent work hours (optional)',{exact:true}).fill('69');await page.getByLabel('Independent signed posted total USD (optional)',{exact:true}).fill('3501.00');
 for(const name of ['work.csv','invoices.csv','rates.csv'])await page.getByRole('button',{name:'Confirm '+name+' mapping',exact:true}).click();await page.getByLabel('I’m authorized to test these minimized records, and I checked the supplied rate terms and declarations.').check();await publish(page);
 await expect(page.getByText('6 of 8 shifts rule-checked')).toBeVisible();await expect(page.locator('.demo-data-label')).toHaveText('Your records · local onlyRecords remain in this tab. Refresh clears your work.');await expect(page.getByRole('link',{name:'Rule approval',exact:true})).toHaveCount(0);
 await expect(page.locator('.toast')).toHaveCount(0,{timeout:10000});
 await page.screenshot({path:info.outputPath('own-file-workspace.png'),fullPage:true});
 await page.getByRole('button',{name:'Download report',exact:true}).click();await expect(page.getByRole('dialog')).toContainText('Your records · local only');await expect(page.getByRole('dialog')).toContainText('Non-hourly invoice lines');
 await page.emulateMedia({media:'print'});await page.pdf({path:info.outputPath('own-file-billing-review.pdf'),printBackground:true,preferCSSPageSize:true});await page.emulateMedia({media:null});
 const downloadEvent=page.waitForEvent('download');await page.getByRole('button',{name:'Download CSV',exact:true}).click();const download=await downloadEvent,stream=await download.createReadStream(),chunks:Buffer[]=[];for await(const c of stream!)chunks.push(c);const report=Buffer.concat(chunks).toString();expect(report).toContain('Non-hourly invoice lines');expect(report).toContain('840');expect(report).toContain('460');expect(report).toContain('SHA-256');expect(report).toContain('Work approval event date');expect(report).not.toContain('OWN-CANARY-42');await download.saveAs(info.outputPath('own-file-report.csv'));
 await page.getByRole('button',{name:'Cancel',exact:true}).click();await page.getByRole('link',{name:'Review next finding',exact:false}).click();await page.getByRole('tab',{name:'Approved work',exact:true}).click();await expect(page.getByRole('tabpanel')).toContainText('event date unknown; approved status observed');
 await page.getByRole('button',{name:'Confirm discrepancy',exact:false}).click();await page.getByLabel('Review reason',{exact:true}).fill('Checked source terms and all posted allocations.');await page.getByRole('button',{name:'Save local review',exact:true}).click();
 expect(requests.some(r=>r.includes('OWN-CANARY-42'))).toBe(false);expect(requests.filter(r=>!r.startsWith('GET '))).toEqual([]);expect(await page.evaluate(()=>JSON.stringify({local:{...localStorage},session:{...sessionStorage}}))).not.toMatch(/OWN-CANARY|AUTHOR-1|FAC-ALPHA|3501/);
 await page.reload();await expect(page.getByText('12 of 14 shifts rule-checked')).toBeVisible();
});
test('corrections and incomplete sources cannot publish a misleading difference',async({page})=>{await page.goto('/demo/?view=files');await configure(page);await page.getByLabel('Independent signed posted total USD (optional)',{exact:true}).fill('3476.00');await page.getByRole('button',{name:'Validate files locally',exact:false}).click();await expect(page.getByRole('alert')).toContainText('Independent signed');await expect(page.getByRole('button',{name:'Open findings & report',exact:false})).toHaveCount(0);await page.getByLabel('Independent signed posted total USD (optional)',{exact:true}).fill('3501.00');await page.getByLabel('Invoice exports include all posted lines, credits and rebills through this cutoff for the same scope.').uncheck();await page.getByRole('button',{name:'Validate files locally',exact:false}).click();await expect(page.getByText('Coverage is incomplete.',{exact:false})).toBeVisible();await expect(page.getByText('$460.00',{exact:true})).toHaveCount(0);});
for(const width of [320,390,1440])for(const theme of ['light','dark'])test(`local evaluation accessible at ${width} ${theme}`,async({page},info)=>{await page.setViewportSize({width,height:900});await page.goto('/demo/?view=files');if(theme==='dark')await page.getByRole('button',{name:'Use dark mode',exact:true}).click();await configure(page);await expect(page.locator('body')).toHaveJSProperty('scrollWidth',width);const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();expect(axe.violations).toEqual([]);await page.screenshot({path:info.outputPath(`local-import-${width}-${theme}.png`),fullPage:true});});

test('saved mapping metadata is reusable without retaining source rows',async({page})=>{
 await page.goto('/demo/?view=files');await configure(page);
 const event=page.waitForEvent('download');await page.getByRole('button',{name:'Download confirmed mappings',exact:true}).click();const file=await event,stream=await file.createReadStream(),parts:Buffer[]=[];for await(const part of stream!)parts.push(part);const text=Buffer.concat(parts).toString();expect(text).not.toContain('C101');expect(text).not.toContain('840.00');
 await page.getByLabel('Saved local mapping profiles',{exact:true}).setInputFiles({name:'mappings.json',mimeType:'application/json',buffer:Buffer.from(text)});
 const work=page.locator('.local-mapping').filter({hasText:'work.csv'});await work.locator('summary').click();await work.getByRole('button',{name:'Reuse matching saved mapping',exact:true}).click();await expect(work).toContainText('Needs confirmation');await expect(page.getByRole('button',{name:'Validate files locally',exact:false})).toBeDisabled();await work.getByRole('button',{name:'Confirm work.csv mapping',exact:true}).click();await expect(page.getByRole('button',{name:'Validate files locally',exact:false})).toBeEnabled();
});

import {read,utils} from 'xlsx';

test('Excel exports are read in-browser with explicit sheet selection and a real local XLSX report',async({page},info)=>{
 const outbound:string[]=[];page.on('request',r=>{if(r.method()!=='GET'||r.url().includes('/api/'))outbound.push(r.url());});
 await page.goto('/demo/?view=files');
 for(const [kind,label] of [['work','Approved work'],['invoices','Posted invoices & credits'],['rates','Approved contract rates']]){
  await page.getByLabel('Local '+label,{exact:true}).setInputFiles(fixture+kind+'.xlsx');
  const picker=page.locator('.import-section').filter({has:page.getByRole('heading',{name:'Choose a worksheet · '+kind+'.xlsx',exact:true})});
  await expect(picker.getByLabel('Header row for '+kind+'.xlsx',{exact:true})).toHaveValue('3');
  await expect(picker.getByRole('combobox',{name:'Worksheet for '+kind+'.xlsx',exact:true})).toHaveValue(({work:'Work detail',invoices:'Invoice detail',rates:'Approved rates'} as Record<string,string>)[kind]);
  await picker.getByRole('button',{name:'Use selected worksheet',exact:true}).click();await page.getByRole('button',{name:new RegExp('^Confirm '+kind+'\\.xlsx / .* mapping$')}).click();
 }
 await page.getByLabel('Period starts',{exact:true}).fill('2026-10-05');await page.getByLabel('Period ends (inclusive)',{exact:true}).fill('2026-10-11');await page.getByLabel('Files current through (UTC)',{exact:true}).fill('2026-10-14T00:00');await page.getByLabel('Billing cutoff (UTC)',{exact:true}).fill('2026-10-13T00:00');await page.getByLabel('Rate author reference',{exact:true}).fill('AUTHOR-1');await page.getByLabel('Independent approver reference',{exact:true}).fill('APPROVER-2');await page.getByLabel('Work exports include all records for this facility and service period.').check();await page.getByLabel('Invoice exports include all posted lines, credits and rebills through this cutoff for the same scope.').check();await page.getByLabel('Independent work hours (optional)',{exact:true}).fill('69');await page.getByLabel('Independent signed posted total USD (optional)',{exact:true}).fill('3501.00');await page.getByLabel('I’m authorized to test these minimized records, and I checked the supplied rate terms and declarations.').check();await publish(page);
 await page.getByRole('button',{name:'Download report',exact:true}).click();const event=page.waitForEvent('download');await page.getByRole('button',{name:'Download Excel',exact:true}).click();const file=await event,stream=await file.createReadStream(),chunks:Buffer[]=[];for await(const chunk of stream!)chunks.push(chunk);const bytes=Buffer.concat(chunks),book=read(bytes,{type:'buffer',cellFormula:true}),overview=Object.fromEntries(utils.sheet_to_json<(string|number)[]>(book.Sheets.Overview,{header:1}).slice(1) as [string,string|number][]);
 expect(overview['Potential underbilling before review exclusions (USD)']).toBe(460);expect(overview['Potential overbilling before review exclusions (USD)']).toBe(24);expect(book.Sheets['Non-hourly invoice lines'].E2.v).toBe(25);expect(book.SheetNames).toContain('Invoice source lines');for(const sheet of Object.values(book.Sheets))for(const [key,cell] of Object.entries(sheet))if(!key.startsWith('!'))expect(cell.f).toBeUndefined();await file.saveAs(info.outputPath('own-file-billing-review.xlsx'));expect(outbound).toEqual([]);
});
test('an active Excel workbook is rejected locally before mappings or upload',async({page})=>{
 await page.goto('/demo/?view=files');const XLSX=await import('xlsx'),book=XLSX.utils.book_new(),sheet=XLSX.utils.aoa_to_sheet([['Work ID','Hours'],['W1',8]]);sheet.B2.f='2+6';XLSX.utils.book_append_sheet(book,sheet,'Time');await page.getByLabel('Local Approved work',{exact:true}).setInputFiles({name:'formula.xlsx',mimeType:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',buffer:XLSX.write(book,{type:'buffer',bookType:'xlsx',compression:true})});await expect(page.getByRole('alert')).toContainText('Formula cells');await expect(page.locator('.local-mapping')).toHaveCount(0);await expect(page.getByRole('button',{name:'Validate files locally',exact:false})).toBeDisabled();
});

test('own-file setup separates staged files from demo results and clearing names the local records',async({page})=>{
 await page.goto('/demo/?view=files');
 const nav=page.getByRole('navigation',{name:'Application navigation',exact:true});
 const disclosure=page.getByRole('note',{name:'Local data disclosure',exact:true});
 await expect(nav.locator('.nav-count')).toHaveCount(0);
 await expect(disclosure).toContainText('Your records · local only');
 await expect(disclosure.getByRole('button')).toHaveCount(0);
 await configure(page);await publish(page);
 await expect(nav.locator('.nav-count')).toHaveText('4');
 await disclosure.getByRole('button',{name:'Clear local records',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'Clear local records?',exact:true});
 await expect(dialog).toContainText('Download your report first');
 await dialog.getByRole('button',{name:'Clear local records',exact:true}).click();
 await expect(page.getByRole('note',{name:'Demo disclosure',exact:true})).toContainText('Fictional demo data');
 await expect(nav.locator('.nav-count')).toHaveText('2');
});
