import {defineConfig} from '@playwright/test';
process.env.SHIFTCLARITY_MVP_AWS_QA='1';
export default defineConfig({
 testDir:'tests/mvp',testMatch:'import.spec.ts',workers:1,fullyParallel:false,timeout:240000,
 expect:{timeout:45000},
 reporter:[['list'],['json',{outputFile:'artifacts/mvp-live-browser-results.json'}]],
 use:{channel:'chrome',baseURL:'https://shiftclarity.pages.dev',viewport:{width:1440,height:1000},actionTimeout:45000,navigationTimeout:45000,trace:'off'},
});
