# ADR 0006: Use Cloudflare Pages as the full pilot origin

- **Status:** Accepted
- **Date:** October 13, 2026
- **Scope:** Synthetic pilot at `https://shiftclarity.pages.dev`

## Context

The user requested a simpler Cloudflare Pages URL and selected the full signed-in pilot under that address. The existing AWS backend, Cognito, private S3, and Neon should keep their responsibilities and low idle-cost design.

## Decision

Use one small Pages advanced-mode Worker as a fixed-origin HTTPS proxy. The approved October 17 landing page now occupies `/`; `/pilot/` and the existing `/demo/` remain available. API calls, private downloads, auth callbacks and app assets share the Pages origin. No cross-site session cookie or relaxed CORS policy is introduced.

The proxy preserves browser Origin/CSRF headers and secure HttpOnly cookies. It replaces any incoming edge credential with its private binding and never follows upstream redirects. Only redirects back to the AWS gateway are rewritten to the Pages address; Cognito redirects retain their destination. Preview hostnames are denied so they cannot share production login state.

The backend separately validates the exact AWS transport host and a constant-time private edge credential. This credential identifies the proxy, not a user: normal session, MFA, membership and role checks still apply. The public health response remains record-free. Cognito accepts only the Pages callback and logout origins.

Store the credential in a Pages secret and the encrypted Lambda environment, supplied through sensitive Terraform input. It is never bundled into browser assets. Terraform state and variable files remain private. The existing database secret remains in Secrets Manager; this adds no second paid secret.

## Alternatives considered

- **Pages-hosted browser demo only:** simpler, but does not meet the selected full-pilot requirement.
- **Separate frontend and cross-origin AWS API:** requires cross-site cookies and CORS changes.
- **Purchased domain and additional AWS routing infrastructure:** unnecessary for the requested free Pages hostname.

## Consequences

Cloudflare is now in the request path and handles fictional authenticated traffic. The landing page and its dedicated `/landing/` assets are served by Pages through the Worker’s `ASSETS` binding and do not invoke AWS. All proxied requests consume the account's Pages Functions/Workers quota, including assets; there is no extra monthly baseline within the Free allowance. AWS requests still incur their usual usage charges. Browser caching of content-hashed assets remains available; private responses are not cached by the proxy.

The old AWS app address is an internal origin and rejects requests lacking the edge credential. A fresh sign-in is required at the new hostname. Real-data operating and legal gates still apply. No paid plan or database migration is needed.

## Implementation and verification

[Proxy](../../infra/cloudflare/_worker.js), [backend host guard](../../backend/app.py), [settings](../../backend/config.py), [Terraform](../../infra/main.tf), [proxy tests](../../tests/edge.test.mjs), and [gateway tests](../../backend/tests/test_edge.py). See [Cloudflare operations](../CLOUDFLARE.md) for deployment and recorded live verification.

October 17 amendment: keep the approved public landing static at the edge. This preserves the existing same-origin private application and avoids an AWS image deployment for public marketing content. The user explicitly approved push/deploy after reviewing desktop and mobile renders.
