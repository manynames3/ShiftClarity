const PUBLIC_ORIGIN = 'https://shiftclarity.pages.dev';
const AWS_ORIGIN = 'https://4p30g92j37.execute-api.us-east-1.amazonaws.com';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.origin !== PUBLIC_ORIGIN) return new Response('Use the production ShiftClarity address.', {status: 403});
    if (!env.ORIGIN_TOKEN) return new Response('Service unavailable.', {status: 503});
    if (url.pathname === '/') return Response.redirect(PUBLIC_ORIGIN + '/pilot/', 302);
    // Assign the path on a fixed origin so double slashes cannot create an open proxy.
    const target = new URL(AWS_ORIGIN);
    target.pathname = url.pathname;
    target.search = url.search;
    const headers = new Headers(request.headers);
    for (const name of ['host', 'x-forwarded-host', 'x-forwarded-for', 'x-real-ip', 'cf-connecting-ip']) headers.delete(name);
    headers.set('x-shiftclarity-edge', env.ORIGIN_TOKEN);
    try {
      const response = await fetch(new Request(target, {
        method: request.method, headers,
        body: ['GET', 'HEAD'].includes(request.method) ? undefined : request.body,
        redirect: 'manual', duplex: 'half',
      }), {cf: {cacheEverything: false, cacheTtl: 0}});
      const location = response.headers.get('location');
      if (!location || new URL(location, AWS_ORIGIN).origin !== AWS_ORIGIN) return response;
      const redirected = new URL(location, AWS_ORIGIN);
      redirected.protocol = 'https:';
      redirected.host = new URL(PUBLIC_ORIGIN).host;
      const resultHeaders = new Headers(response.headers);
      resultHeaders.set('location', redirected.href);
      return new Response(response.body, {status: response.status, headers: resultHeaders});
    } catch {
      return new Response('Service unavailable. Try again.', {status: 502, headers: {'Cache-Control': 'no-store'}});
    }
  },
};
