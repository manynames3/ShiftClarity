import {defineConfig} from '@playwright/test';
process.env.SHIFTCLARITY_CAPACITY_AWS_QA='1';
export default defineConfig({testDir:'tests/mvp',testMatch:'capacity.spec.ts',workers:1,timeout:240000,expect:{timeout:45000},reporter:'list',use:{channel:'chrome',baseURL:'https://shiftclarity.pages.dev',actionTimeout:45000,navigationTimeout:45000,trace:'off'}});
