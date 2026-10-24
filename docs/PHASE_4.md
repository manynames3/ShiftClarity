# Phase 4 · Secured synthetic pilot build

The October 12 request authorized local phase 4 with fictional records. The October 13 follow-up explicitly authorized the synthetic AWS deployment, dedicated role, Lambda/SQS and Mangum. It supersedes the original stage 3 stop and prior AWS preparation-only gate. Customer records, independent measurement and a production launch remain unapproved.

## Working architecture

React retains the original five screens, SVGs and design tokens. `/pilot/` obtains state from one FastAPI service; `/demo/` remains the standalone demonstration. Pilot decisions, source registration, drafts, approvals, imports, tasks and runs are server operations. No browser role switch or reset grants authority.

PostgreSQL stores immutable completed snapshots, source revisions/lineage, rule versions, documents, receipts, jobs and audit events. A restricted runtime login owns no application tables and has no superuser/BYPASSRLS privilege. Organization-scoped tables have forced row-level policies, in addition to endpoint checks. Memberships are provisioned by the operator from verified issuer/subject mappings. Every request rechecks active membership, making revocation effective immediately.

The existing pure TypeScript calculation engine is bundled as a bounded Node process. Python coordinates persistence, not accounting. Rate and money arithmetic stays in the shared decimal engine. Parser processes have a 96 MiB JavaScript heap limit, a 12-second execution timeout and a maximum of two concurrent processes. These limits are process controls, not a measured cloud capacity guarantee.

The integrated worker claims PostgreSQL jobs with row locks and lease tokens. It fences reclaimed workers, retries transient failures up to three attempts, and atomically publishes a completed run with its workspace head and audit event. Reviews lock the head and check run ID, evidence fingerprint and optimistic version; idempotency receipts prevent duplicate writes. A failed legacy canonical import or terminal job retains the prior result and blocks decisions until a validated run is published. Guided draft validation/acceptance errors leave the earlier review available and return actionable diagnostics.

Local development retains the event-driven integrated worker, with no idle database polling. AWS instead uses a FIFO SQS notification and separate Lambda worker. Notifications are sent inside the job-creation transaction; failed sends roll back and early delivery retries until commit. Job-targeted leases and publication protect replay. No recurring wake sweep or always-on process is deployed.

## Identity and sessions

AWS Cognito is the deployed cloud identity service. Authlib is the OIDC client library, not a competing identity service. The local environment remains available, and the separate AWS functions serve the same interface/API against an isolated Neon branch. Local identity uses Keycloak 26.8.0 with a required password/OTP flow and signed AMR claims. Distinct reviewer, author, approver, observer and isolation-test accounts have generated passwords. Test-only authenticator helpers live under `tests/`; the application implements no password or OTP verifier.

Authorization-code sign-in uses PKCE S256, single-use browser-bound state, nonce and verified RS256 issuer/audience/time claims. Cloud startup checks Cognito's required software-token MFA and registered code callback; each login also rechecks required MFA, matching provider subject and verified authenticator enrollment. Classic SSO is cleared before fresh code/PKCE authentication. Local identity tokens must attest OTP execution. Sessions use random HttpOnly/SameSite cookies, hashed database tokens and 15-minute expiry. Cloud cookies use the __Host- prefix, Secure and HTTPS; local HTTP is restricted to loopback. Write requests require both a matching Origin and session CSRF token. Sign-out revokes the application session and redirects through provider sign-out.

## Import boundary

The advanced API accepts a complete normalized fictional JSON snapshot, at most 1 MiB and 2,000 rows per collection, using the exact fields in `src/adapters/custom.ts`. The deployed spreadsheet MVP adds separate guided CSV/XLSX routes for source selection, worksheet/header and confirmed column/value mappings, profiles, independent rate approval and explicit acceptance. Both enter the same immutable canonical import/job pipeline. [ADR 0007](adr/0007-confirmed-spreadsheet-adapters.md) and the [walkthrough](SPREADSHEET_WALKTHROUGH.md) define limits and conventions. The synthetic upgrade was deployed October 23, 2026.

File parsing uses a short-lived Python process with six-second CPU and ten-second wall limits, a 512 MiB address-space limit on Linux, a scrubbed service environment and at most two parser/engine processes. Files are bounded to 1 MiB, archive/XML to 16 MiB and expanded text to 2 MiB. Active workbook content is rejected. These controls are not an OS sandbox or malware certification. A committed workspace-locked budget counts failed parses, previews, mappings, validation and acceptance attempts. Accepted source tables and profiles have forced RLS and immutability controls.

Imports attest to fictional records; IDs must be pseudonymous. No patient/clinical records, PDF/OCR extraction, macros, formulas, unverified live connectors or arbitrary execution are enabled. Explicit aliases are suggestions, never evidence of vendor compatibility.
The server checks content and controls, then registered immutable rules and source excerpts. Importing a claimed approval never grants rule approval. Authors register bounded fictional text separately, propose an explicit predecessor/date/rate, and require a different authenticated approver. Imports may use those approved versions. Reusing a work revision with conflicting content fails; invoice changes get new content revisions and preserved lineage. Identical content reuses the accepted import; reruns never add the same amounts twice.

Safe fixed diagnostics distinguish schema/JSON errors, unsupported fields, source control mismatches, unapproved versions and conflicting revisions without echoing source values. Interrupted quarantine can be retried safely; duplicate validators publish one accepted receipt.

Private storage uses opaque keys, separate quarantine/accepted paths, owner-only local file permissions and authorization-gated downloads. Rejected bytes are deleted and diagnostics contain fixed codes. AWS uses S3 public-access blocks, bucket-owner enforcement, encryption, TLS-only policy and organization-scoped application permissions. Downloads are streamed after authorization; no public or reusable signed file links are issued.

Plain text can still contain sensitive information. Field validation and a synthetic attestation are not automated data classification or legal permission. Do not place real records or personal notes in this build.

## Retention and recovery

Accepted original source objects are available for 30 days; quarantine objects expire within one day in the prepared S3 lifecycle. API source downloads and run requests reject expired imports. `backend.maintenance expire-sources` removes expired local objects and normalized import copies using a separate owner credential. Completed normalized snapshots, review receipts and rule/source evidence require a workspace retention decision; the synthetic default is a 90-day review point, followed by explicit owner-side `purge-workspace --confirm-organization`. This operation deletes normalized records and private objects, revokes memberships and retains record-free audit metadata.

Maintenance is not exposed through HTTP or run using the application credential. No automated production retention schedule or legal hold policy has been approved. Before real records, settle snapshot/audit retention, incident owner/contact and backup expiry. A restore must reapply recorded deletion/revocation decisions before serving users; old backups must expire under that approved policy.

The local rehearsal backs up the isolated test database and private sources. A separate Neon-to-local rehearsal exports the managed synthetic branch, restores into an isolated database/directory, and compares source bytes, lineage, rules, completed runs and review receipts. `artifacts/pilot-recovery.json`, `artifacts/neon-recovery.json` and the cloud rehearsal artifact record actual results/times. It does not establish a cloud RPO/RTO or service commitment.

## API contract choices

The handoff's future OpenAPI describes the intended security boundary. The canonical JSON API remains available. The separately authorized spreadsheet workbench uploads raw CSV/XLSX bytes, confirms their meaning and normalizes them into that same canonical contract. `POST /api/v1/runs` selects one immutable validated `import_id`, whose bundle contains the exact batch/rule/as-of manifest; it does not allow arbitrary independent IDs to be mixed across snapshots. These are deliberate transport constraints, not vendor connectors.

Resource endpoints cover session, workspace, runs, findings/decisions, tasks, members, documents, drafts/approval, imports/status/private source, jobs, audit and reviewed exports. All write bodies forbid extra fields. API schema is available at `/openapi.json`; interactive API documentation is disabled. The supplied handoff contract is unchanged.

## Remaining gates

The local and AWS synthetic environments are separate. AWS provisioning, private S3 operation, real Cognito enrollment/sign-in and the verified Lambda image are exercised; live browser and recovery results are recorded in IMPLEMENTATION_STATUS.md. Production restore targets, representative capacity/billed-cost measurement, real-record evaluation and independent security/accessibility audits remain unproven.

SC-25–29 have synthetic implementation/test evidence. Their real-data pilot acceptance also requires discovery, authorized records, approved hosting/spend, legal/security review and operating contacts. SC-30 independent measurement and SC-31 production approval remain gates. No compliance, certification, recovery revenue, competitive superiority or production-readiness claim follows from this build.

## Spreadsheet MVP retention and reports (local)

Raw file previews are readable only by authorized source-read roles while staged and are removed at acceptance. Quarantine originals/abandoned previews expire after one day; accepted original bytes after 30 days. Derived immutable selections, rule/source/run/review evidence persists until the owner purge. Profiles remain until removed or purged. The maintenance tool covers all new tables, locks sessions before files, commits download-denial tombstones before byte deletion and retains object keys for retry after storage failure. Run the operator expiry command for database/local-file cleanup; an S3 lifecycle alone does not redact derived evidence.

XLSX/PDF downloads use the current reviewed workspace snapshot, all finding states, coverage gaps and explicit source/rate references. Raw evidence fingerprints are hashed. Worker identity fields and reviewer notes are omitted by default; notes require explicit opt-in. Literal Excel cells, escaped PDF text, private/no-store responses, audited downloads and two bounded report encoders protect the new output path. Current-run-only reports must be downloaded before advancing to another period. No customer retention policy, real-data permission or live MVP deployment follows from these synthetic controls.
