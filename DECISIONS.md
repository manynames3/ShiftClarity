# ShiftClarity decisions

- Dedicated local workspace; canonical handoff copied unchanged into ./handoff. Source files remain in the requested parent handoff directory as well.
- Single React/TypeScript/Vite package with a pure src/domain boundary, typed fixture adapter and memory-only synthetic state. No backend is necessary for stages 0–3.
- decimal.js for exact accounting; self-hosted OFL Inter via Fontsource. Only requested framework, accounting, font and test dependencies.
- Canonical CSS is reused for visual consistency, with scoped accessibility/responsiveness corrections. Reference toolbar becomes a demo toolbar, without reference-only marketing routes.
- Demo time is fixed. Review event sequence numbers distinguish local actions at that fixed instant.
- Stages 4–6 depend on discovery, approved identity/environment/retention choices, authorized records and independent evaluation. They cannot be certified by synthetic implementation. Scope clarification requested; no real-data work starts implicitly.
- Original handoff acceptance matrix is preserved; application evidence is tracked separately.
- Repowise MCP has no registered index for this new workspace; source/spec inspection supplies implementation context. No unrelated repository/index is modified.

## Scope update from user
User requests common-complaint research, AWS infrastructure direction, conditional Neon database evaluation and an option to enter/import their own data. Canonical fixture-only demo remains available unchanged. A separate local preview will accept only explicit minimized schema fields with no clinical/patient data, validate before publication and keep missing-completeness conclusions blocked. This extension is tracked separately from the original SC-17 fixture-only acceptance. No cloud provisioning, account credit consumption or real-customer security claims are inferred from the AWS preference.

## Phase 4 · October 12, 2026

The user explicitly authorized backend/auth/persistence/secure-import development with realistic synthetic records and approved its libraries. The original stage 3 stop remains part of the unchanged handoff but is superseded for this local work. AWS/cloud spend and real data remain separate gates.

Keep one FastAPI service, PostgreSQL queue, integrated bounded Node worker and the existing React screens. The shared exact-decimal TypeScript engine remains authoritative on the server; no Python accounting rewrite or additional queue system. Private local storage verifies the workflow; a Boto3 adapter and least-privilege S3 configuration provide the cloud boundary.

Cognito is the cloud identity service; Authlib implements OIDC code/PKCE verification. Keycloak is a loopback-only development provider with required OTP and distinct generated accounts. Psycopg connects to PostgreSQL regardless of whether Neon or RDS hosts it. Neon is preferred conditionally for intermittent fictional presentations, with verified TLS and no idle polling. Nothing was provisioned.

Normalized JSON snapshot imports select exact source/rule manifests through an immutable import ID. This narrows the handoff's future multipart/batch-selection transport; it is not arbitrary vendor mapping or a live connector. Import-supplied approvals never establish authority. New source/draft authoring and independent approval use authenticated server operations.

Runtime permissions, forced RLS, immutable records, optimistic review writes, receipts, private downloads, source retention and worker/restore tests support the synthetic build. Real customer semantics, data-use/legal approval, actual cloud recovery, operating contacts and independent measurement remain unproven.

The conditional Neon choice is now implemented: verified Free organization, isolated project lively-field-50384173 and application branch br-holy-block-b75wbmjb, verified TLS through a trusted CA bundle, restricted runtime role, full real-provider browser journey and a Neon-to-local restore rehearsal. AWS services remain prepared, not provisioned. Account suspension settings could not be edited; manual suspend/resume was verified after observing idle state. Both endpoints are capped at 0.25 CU, and unused base compute is suspended.


## October 13 · authorized synthetic AWS deployment

The user explicitly requested container verification and live AWS deployment with Cognito/S3 while retaining Neon. Account 636305658578 is correct; resources are managed through the dedicated shiftclarity-deployer role and remain visible to root. Existing credentials establish/maintain only that role. No long-lived access keys were created, and no DealFinder resources were changed.

The user preferred near-zero idle cost and approved Mangum plus Lambda/SQS. This supersedes the earlier prepared App Runner/single-instance arrangement and its no-additional-queue decision. One image contains FastAPI, the original Node calculator and the branded React build. HTTP API invokes the web function; one FIFO group wakes the worker only for a durable job. PostgreSQL remains the publication authority. SQS notification is sent before the database commit, so notification failure rolls the job back and early delivery retries until the committed row exists. Existing leases, fencing and idempotency still protect publication. No polling web server, NAT gateway, Redis or provisioned Lambda capacity.

The AWS branch is br-blue-butterfly-b7fv14zq, copied from the fictional base and isolated from local identity/storage. Its runtime password is distinct; verified TLS and a nonowner role remain mandatory. Original bytes reside in private S3. Terraform state is encrypted/versioned in a separate private bucket and never committed.

Cognito Lite/classic sign-in preserves the requested cost direction. Classic login ignores prompt=login and can leave the MFA preference unset after verified enrollment. The flow clears provider SSO before its browser-bound code/PKCE redirect. Signed cognito:username is used for provider lookup and returned sub must equal the verified token's sub. Cognito must confirm an enabled, verified software token; enabling an unverified factor was tested to fail. No password-only workspace access.

Cloud cold writes require visible pending feedback. Save buttons block duplicate clicks, hashed public build assets are cached, and confidential responses remain no-store. Endpoint throttling allows initial assets and API calls while staying bounded; it is not a hard cost cap. Lambda functions use 1024 MiB for CPU availability without idle reservation. Live evidence and residual gates are recorded in IMPLEMENTATION_STATUS.md.


A live repeated-import test found that content deduplication of a previously rejected file bypassed the new-attempt stale guard after recovery. Failed-attempt receipts now distinguish a new attempt (blocks review and records the rejection) from an exact request retry (returns its prior receipt without re-invalidating a recovered run). Rejected bytes remain deleted and content/financial rows are not duplicated. A failing regression reproduced the defect, then passed with the fix.
# Public product documentation · October 13, 2026

The user approved creating public `manynames3/ShiftClarity`. The repository includes reviewed application source, original reproducible handoff, a product-led README with four actual synthetic AWS product captures, GitHub About metadata, five ADRs and C4 context/container/component views plus an import sequence. Credentials, authenticator setup keys, Terraform state, backups, generated runtime files and raw artifacts remain excluded. Existing AWS account/project guards are non-secret operator safety checks and remain intact. The GitHub website points to the already-deployed standalone browser demo; the persistent pilot retains assigned-account authentication. No license, customer-value, compliance or production-readiness claim is invented.

