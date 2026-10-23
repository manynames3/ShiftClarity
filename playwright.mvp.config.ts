import {defineConfig} from '@playwright/test';
export default defineConfig({
 testDir:'tests/mvp',workers:1,fullyParallel:false,timeout:90000,reporter:'list',
 use:{channel:'chrome',baseURL:'http://127.0.0.1:5196',viewport:{width:1440,height:1000},trace:'off'},
 webServer:{command:'backend/.venv/bin/python tests/setup-mvp-browser.py && SHIFTCLARITY_CONFIG="$PWD/.local/mvp-browser-config.json" backend/.venv/bin/python -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 5196 --no-access-log',url:'http://127.0.0.1:5196/health',reuseExistingServer:false},
});
