import {defineConfig} from '@playwright/test';
import {readFileSync} from 'node:fs';
const outputs=JSON.parse(readFileSync('.local/aws-outputs.json','utf8'));
process.env.SHIFTCLARITY_AWS_QA='1';
export default defineConfig({
 testDir:'tests/pilot',testMatch:'journey.spec.ts',workers:1,fullyParallel:false,timeout:180000,
 expect:{timeout:30000},
 reporter:[['list'],['json',{outputFile:'artifacts/aws-e2e-results.json'}]],
 use:{channel:'chrome',baseURL:outputs.app_origin.value,viewport:{width:1440,height:1000},trace:'off'},
});
