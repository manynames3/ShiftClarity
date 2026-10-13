import {chromium} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
const browser=await chromium.launch({channel:'chrome'});
const errors=[],report=[];await mkdir('artifacts/screenshots',{recursive:true});
const sizes=[[1440,1000],[1280,900],[1024,900],[390,844],[320,844]];
for(const [width,height] of sizes){
 const page=await browser.newPage({viewport:{width,height}});page.on('pageerror',e=>errors.push(e.message));
 async function capture(name){await page.evaluate(()=>document.fonts.ready);const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);const file=`artifacts/screenshots/${name}-${width}.png`;await page.screenshot({path:file,fullPage:!name.includes('dialog')});report.push({name,width,height,overflow,file});if(overflow)throw new Error(`${name} at ${width} has page overflow`);}
 const navigate=async view=>{if(width<=680)await page.getByLabel('Demo screen',{exact:true}).selectOption(view);else await page.locator('.refnav').getByRole('link',{name:({'workspace':'Workspace','inputs':'Inputs & rules','evidence':'Evidence','rules':'Rule approval','coverage':'Coverage'})[view],exact:true}).click();};
 for(const view of ['workspace','evidence','inputs','rules','coverage','custom']){await page.goto(`http://127.0.0.1:5178/?view=${view}`);await capture(view);}
 await page.goto('http://127.0.0.1:5178/?view=evidence&id=FND-002');await capture('evidence-missing');
 await page.goto('http://127.0.0.1:5178/');await page.getByLabel('Search findings').fill('no matching finding');await capture('filter-empty');
 await page.goto('http://127.0.0.1:5178/?view=inputs');await page.getByRole('button',{name:'Incomplete invoice extract',exact:true}).click();await navigate('workspace');await capture('incomplete');
 await navigate('inputs');await page.getByRole('button',{name:'No findings · partial coverage'}).click();await navigate('workspace');await capture('no-findings-partial');
 await navigate('inputs');await page.getByRole('button',{name:'Test invalid work row'}).click();await capture('failed-run');
 await page.goto('http://127.0.0.1:5178/?view=rules');await page.getByRole('button',{name:'Test self-approval denial'}).click();await capture('self-approval-denied');await page.getByLabel('Demo role',{exact:true}).selectOption('DEMO-APPROVER');await page.getByRole('checkbox').check();await page.getByRole('button',{name:'Approve rule',exact:true}).click();await capture('rule-approved');
 await page.goto('http://127.0.0.1:5178/?view=evidence');await page.getByRole('button',{name:'Confirm discrepancy',exact:true}).click();await capture('review-dialog');await page.getByLabel('Review reason').fill('Supplied sample terms reviewed');await page.getByRole('button',{name:'Save local review'}).click();await capture('confirmed');
 await page.goto('http://127.0.0.1:5178/?view=inputs');await page.getByRole('button',{name:'Empty imports'}).click();await capture('empty-imports');
 if(width===1024){await page.goto('http://127.0.0.1:5178/?view=evidence');await page.evaluate(()=>document.documentElement.style.zoom='2');await capture('zoom-200');}
 await page.close();
}
await browser.close();await writeFile('artifacts/screenshot-manifest.json',JSON.stringify({report,errors},null,2));if(errors.length)throw new Error(errors.join('\n'));console.log(`${report.length} screenshots; no page errors; no horizontal page overflow.`);
