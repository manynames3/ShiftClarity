import {defineConfig} from '@playwright/test';
export default defineConfig({
 testDir:'tests/pilot',workers:1,fullyParallel:false,timeout:120000,
 reporter:[['list'],['json',{outputFile:'artifacts/pilot-e2e-results.json'}]],
 use:{channel:'chrome',baseURL:'http://127.0.0.1:5180',viewport:{width:1440,height:1000},trace:'off'},
});
