import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('approved landing stays bright, accessible and inside five viewport widths',async({page})=>{
 const errors:string[]=[];
 page.on('pageerror',error=>errors.push(error.message));
 await page.emulateMedia({colorScheme:'dark',reducedMotion:'reduce'});
 for(const width of [320,390,768,1024,1440]){
  await page.setViewportSize({width,height:1000});
  await page.goto('/');
  await page.evaluate(()=>document.fonts.ready);
  await expect(page.getByRole('heading',{level:1})).toHaveText('When shifts and invoices disagree, see why.');
  expect(await page.evaluate(()=>getComputedStyle(document.body).backgroundColor)).toBe('rgb(255, 255, 255)');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBe(width);
  expect(await page.evaluate(()=>[...document.querySelectorAll<HTMLImageElement>('img:not([loading="lazy"])')].every(i=>i.complete&&i.naturalWidth>0))).toBe(true);
  await expect(page.getByRole('link',{name:'Try this sample finding →'})).toHaveAttribute('href','/demo/?view=evidence&id=FND-001');
  await expect(page.getByRole('link',{name:'Sign in',exact:true}).first()).toHaveAttribute('href','/pilot/');
  expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
  if([390,1440].includes(width))await page.locator('.hero').screenshot({path:`artifacts/landing-hero-${width}.png`});
  if([390,1440].includes(width))await page.screenshot({path:`artifacts/landing-${width}.png`,fullPage:true});
 }
 expect(errors).toEqual([]);
});

test('keyboard traces each source without moving or changing the financial result',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.goto('/');
 await page.keyboard.press('Tab');
 await expect(page.getByRole('link',{name:'Skip to content'})).toBeFocused();
 await page.keyboard.press('Enter');
 await expect(page).toHaveURL(/#main$/);
 const height=await page.evaluate(()=>document.documentElement.scrollHeight);
 for(const [key,text] of [['terms','$65'],['work','40 approved'],['invoice','$2,400']]){
  const button=page.locator(`button[data-source="${key}"]`);
  await button.focus();
  await page.keyboard.press('Enter');
  await expect(button).toHaveAttribute('aria-pressed','true');
  await expect(page.locator('[data-caption]')).toContainText(text);
  await expect(page.locator('.result-amt')).toHaveText('$200');
  expect(await page.evaluate(()=>document.documentElement.scrollHeight)).toBe(height);
  expect(await page.evaluate(()=>document.getAnimations().filter(a=>a.playState==='running').length)).toBe(0);
  await page.keyboard.press('Space');
  await expect(button).toHaveAttribute('aria-pressed','false');
 }
 await page.getByText('Open the coverage screen',{exact:true}).click();
 await expect(page.locator('.peek img')).toBeVisible();
 await expect.poll(()=>page.locator('.peek img').evaluate((image:HTMLImageElement)=>image.complete&&image.naturalWidth>0)).toBe(true);
 expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
});

test('content, navigation and FAQ work with JavaScript disabled',async({browser})=>{
 const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
 try {
  const page=await context.newPage();
  await page.goto('http://127.0.0.1:5194/');
  await expect(page.getByRole('heading',{level:1})).toBeVisible();
  await expect(page.getByRole('link',{name:'Explore the live demo',exact:true}).first()).toHaveAttribute('href','/demo/');
  await expect(page.locator('button[data-source]')).toHaveCount(0);
  await expect(page.locator('[data-hint]')).toBeHidden();
  await page.getByText('Does ShiftClarity change invoices?',{exact:true}).click();
  await expect(page.getByText('No. It does not edit source invoices or collect money.',{exact:false})).toBeVisible();
 } finally {await context.close();}
});

test('agency entry makes the local path and downloadable evidence concrete',async({page,request})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');
 await expect(page.locator('.hero .cta .btn')).toHaveAttribute('href','/demo/?view=files');await expect(page.locator('.hero .cta .btn')).toBeInViewport();expect(await page.locator('.hero .cta .text-link').count()).toBe(1);
 await expect(page.locator('.hero')).toContainText('Your files stay in your browser');
 for(const [file,signature] of [['pdf','%PDF-'],['xlsx','PK']]){const response=await request.get('/landing/assets/agency-billing-review.'+file);expect(response.status()).toBe(200);expect((await response.body()).subarray(0,signature.length).toString()).toBe(signature);}
 await page.getByText('What will I get back?',{exact:true}).click();await expect(page.getByText('Differences are candidates for review, not recovered revenue or evidence of payment.',{exact:false})).toBeVisible();
});
