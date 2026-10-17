import {cp, mkdir, rm, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const output = `${root}dist/cloudflare`;
await rm(output, {recursive: true, force: true});
await mkdir(`${output}/landing`, {recursive: true});
await cp(`${root}landing`, `${output}/landing`, {recursive: true});
await cp(`${root}landing/index.html`, `${output}/index.html`);
await rm(`${output}/landing/index.html`);
await cp(`${root}infra/cloudflare/_worker.js`, `${output}/_worker.js`);
await writeFile(`${output}/404.html`, '<!doctype html><html lang="en"><meta charset="utf-8"><title>Not found</title><h1>Page not found</h1><a href="/">Return to ShiftClarity</a></html>\n');
console.log('Built Cloudflare landing assets and the existing pilot proxy in dist/cloudflare.');
