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

test('preview domains and missing credentials fail closed; root opens full pilot',async()=>{
  assert.equal((await worker.fetch(new Request('https://preview.shiftclarity.pages.dev/pilot/'),{ORIGIN_TOKEN:'private-test-value'})).status,403);
  assert.equal((await worker.fetch(new Request('https://shiftclarity.pages.dev/pilot/'),{})).status,503);
  assert.equal((await worker.fetch(new Request('https://shiftclarity.pages.dev/'),{ORIGIN_TOKEN:'private-test-value'})).headers.get('location'),'https://shiftclarity.pages.dev/pilot/');
});
