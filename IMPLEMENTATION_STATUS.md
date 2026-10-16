# ShiftClarity implementation status

## October 15 standalone demo product polish

Working branch: `codex/demo-product-polish`. This request applies to the standalone `/demo/` experience; the calculation engine and canonical fixture results remain unchanged.

- **Item 1 — demo framing:** completed. Added one dismissible fictional-data disclosure with reset, session-only dismissal, and removed the old persistent demo labels. Baseline “before” screenshots are captured for the final image set.
- **Verification:** `npm test` (70 passed), `npm run build` (passed), `npm run test:e2e` (22 passed).
- **Item 2 — navigation:** completed. Desktop now has one four-link sidebar; mobile uses the same routes in a hamburger drawer. Evidence remains a finding detail with a Workspace breadcrumb. About and parent-brand copy moved to the content footer.
- **Verification:** `npm test` (70 passed), `npm run build` (passed), `npm run test:e2e` (23 passed, including desktop/mobile navigation).
- **Item 3 — workspace hierarchy:** completed. Added the exact-decimal potential-underbilling headline, unique affected-shift count, findings-first layout, compact summary strip, default priority/state and largest-impact ordering, and sortable difference/facility/state headings.
- **Verification:** `npm test` (72 passed), `npm run build` (passed), `npm run test:e2e` (23 passed). At 1920×1080 the findings panel ends at y=733 and page width is 1920; at 390×844 page width remains 390. Both views were inspected.

## October 13 Cloudflare full-pilot checkpoint

The user selected the full signed-in pilot at https://shiftclarity.pages.dev/. A fixed-origin Pages Worker forwards to the existing AWS gateway, preserves secure cookies/Origin, avoids private caching and redirect following, and supplies a private edge credential. Backend exact gateway-host/credential checks precede the existing user permissions. Cognito callback/logout URLs use Pages. Terraform changed only its client and the two function images/environments in place; no data resource was replaced. No paid plan or additional Secrets Manager secret was added.

Actual verification: two proxy tests, two gateway tests, frontend build, final Lambda runtime emulator, matching deployed digests, callback settings, anonymous/direct-origin/preview denial, zero drift, and real-browser authenticator sign-in/import/private download/SQS publication/persisted reload all passed. The sample again computed 12 checked records and $1,760.00 potential underbilling. The rendered signed-in product was inspected. Full original backend tests were blocked by local peer authentication, so their earlier results are not presented as rerun. See docs/CLOUDFLARE.md, ADR 0006 and ignored artifacts/cloudflare-browser-verification.json.

Resource-based idle estimate: approximately $0.79/month baseline before credits/free allowances, with small variable requests/storage; budget about $0.60–$1/month at low use. Cloudflare adds no separate subscription within the shared Free allowance. This is not a measured monthly bill or a hard cap. Private sign-in instructions now use the Pages URL.

## October 13 public documentation checkpoint

Public `manynames3/ShiftClarity` was explicitly approved by the user. Publication content includes the application source, unchanged handoff, an outcome-led README, four actual synthetic product screenshots, five ADRs, C4 context/container/component diagrams, and an import/publication sequence. Documentation validation checks 19 Markdown files, 114 local links/images and four Mermaid diagrams. All original 84 handoff hashes still match; the 20 fixture tests were rerun and passed. A public-source audit and Gitleaks scan found no real credentials in the selected files; private configuration/state/backups and raw artifacts are excluded.

Fresh-checkout review found generated-state assumptions in the local launcher. It now builds the shared engine before database seeding and creates the template output directory. Syntax and isolated fresh-workspace engine/template checks passed, including the canonical $1,760.00 potential-underbilling result. Full local service startup was not rerun, and no pilot accounts/databases/cloud resources were changed by these fixes. The existing hosted standalone demo returned HTTP 200 and provides the GitHub website destination. App/data acceptance limits remain as recorded below.

Source: ShiftClarity Build Kit v1.0, prepared October 12, 2026. All 84 supplied hashes matched. The kit is preserved unchanged under ./handoff; the original ZIP was also extracted to the requested parent handoff/ directory. Dedicated app workspace: ShiftClarity/.

## Outcome

**Phase 4 synthetic pilot: deployed on AWS with Cognito, private S3 and Neon.** One FastAPI backend serves the branded React app; actual local OIDC/MFA identities, restricted PostgreSQL roles/forced RLS, private normalized imports, immutable revisions/runs/rules/documents, optimistic reviews, durable jobs/replay, source/draft authoring, retention tools and restore rehearsals are working. AWS Lambda/HTTP API/SQS, real Cognito MFA and private S3 are deployed in the approved account. The eight live workflow checks and restore rehearsal passed. See the October 13 checkpoint below.

**Stages 0–3: working local demo, tested.** All SC-01–24 demo behaviors implemented with the SC-17 scope extension described below. Canonical output computes from input records and exactly matches the independent oracle: 14 records / 8,880 minutes received; 12 / 7,440 evaluated; 6 aligned, 6 flagged, 1 abstained, 1 not evaluated; +200.00 and +1560.00 financial findings; two unknown-value coverage tasks. No recovered/collected metric.

**User-authorized extension:** a separate own-data local preview supports manual USD standard-RN entry and normalized JSON bundle import. It validates types, fields, source references, source totals, limits and approval metadata, then requires explicit acceptance before replacing the visible run. It never uploads the file. The canonical fixture loader remains content-restricted. Neither preview nor DEMO roles establish production authorization.

## Checkpoints and evidence

| Checkpoint | Changed areas | Acceptance | Actual verification |
|---|---|---|---|
| 0 | handoff copy, root AGENTS, DECISIONS/status, dedicated directories | Scope/read/data/visual lock | 84 file hashes; 20 supplied fixture-integrity tests. Supporting docs, contracts, synthetic records, golden cases, acceptance spec and reference screens read. |
| 1 | package/config/lock, domain types/engine, adapter, shell/Workspace/components, original assets and CSS | SC-01–11, SC-24 domain/shell | First 34 domain tests plus workspace interaction; exact oracle fields/partitions; production build. 1440/390 shell captures inspected with no page overflow. |
| 2 | demo state, Evidence/Inputs/Rules/Coverage/App, dialogs, decisions, roles, scenarios, exports | SC-12–21 | 50 unit/component tests at gate; eight initial browser workflow/keyboard cases and five targeted accessibility scans. Five routes at 1440/390 captured/inspected. Focus trap/restore, contrast, rule fields and monetary wrapping corrected. |
| 3 | additional negative/property/browser tests, own-data adapter/preview, screenshot suite, final lineage/review corrections, delivery docs | SC-01–24; own-data extension | Final checks below. All G01–G20 exercised in engine/demo tests. |

### Final checks actually run

- `npm run test:fixtures`: **20 passed**.
- `npm test`: **69 passed** in the final rerun recorded in artifacts/final-verification.txt.
- `npm run build`: TypeScript check and Vite production build **passed**; final rerun recorded below.
- `npm run test:e2e`: **21 passed** in installed Google Chrome, isolated test profiles. Includes six axe route checks (core five plus custom preview), full decision/reopen/reset journey, negative import, independent rule approval/rejection, local tasks, CSV download, keyboard focus/trap/return, mobile review and successful own-template import with no non-GET requests. Final rerun passed and is recorded in artifacts/final-verification.txt.
- `npm run screenshots`: **81 captures**, no browser page errors or horizontal page overflow at 1440×1000, 1280×900, 1024×900, 390×844 and 320×844, plus a CSS 200% zoom state. Covers baseline/missing evidence, empty filters/imports, incomplete/partial coverage, failed run, denial/approval, confirmation/dialog and custom preview.
- Visual inspection: all capture layouts reviewed through per-width inspection sheets; core desktop/mobile evidence, rules, workspace and custom preview additionally inspected at full resolution. Table scrolling is contained. This is not a pixel-diff certification or a manual review of every pixel of all 81 files.
- Production bundle scan found no independent oracle-only fields/text after excluding expected_results.json from eager fixture raw imports. Runtime results are computed.
- Local dependency installation audit reported zero vulnerabilities; no claim of a comprehensive security audit.

Captured evidence: artifacts/screenshots/, artifacts/screenshot-manifest.json, artifacts/e2e-results.json. The app preview is running locally at http://127.0.0.1:5178/. Exact commands and walkthrough are in README.md.

## Deliberate differences and limits

- Design-reference toolbar becomes a demo navigation/reset toolbar. Brand board/product intro remain references, not marketing routes. Original SVGs, palette, shell widths and evidence hierarchy are preserved.
- Actual supplied source text, source/line IDs, reason codes and local history are displayed. Extra run/control/scenario details are functional additions and may increase page height. Mobile comparison values use 18px to remain intact; 320px comparisons stack. No generic restyle or fake analytics.
- Canonical fixture-file selection validates the selected supplied file then reloads the complete fixture snapshot; it does not claim incremental/vendor ingestion. Own-data import is the separately approved schema-bound JSON path, not arbitrary vendor CSV/PDF/OCR conversion.
- The original standalone demo/preview remains memory-only. The separate phase 4 pilot now persists through FastAPI/Neon with verified local identities, durable jobs/audit and private local source storage. The separate AWS pilot now uses Cognito/S3 and its own Neon branch; original local history remains intact.
- Plain-text source excerpts and review notes must contain only allowed minimized content; schema validation is not a clinical-data classifier. Do not enter sensitive notes. Raw documents/worker names/contact fields are not exported.
- Reordered/identical sources preserve decisions. Relevant amount, source or rule changes reopen them and preserve history, including regrouping/direction changes. Failed runs retain prior completed results and block review until refreshed.
- Independent Claude review, screen-reader user testing, production accessibility/security audit and real-data evaluation were not run. Synthetic cloud integration and recovery are documented below. Repowise has no registered index for this new workspace; no unrelated index/repository was altered.

## October 12 local phase 4 checkpoint and actual evidence

The user explicitly authorized this synthetic phase 4 build and approved its backend libraries. The conditional Neon request was resolved after verifying the connected organization reports Free. A new isolated project and application branch were created; no existing customer project was modified.

- **Backend:** 34 PostgreSQL/API/security/recovery tests passed. Covers object/action authorization, identity claims, browser-bound PKCE/nonce/state, single-use callbacks, session expiry/revocation, CSRF, self-approval, optimistic conflicts, immutable accepted imports/rules/runs/audit, parser/content/size limits, private storage, source controls, failed-import retention, concurrent quarantine recovery, idempotency, actual killed-worker rollback/replay, retry limits, retention/purge and backup restore.
- **Shared domain/component:** 69 tests passed after the server adapter/context changes. Calculation authority remains the same pure exact-decimal engine; the Node I/O adapter is outside the domain directory.
- **Original fixture/standalone regression:** 20 supplied fixture tests and 21 browser tests passed. The original handoff remains unchanged.
- **Real-provider browser journey:** 8 tests passed against local PostgreSQL, then all 8 passed against the managed synthetic Neon branch. Includes individual required-OTP sign-ins, persisted decisions after reload, real uploads/jobs/private downloads, read-only restrictions, rejected upload diagnostics/stale results, provider sign-out, independent approval, denied outsider, new source/draft authoring and accessible responsive routes.
- **Additional Neon import check:** one targeted live check passed after batching revision writes; amounts, coverage and review history were preserved across a new immutable run.
- **Build/infrastructure:** TypeScript/Vite and shared-engine builds passed. Terraform initialization/format/validation passed with locked AWS provider 6.68.0. No Terraform apply, AWS image push or application deployment ran.
- **Restore:** local test database/source restore matched. A separate Neon-to-isolated-local restore matched 4 imports, 24 source revisions, 72 lineage links, 5 documents, 4 approved versions, 3 jobs, 4 completed runs, the workspace, 28 audit events and 4 write receipts; 8 private source objects matched. The recorded rehearsal took 5.196 seconds. No production RPO/RTO is inferred.
- **Visual:** 25 loaded route captures across 1440/1280/1024/390/320 widths, plus authoring mobile capture. The initial capture waits were corrected to wait for the actual workspace and completed history fetch instead of loading/temporary empty states. Desktop/mobile sheets and representative full images were inspected; no page overflow or browser page errors in the final route check. Full axe checks passed on the five main routes and source authoring. Existing phase 3 zoom/state captures remain historical evidence.

Evidence: artifacts/phase4-backend-tests.txt, artifacts/phase4-domain-tests.txt, artifacts/phase4-browser-tests.txt, artifacts/phase4-neon-browser-tests.txt, artifacts/neon-bulk-import-check.txt, artifacts/phase4-build.txt, artifacts/pilot-recovery.json, artifacts/neon-recovery.json and artifacts/pilot-screenshots/.

## October 12 running environment and limits

Pilot: http://127.0.0.1:5180/pilot/. Backend/frontend and Keycloak run locally; PostgreSQL persistence uses Neon project lively-field-50384173, application branch br-holy-block-b75wbmjb in AWS us-east-1. The seeded base branch is retained and its unused compute suspended. Runtime credentials are ignored, owner-only local files. Both endpoints are capped at 0.25 CU. The observed branch storage limit is 512 MiB, with six-hour history. Free-plan suspension settings could not be edited; manual suspension/resume is tested rather than automatic behavior assumed.

HTTPX transport deprecation warnings remain in the pinned Authlib/Starlette test environment, plus a Mangum event-loop deprecation warning in local tests. Docker became available for the October 13 deployment. No independent security audit, screen-reader user study or real-data evaluation is claimed. Repowise still reports Repository not found for ShiftClarity; no unrelated index was updated. Manual indexing with repowise init --yes would be needed for that tool.

SC-25–29 have synthetic local/cloud implementation evidence; full real-data acceptance still requires discovery/source semantics, authorized data-use/legal scope, operating contacts and retention/backup policy. SC-30 independent measurement and the stage 6 productization gate remain unmeasured/unapproved. The build makes no production-ready, HIPAA, SOC 2, superiority, savings or collected-money claim. No paid Neon upgrade, external communications, commit or push occurred. AWS deployment/spend was explicitly approved on October 13 and uses minimal serverless resources.


## October 13 · verified synthetic AWS deployment

Live app: https://4p30g92j37.execute-api.us-east-1.amazonaws.com/pilot/. Account 636305658578, us-east-1; root can view the account-owned resources. The dedicated shiftclarity-deployer role manages the pilot. Initial credentials established/maintained only that role; no DealFinder resource or long-lived key was created. The user approved Mangum/Lambda/SQS in response to the near-zero-idle preference. No provisioned Lambda capacity, App Runner instance, VM, load balancer, NAT gateway, custom domain, SMS or paid Neon upgrade.

- Verified x86 container: actual AWS runtime emulator at 512 MiB/0.25 CPU, nonroot UID 10001, read-only root, restricted Neon connection, branded interface, denied unauthenticated APIs/host mismatch, and shared Node calculator. The deployed functions use 1024 MiB for CPU availability; no idle reservation. Image ID/digest and scan artifacts identify the actual build.
- Backend: **52 passed**, including cloud token/enrollment/subject checks, host-bound cookies, FIFO delivery/replay/rollback, public-assets-only caching, and rejection-attempt idempotency. The repeated rejected-content bug was reproduced with a failing test, fixed, and exercised on AWS.
- Domain/component: **70 passed**, including a deferred server review that remains visibly pending and blocks duplicate submission. Final TypeScript/Vite build and targeted pending-review check passed after the wording-only correction. Exact decimal calculation authority is unchanged.
- Original fixture/demo regression: **20 fixture tests and 21 browser tests passed** after pending-review changes. No original handoff file was changed.
- Actual AWS journeys: **8 passed in 2.1 minutes** with real Cognito OTP enrollment/sign-in, persisted review/reload, S3 originals and SQS publication, read-only denial, repeated rejection/stale-state recovery, provider sign-out, independent approval, denied outsider, source/draft registration, and full responsive/axe routes. Failures in earlier runs are retained as diagnosis artifacts; the final complete run passed. This run predates only the final wording correction, which received TypeScript/build, targeted component, container and anonymous API/resource checks. The final authenticated manual recheck stopped when the user took control and ended the browser task.
- Visuals: **26 cloud captures** at 1440×1000, 1280×900, 1024×900, 390×844 and 320×844. No page errors/horizontal page overflow and no axe violations in the main five routes and source authoring. Manual AWS workspace and branded Cognito sign-in were inspected. These are synthetic usability checks, not a manual accessibility certification.
- Private S3: public-access blocks, AES256, TLS-only policy, expiry and organization-scoped runtime access verified. Anonymous retrieval of an existing source returned **403**. Authorized source download passed in the live workflow. Confidential responses remain no-store; only content-hashed public build assets are cached.
- Cloud restore: Neon public schema and S3 originals restored into the dedicated local shiftclarity_aws_restore database/directory. Exact financial/state/role row hashes and **7 source objects matched**, including 3 imports, 24 source revisions, 48 lineage records, 5 documents, 4 rule versions, 7 jobs, 8 completed runs, 62 audit records, 13 receipts and 4 memberships. Recorded rehearsal: **8.085 seconds**. No live branch was overwritten or production RPO/RTO inferred.
- ECR basic OS scan: completed with **no reported findings** after applying available AL2023 security updates. This is not an application/third-party dependency audit.
- Neon idle behavior: cloud compute was actually observed idle after suspension at 05:39:16 UTC without an explicit suspension call. Metadata still reports suspend_timeout_seconds=0; the observation confirms idle suspension but not an exact timeout guarantee. Final deployment health access resumed successfully; no exact cold-start or suspend interval commitment is inferred.

Cloud resource metadata, exact image equality, MFA/callbacks, empty queue/dead-letter state and zero Terraform drift passed and are recorded in artifacts/aws-final-resources.json and aws-final-drift.txt. Private sign-in details are in .local/AWS_SIGN_IN.md with mode 600, not in public artifacts.

Evidence: artifacts/aws-backend-tests.txt, aws-domain-tests.txt, aws-fixture-tests.txt, aws-demo-regression-tests.txt, aws-browser-tests.txt, aws-e2e-results.json, lambda-container-verification.json, aws-image.json, aws-image-scan.json, aws-s3-controls.json, aws-recovery.json, aws-neon-idle.json, aws-final-drift.txt and aws-screenshots/.

Actual preflight account state was PAID/ACTIVE with $110.83 credits; credit expiry and eventual billed usage remain unverified. One secret/storage/logging and any exhausted shared free allowances can incur small charges. The $5 account budget and queue alarm have console visibility but no notification recipient or hard spending cap. No customer-data authorization, production certification, independent measurement or stage 6 productization claim is made.
