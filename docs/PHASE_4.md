# Phase 4 · Secured synthetic pilot build

The October 12 request authorized local phase 4 with fictional records. The October 13 follow-up explicitly authorized the synthetic AWS deployment, dedicated role, Lambda/SQS and Mangum. It supersedes the original stage 3 stop and prior AWS preparation-only gate. Customer records, independent measurement and a production launch remain unapproved.

## Working architecture

React retains the original five screens, SVGs and design tokens. `/pilot/` obtains state from one FastAPI service; `/demo/` remains the standalone demonstration. Pilot decisions, source registration, drafts, approvals, imports, tasks and runs are server operations. No browser role switch or reset grants authority.

PostgreSQL stores immutable completed snapshots, source revisions/lineage, rule versions, documents, receipts, jobs and audit events. A restricted runtime login owns no application tables and has no superuser/BYPASSRLS privilege. Organization-scoped tables have forced row-level policies, in addition to endpoint checks. Memberships are provisioned by the operator from verified issuer/subject mappings. Every request rechecks active membership, making revocation effective immediately.

The existing pure TypeScript calculation engine is bundled as a bounded Node process. Python coordinates persistence, not accounting. Rate and money arithmetic stays in the shared decimal engine. Parser processes have a 96 MiB JavaScript heap limit, a 12-second execution timeout and a maximum of two concurrent processes. These limits are process controls, not a measured cloud capacity guarantee.

The integrated worker claims PostgreSQL jobs with row locks and lease tokens. It fences reclaimed workers, retries transient failures up to three attempts, and atomically publishes a completed run with its workspace head and audit event. Reviews lock the head and check run ID, evidence fingerprint and optimistic version; idempotency receipts prevent duplicate writes. A failed import or terminal job retains the prior result and blocks decisions until a validated run is published.

Local development retains the event-driven integrated worker, with no idle database polling. AWS instead uses a FIFO SQS notification and separate Lambda worker. Notifications are sent inside the job-creation transaction; failed sends roll back and early delivery retries until commit. Job-targeted leases and publication protect replay. No recurring wake sweep or always-on process is deployed.

## Identity and sessions

AWS Cognito is the deployed cloud identity service. Authlib is the OIDC client library, not a competing identity service. The local environment remains available, and the separate AWS functions serve the same interface/API against an isolated Neon branch. Local identity uses Keycloak 26.8.0 with a required password/OTP flow and signed AMR claims. Distinct reviewer, author, approver, observer and isolation-test accounts have generated passwords. Test-only authenticator helpers live under `tests/`; the application implements no password or OTP verifier.

Authorization-code sign-in uses PKCE S256, single-use browser-bound state, nonce and verified RS256 issuer/audience/time claims. Cloud startup checks Cognito's required software-token MFA and registered code callback; each login also rechecks required MFA, matching provider subject and verified authenticator enrollment. Classic SSO is cleared before fresh code/PKCE authentication. Local identity tokens must attest OTP execution. Sessions use random HttpOnly/SameSite cookies, hashed database tokens and 15-minute expiry. Cloud cookies use the __Host- prefix, Secure and HTTPS; local HTTP is restricted to loopback. Write requests require both a matching Origin and session CSRF token. Sign-out revokes the application session and redirects through provider sign-out.

## Import boundary

Accepted input is one complete normalized JSON snapshot, at most 1 MiB and 2,000 rows per collection, using the exact fields in `src/adapters/custom.ts`. The import declares fictional data through both the manifest and `X-Data-Classification: synthetic`. IDs must be pseudonymous. No names, contact/patient/clinical fields, archives, executable formats, PDF, OCR, model extraction or arbitrary vendor CSV mapping are accepted.

The server checks content and controls, then registered immutable rules and source excerpts. Importing a claimed approval never grants rule approval. Authors register bounded fictional text separately, propose an explicit predecessor/date/rate, and require a different authenticated approver. Imports may use those approved versions. Reusing a work revision with conflicting content fails; invoice changes get new content revisions and preserved lineage. Identical content reuses the accepted import; reruns never add the same amounts twice.

Safe fixed diagnostics distinguish schema/JSON errors, unsupported fields, source control mismatches, unapproved versions and conflicting revisions without echoing source values. Interrupted quarantine can be retried safely; duplicate validators publish one accepted receipt.

Private storage uses opaque keys, separate quarantine/accepted paths, owner-only local file permissions and authorization-gated downloads. Rejected bytes are deleted and diagnostics contain fixed codes. AWS uses S3 public-access blocks, bucket-owner enforcement, encryption, TLS-only policy and organization-scoped application permissions. Downloads are streamed after authorization; no public or reusable signed file links are issued.

Plain text can still contain sensitive information. Field validation and a synthetic attestation are not automated data classification or legal permission. Do not place real records or personal notes in this build.

## Retention and recovery

Accepted original source objects are available for 30 days; quarantine objects expire within one day in the prepared S3 lifecycle. API source downloads and run requests reject expired imports. `backend.maintenance expire-sources` removes expired local objects and normalized import copies using a separate owner credential. Completed normalized snapshots, review receipts and rule/source evidence require a workspace retention decision; the synthetic default is a 90-day review point, followed by explicit owner-side `purge-workspace --confirm-organization`. This operation deletes normalized records and private objects, revokes memberships and retains record-free audit metadata.

Maintenance is not exposed through HTTP or run using the application credential. No automated production retention schedule or legal hold policy has been approved. Before real records, settle snapshot/audit retention, incident owner/contact and backup expiry. A restore must reapply recorded deletion/revocation decisions before serving users; old backups must expire under that approved policy.

The local rehearsal backs up the isolated test database and private sources. A separate Neon-to-local rehearsal exports the managed synthetic branch, restores into an isolated database/directory, and compares source bytes, lineage, rules, completed runs and review receipts. `artifacts/pilot-recovery.json`, `artifacts/neon-recovery.json` and the cloud rehearsal artifact record actual results/times. It does not establish a cloud RPO/RTO or service commitment.

## API contract choices

The handoff's future OpenAPI describes the intended security boundary. This implementation narrows ingestion to the user-authorized normalized JSON format instead of multipart arbitrary source uploads. `POST /api/v1/runs` selects one immutable validated `import_id`, whose bundle contains the exact batch/rule/as-of manifest; it does not allow arbitrary independent IDs to be mixed across snapshots. These are deliberate transport constraints, not vendor connectors.

Resource endpoints cover session, workspace, runs, findings/decisions, tasks, members, documents, drafts/approval, imports/status/private source, jobs, audit and reviewed exports. All write bodies forbid extra fields. API schema is available at `/openapi.json`; interactive API documentation is disabled. The supplied handoff contract is unchanged.

## Remaining gates

The local and AWS synthetic environments are separate. AWS provisioning, private S3 operation, real Cognito enrollment/sign-in and the verified Lambda image are exercised; live browser and recovery results are recorded in IMPLEMENTATION_STATUS.md. Production restore targets, representative capacity/billed-cost measurement, real-record evaluation and independent security/accessibility audits remain unproven.

SC-25–29 have synthetic implementation/test evidence. Their real-data pilot acceptance also requires discovery, authorized records, approved hosting/spend, legal/security review and operating contacts. SC-30 independent measurement and SC-31 production approval remain gates. No compliance, certification, recovery revenue, competitive superiority or production-readiness claim follows from this build.
