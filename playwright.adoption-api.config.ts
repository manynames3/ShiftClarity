import {defineConfig} from '@playwright/test';
import base from './playwright.adoption.config';
export default defineConfig({...base,testMatch:'adoption.spec.ts',outputDir:'artifacts/adoption-api-browser',reporter:'list',use:{...base.use,baseURL:'http://127.0.0.1:5196'},webServer:{command:'SHIFTCLARITY_CONFIG="$PWD/.local/mvp-browser-config.json" backend/.venv/bin/python -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 5196 --no-access-log',url:'http://127.0.0.1:5196/health',reuseExistingServer:false}});
