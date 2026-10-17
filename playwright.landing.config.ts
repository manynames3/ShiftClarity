import {defineConfig} from '@playwright/test';

export default defineConfig({
 testDir:'tests/landing', workers:1, reporter:'list',
 use:{channel:'chrome',baseURL:'http://127.0.0.1:5194',viewport:{width:1440,height:1000}},
 webServer:{command:'npm run build:pages && python3 -m http.server 5194 --bind 127.0.0.1 --directory dist/cloudflare',url:'http://127.0.0.1:5194',reuseExistingServer:false},
});
