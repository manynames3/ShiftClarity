import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {readFileSync,mkdirSync} from 'node:fs';

test('demo report is discoverable, complete, private and reflects current decisions',async({page})=>{
 const requests:string[]=[];page.on('request',request=>{if(!['GET','HEAD'].includes(request.method())||request.url().includes('/api/'))requests.push(request.url());});
 await page.goto('/demo/');
 await expect(page.getByRole('button',{name:'Download report',exact:true})).toBeInViewport();
 await page.getByRole('link',{name:'Rate change not reflected'}).click();
 await page.getByRole('button',{name:'Confirm discrepancy',exact:true}).click();
 await page.getByLabel('Review reason').fill('PRIVATE_REPORT_NOTE =HYPERLINK("https://example.invalid", "test") <img src="https://example.invalid/tracker">');
 await page.getByRole('button',{name:'Save local review'}).click();
 await page.getByLabel('Search findings').fill('no such finding');
 await page.getByRole('button',{name:'Download report',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'Download billing review'}),preview=page.getByRole('article',{name:'Billing report preview'});
 await expect(preview).toContainText('2 findings. 1 confirmed');
 await expect(preview).toContainText('FND-001');await expect(preview).toContainText('FND-002');
 await expect(preview).toContainText('No estimate applied');await expect(preview).not.toContainText('PRIVATE_REPORT_NOTE');
 const csvDownload=page.waitForEvent('download');await dialog.getByRole('button',{name:'Download CSV',exact:true}).click();
 const download=await csvDownload;mkdirSync('artifacts/reports',{recursive:true});await download.saveAs('artifacts/reports/demo-billing-review.csv');
 const csv=readFileSync('artifacts/reports/demo-billing-review.csv','utf8');
 expect(csv).toContain('Confirmed discrepancy');expect(csv).toContain('Needs review');expect(csv).toContain('Coverage gaps');expect(csv).not.toContain('PRIVATE_REPORT_NOTE');expect(csv).not.toContain('worker_id');
 await dialog.getByLabel('Include reviewer notes I’m authorized to share').check();
 await expect(preview).toContainText('PRIVATE_REPORT_NOTE');await expect(preview.locator('img')).toHaveCount(1);
 expect(requests).toEqual([]);
 await page.evaluate(()=>{window.print=()=>{document.documentElement.dataset.printInvoked='true';};});
 await dialog.getByRole('button',{name:'Print / save PDF'}).click();await expect(page.locator('html')).toHaveAttribute('data-print-invoked','true');
 await dialog.getByRole('button',{name:'Cancel',exact:true}).click();await expect(dialog).toHaveCount(0);await expect(page.getByRole('button',{name:'Download report',exact:true})).toBeFocused();
 await page.getByRole('button',{name:'Download report',exact:true}).click();await expect(page.getByLabel('Include reviewer notes I’m authorized to share')).not.toBeChecked();
});

test('demo report renders cleanly for print, mobile and both themes',async({page})=>{
 await page.goto('/demo/');await page.getByRole('button',{name:'Download report',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'Download billing review'});
 await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].filter(image=>image.getClientRects().length).map(image=>image.decode()));});
 mkdirSync('artifacts/reports',{recursive:true});await page.screenshot({path:'artifacts/reports/demo-report-desktop.png'});
 await page.emulateMedia({media:'print'});
 await expect(page.getByRole('navigation',{name:'Application navigation'})).toBeHidden();await expect(page.getByRole('button',{name:'Print / save PDF'})).toBeHidden();
 await expect(page.getByRole('heading',{name:'Billing review',exact:true})).toBeVisible();await expect(page.getByRole('heading',{name:'Review history',exact:true})).toBeVisible();
 await page.pdf({path:'artifacts/reports/demo-billing-review.pdf',preferCSSPageSize:true,printBackground:true});
 await page.emulateMedia({media:'screen'});
 for(const width of [390,320]){
  await page.setViewportSize({width,height:844});
  expect(await dialog.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);
  expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
  await dialog.getByRole('button',{name:'Close report',exact:true}).click();
  await expect(page.getByRole('button',{name:'Download report',exact:true})).toBeInViewport();
  await page.getByRole('button',{name:'Download report',exact:true}).click();
 }
 await page.screenshot({path:'artifacts/reports/demo-report-mobile.png'});
 await dialog.getByRole('button',{name:'Cancel',exact:true}).click();
 await page.getByRole('button',{name:'Use dark mode'}).click();await page.getByRole('button',{name:'Download report',exact:true}).click();
 expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
 await page.getByRole('button',{name:'Close report',exact:true}).click();
 await page.emulateMedia({media:'print'});await expect(page.locator('.app')).toBeVisible();
});

test('reports remain available from sources and evidence, and label stale results',async({page})=>{
 await page.goto('/demo/?view=inputs');await page.getByRole('button',{name:'Test invalid work row'}).click();
 await page.getByRole('button',{name:'Download report',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'Download billing review'});
 await expect(dialog.getByRole('alert')).toContainText('Stale results');await expect(page.getByRole('article')).toContainText('STALE RESULTS');
 await page.keyboard.press('Escape');await expect(dialog).toHaveCount(0);
 await page.goto('/demo/?view=evidence&id=FND-001');await page.getByRole('button',{name:'Download report',exact:true}).click();await expect(dialog).toBeVisible();
});
