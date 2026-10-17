import {test} from 'node:test';
import assert from 'node:assert/strict';
import worker from '../infra/cloudflare/_worker.js';

test('proxy fixes origin, preserves CSRF and cookies, replaces client credential, and never follows redirects', async()=>{
  const original=globalThis.fetch;
  try {
    globalThis.fetch=async(request,options)=>{
      assert.equal(new URL(request.url).origin,'https://4p30g92j37.execute-api.us-east-1.amazonaws.com');
      assert.equal(request.redirect,'manual');
      assert.equal(request.headers.get('Origin'),'https://shiftclarity.pages.dev');
      assert.equal(request.headers.get('x-shiftclarity-edge'),'private-test-value');
      assert.equal(request.headers.get('x-forwarded-host'),null);
      assert.equal(await request.text(),'synthetic request');
      assert.equal(options.cf.cacheTtl,0);
      const headers=new Headers({'Location':'https://4p30g92j37.execute-api.us-east-1.amazonaws.com/pilot/','Cache-Control':'no-store'});
      headers.append('Set-Cookie','__Host-session=one; Secure; HttpOnly; SameSite=Lax; Path=/');
      headers.append('Set-Cookie','__Host-flow=two; Secure; HttpOnly; SameSite=Lax; Path=/');
      return new Response(null,{status:303,headers});
    };
    const result=await worker.fetch(new Request('https://shiftclarity.pages.dev//attacker.invalid/api',{method:'POST',body:'synthetic request',headers:{Origin:'https://shiftclarity.pages.dev','x-shiftclarity-edge':'spoofed','x-forwarded-host':'attacker.invalid'}}),{ORIGIN_TOKEN:'private-test-value'});
    assert.equal(result.status,303);
    assert.equal(result.headers.get('Location'),'https://shiftclarity.pages.dev/pilot/');
    assert.equal(result.headers.getSetCookie().length,2);
    assert.equal(result.headers.get('Cache-Control'),'no-store');
  } finally {globalThis.fetch=original;}
});

test('preview domains and missing pilot credentials fail closed',async()=>{
  assert.equal((await worker.fetch(new Request('https://preview.shiftclarity.pages.dev/pilot/'),{ORIGIN_TOKEN:'private-test-value'})).status,403);
  assert.equal((await worker.fetch(new Request('https://shiftclarity.pages.dev/pilot/'),{})).status,503);
});

test('public landing assets use Pages without contacting AWS or attaching credentials',async()=>{
  for (const path of ['/', '/landing/styles.css', '/landing/assets/finding-evidence.png']) {
    const request=new Request('https://shiftclarity.pages.dev'+path);
    const result=await worker.fetch(request,{ASSETS:{fetch:async(received)=>{
      assert.equal(received,request);
      assert.equal(received.headers.get('x-shiftclarity-edge'),null);
      return new Response('public landing',{headers:{'Content-Type':'text/html'}});
    }}});
    assert.equal(result.status,200);
    assert.equal(await result.text(),'public landing');
    assert.match(result.headers.get('Content-Security-Policy'),/frame-ancestors 'none'/);
    assert.equal(result.headers.get('Cache-Control'),'public, max-age=0, must-revalidate');
    assert.equal(result.headers.get('X-Content-Type-Options'),'nosniff');
  }
});

test('landing denies preview hosts and mutations; missing assets retain their 404',async()=>{
  const request=url=>new Request(url);
  assert.equal((await worker.fetch(request('https://preview.shiftclarity.pages.dev/'),{})).status,403);
  assert.equal((await worker.fetch(new Request('https://shiftclarity.pages.dev/',{method:'POST'}),{})).status,405);
  const response=await worker.fetch(request('https://shiftclarity.pages.dev/landing/missing.js'),{ASSETS:{fetch:async()=>new Response('Not found',{status:404})}});
  assert.equal(response.status,404);
});
