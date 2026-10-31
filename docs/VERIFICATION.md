# Synthetic release verification

## October 24, 2026 · Varied fictional billing output

The [richer PDF/Excel example and source kit](../public/examples/realistic-billing/README.md) were generated through the real local FastAPI import, mapping, separate-account rate approval, durable reconciliation, review-decision and report-download endpoints. Only the disposable local test database was used; no live workspace was overwritten. The original compact quickstart remains intact. No report formatting or calculation shortcut was introduced.

The new scenario plus four existing report regressions passed (**five tests**). Assertions compare independently authored amounts for all eight discrepant shifts: $18.75, $28.75, $72.50, $580, -$33.25, $54, $139 and $12. Verified totals: 18 shifts/136 hours received, 16 shifts/124.5 hours evaluated, eight aligned records, seven findings, two gaps, $8,626 expected, $7,754.25 evaluated allocations, $8,328.25 all posted, $905 underbilling and $33.25 overbilling. The $1,020 original/-$1,020 credit/$966 rebill chain contributes $966 net; the voided $800 line is excluded. Callback/pending-time gaps have no estimate.

The exported workbook contains all 18 work calculations and 45 source-row references, literal cells, three confirmed findings, one evidence request and three pending findings. Default worker IDs and reviewer notes were verified absent. All five PDF pages were rendered and inspected; headers/footers and pagination remain present. Curated outputs are `docs/examples/realistic-billing-review.pdf` and `.xlsx`, with a reproducible CSV kit alongside them. Detailed test evidence is ignored `artifacts/realistic-billing-test.txt` and `artifacts/reports/realistic-billing-results.json`. No new cloud deployment or real-data accuracy claim is made for this fixture addition.

## October 23, 2026 · Hosted spreadsheet MVP

The user explicitly authorized push/deploy after local MVP acceptance. The spreadsheet workflow is live at [the assigned-account pilot](https://shiftclarity.pages.dev/pilot/). Application source is `5d3e324`; both Lambda functions are Active/Successful at `sha256:8114bdfc526c79875beead7f116811a432477a9910156b9d7da5205d818e1eba`. Pages release `d39a4aa3` serves the updated landing copy from `b517803`. The app's JS/CSS assets matched the local build bytes. No new cloud service or paid upgrade was introduced.

| Check actually performed for this release | Result |
|---|---|
| Database migration and recovery | Restored the existing Neon branch and **13 S3 originals** into an isolated local rehearsal; state/object hashes matched. Rehearsed migrations **004/005**, then applied them owner-side to the authorized synthetic branch. Running migrations twice was idempotent; existing record hashes were unchanged. |
| Packaging | AMD64 Lambda runtime-emulator and restricted-Neon checks passed. UID 10001/read-only/network-isolated smoke covered spreadsheets, independent rate approval, shared calculations and both report encoders. Registry manifest type is checked before selecting an image for deployment. |
| Backend regressions | **98 passed** after the final calculator timeout/error-handling correction, including the new interrupted-approval regression. The focused recovery/approval suite also passed all eight cases. |
| Local browser | The full two-period MVP journey passed again after the backend correction; TypeScript passed. Three landing browser checks and all four edge-routing tests passed for the copy release. |
| Real Cognito workflow | Signed in with distinct MFA-protected reviewer and approver accounts. The live fictional XLSX journey obtained independent approval, accepted private sources, published a durable run, derived **$200 potential underbilling / 6 of 8 work records**, saved a review and retained it after reload. |
| Secure sources and roles | The authorized S3 original matched the supplied XLSX bytes exactly and carried no-store. Missing CSRF, an approver attempting an import, and an approver downloading work originals were denied. |
| Unassigned identity | A separate real Cognito MFA account without workspace membership was denied after sign-in. |
| Repeat period | Live CSV reuse of the saved work profile required explicit mapping of the new RG value. Unchanged approved rates were reused; the second period began with a fresh Needs review decision. |
| Loaded-screen visual checks | A repeat live journey passed in **48.8 seconds**. Source cards, fonts and logos loaded before captures/checks. Actual light desktop/mobile captures were inspected; accepted import had no overflow or automated axe violations at 1440/390/320px. Open mappings and the report workspace also passed light/dark scans. The same-period retest used All findings to inspect retained decisions. |
| Actual report downloads | Both formats downloaded through the hosted workspace. Excel had eight literal-cell sheets with no formulas; default worker references and reviewer notes were omitted. The three-page PDF was rendered and inspected, including confirmed review, $3,305 expected / $3,105 evaluated invoiced and $3,775 all-posted amounts. |
| Boundary controls | Anonymous workspace/import/report APIs returned 401. Direct gateway and preview-host access returned 403. Cognito mandatory TOTP/callback, private encrypted S3, restricted Neon role, verified client TLS, forced RLS and unscoped-row denial were read back. The existing alert subscription remained confirmed. |
| Infrastructure | Reviewed plans changed only the web/worker image digests. Final Terraform plan exited **0 with no drift**; job and dead-letter queues were empty after the completed journey. |
| Post-release restore | Extended the existing rehearsal to include spreadsheet tables and unexpired originals. All **15 tables**, including six source selections, 18 file records and four mapping profiles, matched after isolated restore; **34 private S3 objects** matched byte hashes. The rehearsal took **7.92 seconds**, establishing no production recovery objective. |

The first registry upload contained an OCI index with an attestation, which Lambda rejected; both functions stayed on the prior image. Rebuilding with `--provenance=false --sbom=false` produced a compatible single manifest, now guarded by the upload script. The first hosted rate calculation then exceeded the former 12-second subprocess limit; retrying the same selection approved its three rates. The final image allows a bounded 20-second calculator start inside the 29-second HTTP limit and returns retryable 503 for interruptions, preserving sources, versions and prior results. A failing local regression was recorded before the fix and passed afterward. No approval or integrity guard was bypassed.

Evidence remains in ignored `artifacts/mvp-migration-*.json`, `mvp-release-backend-final.txt`, `mvp-live-browser-final.txt`, `mvp-live-browser-visual-final.txt`, `mvp-live-outsider.txt`, `mvp-postdeploy-recovery.json`, `mvp-live-resources.json`, `mvp-live-public-origin.json`, actual report downloads and private Terraform logs. Earlier 90 domain/component, 44 original browser and 20 fixture results below are retained as earlier MVP evidence, not relabeled as fresh cloud runs. Representative customer accuracy, capacity, recovery objectives, incident/data-use ownership and historical report navigation remain outside this synthetic release.

## October 23, 2026 · Spreadsheet adoption MVP (local only)

This checkpoint records the completed local implementation before the separately authorized hosted release above. At this checkpoint it had **not** been deployed to AWS/Neon/Pages. The earlier hosted release evidence below remains historical.

| Check actually performed | Result and scope |
|---|---|
| Backend / local PostgreSQL | **97 passed**: original regressions plus bounded spreadsheets, profiles, cross-workspace endpoints, identity/role/CSRF denials, immutable acceptance, rate-approval races, failed copies/retries, revision conflicts, quotas, retention/purge and reports |
| Domain / component | **90 passed**; original exact-money/oracle behavior retained, with explicit imported hourly components and historical authorization tests |
| Original handoff | **20 integrity checks passed**; handoff unchanged |
| Original browser regressions | **44 passed**, including light/dark accessibility, mobile layouts, review/reopen and signed-in header widths |
| Full MVP browser journey | **Passed**: first-period XLSX, confirmed/saved mappings, second-account approval, acceptance/queue publication, $200 derived difference, 6/8 evaluated work, persisted decision, both downloads, and second-period CSV with new RG mapping and fresh review state |
| Responsive/accessibility | No overflow and zero automated axe violations on the new import view at 1440/390/320px; open mappings and report workspace also passed in light/dark themes; actual desktop/mobile captures inspected |
| Report correctness | Four integration tests passed; current decisions, both financial directions, evaluated versus all-posted totals, all finding states, original hashes/lineage, literal Excel cells, escaped PDF markup, default note/worker omission and stale warnings |
| Report visuals | Actual browser-download PDF rendered and all three pages inspected; branding, embedded fonts, readable tables, row references and pagination checked. Curated XLSX/PDF examples and product captures are published. |
| Declared capacity | Synthetic adapter/engine/XLSX/PDF check passed for **500 work rows / 1,000 invoice lines** within stated byte/response bounds; no latency SLA or representative Lambda capacity claim |
| Container | Local AMD64 Lambda image built; **nonroot UID 10001, read-only filesystem, no network** parser/shared-engine/XLSX/PDF smoke passed. No image push. |
| Public landing compatibility | Three existing landing browser checks and static Pages build passed locally; no deployment |
| Independent opinion | Claude supplied read-only plan and code reviews; Codex verified/fixed concrete findings and ran tests. See [disposition](CLAUDE_MVP_REVIEW.md). |

The MVP browser test uses real local API authorization and disposable PostgreSQL, but provisions short test sessions directly. It does **not** retest the Cognito provider. No new real-provider/cloud, restore, monthly-cost or customer-data evaluation was performed. Existing provider/backup evidence below is not relabeled as a new test.

The final visual pass corrected a wrapped PDF Minutes header, long fractional-hour display, confirmation navigation and setup checkbox alignment. Earlier failing tests also exposed raw canonical fingerprints in reports, accepted-preview UI assumptions, and saved-profile new-value behavior; they were corrected and the affected checks rerun. Framework deprecation warnings remain (Authlib/Starlette httpx compatibility and a Mangum event-loop warning); they did not fail tests and no unapproved dependency migration was introduced.

Ego confirmed the local page and 1920px bounds but its screenshot capture timed out; the published images are actual captures from the passing isolated Chrome tests. Its task was finished; an announced browser update was not applied. The Pages project was read back with **Git Provider: No** before source publication; GitHub publication does not deploy this direct-upload project.

See the [walkthrough](SPREADSHEET_WALKTHROUGH.md), [MVP acceptance checklist](../ACCEPTANCE_CHECKLIST.md#spreadsheet-adoption-mvp--october-23-2026), [capability limits](BILLING_CAPABILITIES.md), [sample reports](examples/fictional-billing-review.pdf) and [remaining gates](PILOT_GATES.md). Current-run-only report navigation, whole-minute time, stable reference codes and explicit flat hourly terms are documented limits.


## October 16, 2026 readiness checkpoint

The current synthetic pilot is deployed at https://shiftclarity.pages.dev/pilot/. The manual [staffing exercise](../examples/synthetic-healthcare-staffing/README.md) includes the exact bundle exercised by the live import journey and a separate expected-results file.

| Area | Recorded result |
|---|---|
| Domain / components | 82 tests passed |
| Local browser | 44 cases passed: the standalone suite and a signed-in header regression at seven widths |
| Backend / PostgreSQL | 54 tests passed during this readiness work |
| Original handoff | 20 integrity checks passed; original files remain unchanged |
| Live AWS browser | All eight Cognito/MFA journeys passed against the final deployed image |
| Responsive / accessibility | Five signed-in routes checked at 1440/1280/1024/390/320px; desktop axe scans, mobile authoring scan and selected actual captures inspected |
| Container | Final AMD64 image passed actual Lambda runtime-emulator, restricted Neon, shared engine, UI, host validation, nonroot/read-only and anonymous-denial checks |
| Deployment | Both functions Active/Successful at the verified digest; Cloudflare bundle matched the local production build; zero Terraform drift and empty job/dead-letter queues |
| Alerts | Owner-confirmed email subscription active; budget thresholds/subscribers, SNS service permissions and failed-job alarm wiring read back successfully |

The final pilot header correction reran the frontend tests/build, container checks and full live browser suite. Backend and fixture checks ran earlier in this readiness work, with no subsequent backend/fixture changes. The $5 account-wide budget warns at 80% actual and 100% forecasted spend; it does not cap spending. No artificial failure or spend event was sent to test notification delivery.

Final deployed image: `sha256:7a3c8863e3b10819914339322a893d764e463fb1b3b325de2656d3a4a54f27e0`. Sanitized local reports are `artifacts/readiness-resources.json`, `readiness-public-origin.json`, `aws-e2e-results.json`, `e2e-results.json` and `lambda-container-verification.json`; detailed plans, credentials and the alert recipient remain private.

## October 13 original release evidence

The subsequent full Cloudflare-origin change has its own [recorded checks](CLOUDFLARE.md#recorded-verification--october-13-2026). Earlier full-suite results below remain the original release evidence. The address-change checks exercised real authenticator sign-in, private import/download, durable publication and reload, in addition to focused host/proxy tests and container verification.

Release checkpoint: **October 13, 2026**. These results describe the fictional phase 4 pilot. They are recorded results from the implementation/deployment work, not a claim that every test was rerun for this documentation update.

## Checks actually performed

| Area | Recorded result | What was exercised |
|---|---|---|
| Backend / PostgreSQL | 52 tests passed | Identity/session validation, permissions, independent approval, RLS, immutable evidence, imports, optimistic conflicts, idempotency, worker failure/replay, retention and recovery |
| Domain / components | 70 tests passed | Exact decimal calculations, effective dates, signed allocations, coverage partitions, review history and pending save behavior |
| Original handoff | 20 integrity tests passed | Supplied fixture controls; all 84 original handoff file hashes matched at extraction |
| Standalone browser | 21 cases passed | Review/reopen/reset, rule approval, negative/custom imports, exports, keyboard/dialog focus, mobile layouts and automated accessibility checks |
| Live AWS browser | 8 journeys passed | Actual Cognito OTP, persisted reviews, private S3 imports/downloads, SQS publication, denied roles/membership, stale/recovery guards, separate approval and source authoring |
| Responsive cloud UI | 26 captures | Five product routes at five widths, plus mobile authoring; selected captures inspected |
| Container | Actual Lambda runtime emulator passed | Same engine, restricted database access, UI/API, anonymous denial, nonroot/read-only execution; web and worker deployed image digests matched |
| Restore | Isolated rehearsal matched | Neon database and seven S3 original objects restored locally; source bytes, lineage, rule/run history and review state compared |
| Deployment | Zero Terraform drift recorded | Deployed functions, callbacks, required MFA, private S3 settings and queue state inspected |
| Image OS scan | No findings in final ECR basic scan | Operating-system package scan of the deployed image; this is not an application or dependency audit |

The eight AWS journeys passed before a final wording-only UI update. That update passed TypeScript/build, the targeted component check, container execution, and anonymous API/resource checks. The additional authenticated manual recheck ended when the user took control of the browser, so it is not counted as completed.

The cloud database was observed idle without an explicit suspend call. That observation establishes no exact suspension timeout or zero-cost guarantee. The restore rehearsal establishes no production RPO/RTO or service commitment.

## Evidence and reproduction

The repository includes the test source, [development instructions](DEVELOPMENT.md), immutable original handoff, [acceptance checklist](../ACCEPTANCE_CHECKLIST.md), and [product screenshots](images/README.md). Runtime logs, detailed deployment reports, browser traces, backups and sign-in setup files stay local and are excluded from publication.

Recorded private/local report filenames include `AWS_DEPLOYMENT_QA.json`, `aws-backend-tests.txt`, `aws-domain-tests.txt`, `aws-fixture-tests.txt`, `aws-demo-regression-tests.txt`, `aws-browser-tests.txt`, `lambda-container-verification.json`, `aws-final-drift.txt`, and `aws-recovery.json` under `artifacts/`. They are generated evidence, not repository fixtures or embedded credentials for reproducing cloud access.

## Limits

SC-01–24 have demo implementation/test evidence. SC-25–29 have synthetic backend/cloud evidence, with real-data policies and operating requirements still gated. SC-30 independent measurement and SC-31 production approval remain incomplete.

Real customer records, authorized source semantics, representative capacity/cost measurement, independent accessibility/security audits, production restore targets, incident response commitments, and approved retention/backup policies remain unverified. See [pilot gates](PILOT_GATES.md) and the [evaluation plan](EVALUATION_PLAN.md).

No recovered/collected-money, competitor-superiority, legal compliance, certification, or production-readiness claim follows from the synthetic checks.


## October 17, 2026 · Approved public landing page

The user approved the Claude/Codex desktop/mobile concept, then explicitly requested push and deployment. The same bright editorial layout, actual fictional evidence screenshots, $200 worked example, native source-tracing controls, coverage explanation and demo-first navigation are integrated as standalone `landing/` files. `/` and `/landing/` are served directly from Cloudflare Pages; the existing demo, pilot, API and Cognito paths retain their fixed AWS proxy. No application calculations, permissions, backend, database, Lambda image, dependency or paid resource changed. The original handoff and historical untracked design work remain untouched.

Acceptance mapping: SC-01 truthful synthetic scope and unknown collection; SC-21 functional demo/pilot/evidence links; SC-22 keyboard, responsive, bright default and reduced motion. This adds the separately approved public entry point and makes no measured conversion or production-readiness claim.

Verification before deployment: TypeScript/Vite production build and all 82 unit/component/domain tests passed; four Worker routing/security tests passed. Three landing browser checks passed, covering 320/390/768/1024/1440px with zero automated axe violations, dark-system/light-page behavior, keyboard source tracing, fixed financial values, stable caption layout, native coverage disclosure, and no-JavaScript navigation/FAQ. Three focused app regressions passed: approved overview, complete local review/reopen journey, and signed-in header at seven widths. Desktop/mobile landing captures were inspected. The broader backend suite and authenticated Cognito journeys were not rerun for this static-page release.


Deployment evidence: application/source commit `8e3be20` was pushed to `codex/demo-product-polish`, and the Pages production deployment `c18b01eb` completed successfully. Eleven live HTTP checks passed using an explicit release-check user agent. Root HTML, stylesheet, script, font and both evidence images matched committed bytes exactly. Missing landing assets returned 404 with the landing content policy. Demo/pilot shells still serve the unchanged `index-CWGC2Gbc.js` app bundle; health returned 200, anonymous workspace API returned 401, and the deployment preview host returned 403. No AWS, Cognito, S3 or Neon deployment was performed.

The actual browser verified the live root title/heading, Inter font, white background, working source activation/caption, no overflow at 1440px or 390px, the FND-001 evidence deep link with $2,600 expected, and the private pilot sign-in entry. Ego's screenshot capture timed out; the local integrated desktop/mobile captures were inspected and deployed public bytes were checked independently. The full authenticated Cognito journey was not rerun. Browser task 16 was finished. Detailed HTTP checks are in ignored `artifacts/landing-live-http.json`; the approved original concept remains in its separate workspace, and the old untracked design files remain untouched.


## October 24, 2026 · Discoverable demo reports

The missing demo control was caused by a pilot-only report component. **Download report** is now beside the summary and on evidence/inputs. The demo exports current local results through browser print/save-as-PDF and an Excel-compatible CSV; it does not call the private report API or upload local records. The assigned-account pilot retains direct PDF/XLSX downloads from the same dialog.

Local evidence: 94 unit/component tests, 47 Chrome UI tests, and five targeted report API tests passed; production typecheck/build passed. New checks cover all finding states before review, a changed decision despite workspace filters, default note/worker omission, explicit note inclusion, literal hostile text, CSV formula protection, stale labels, Escape/focus return, 320/390px layout and light/dark accessibility. Four printed PDF pages were rendered and visually inspected. No new production library was added.

Hosted verification: source release `2efb50e` was pushed to GitHub and deployed through the dedicated role. The inspected Terraform plan changed only the image URI on the existing web/worker Lambda functions; apply succeeded and a subsequent plan reported no changes. Both functions are Active/Successful on the verified image (`sha256:ed5a50b7ecf619239cf5f780e8f87de8af4a4beac603c8762cc8f2dacc70623c`). Existing Cognito TOTP/callback, S3 access blocks/encryption, restricted Neon TLS/forced RLS and confirmed alert subscription passed read-only checks. All three report browser tests passed against the public Cloudflare demo. A separate real Cognito reviewer downloaded PDF and XLSX through the new control; assertions confirmed the current workspace state/version were unchanged. The full local import-to-report browser journey also passed.

The browser demo uses native print/save-as-PDF and CSV, not a direct `.xlsx` download. Chrome print output was rendered/inspected; a physical iPhone/Safari print sheet was not exercised. Direct PDF/XLSX remain available in the signed-in pilot. No data was uploaded by demo reporting and no new service or production dependency was added.


## Recurring workflow release · October 24, 2026

The complete local recurring workflow passes with the approved bright design: first-period XLSX; confirmed/saved layouts; separate approval; actual PDF/XLSX; second-period CSV; independent period selection; preserved earlier review/report; persistent assignment; an actual correction reference; registered-rate reuse without a rate reupload; corrected invoices; $0 difference with two coverage gaps retained; and resolved-case history. Expanded case forms were checked at 1440/390/320px in light and dark themes, with zero detected axe violations in those checked states.

Release regressions: **118 backend checks**, **97 unit/component/domain checks**, **47 original demo browser checks**, and **20 immutable handoff checks** passed. The final PDF pagination change has compact/varied/capacity coverage and a varied-example page-count regression; every rendered page of the 7-page varied report was inspected. The published compact example remains 3 pages; report length can grow with follow-up history. There are no nested layout groups forcing a separate page per finding, orphan headings or a trailing reference-only stub.

The measured 1,000-work/2,000-invoice scenario produces about 2.52 MB of state, a roughly 209 KB workbook and 234 KB PDF in about 2.8 seconds locally. A larger 2,000-work/4,000-invoice experiment exceeded the retained 4 MiB response guard; capacity was kept at the measured level. File, normalized-source, parser CPU/memory/time, result and concurrency guards remain active. This is not a cloud latency SLA.

The administrator migration test identified missing explicit organization predicates in the privileged backfill path and fixed them before live migration. Migrations 006–009 preserve original source/run/rate hashes and current decisions; published evidence is not rewritten. A predeployment recovery rehearsal restored 34 private source objects and matched the database snapshot. The initial live backfill created 24 historical workspaces, and the approved existing private reviewer became owner.

Live verification found that this Cognito pool requires its username for administrative password reset rather than the subject UUID. The corrected implementation stores the provider-verified username separately, protects it against reassignment, verifies its subject again before reset, and preserves authenticator requirements. Positive/negative identity-binding tests pass. Hosted completion is recorded below.

The actual hosted capacity check passed through Cloudflare, API Gateway, S3, SQS, Neon and both report encoders with 1,000 work records and 2,000 invoice lines. Acceptance took 16.8 seconds; XLSX and PDF took 15.5 and 12.2 seconds; the workspace response was 2.84 MB. The full measured check took 59.2 seconds, excluding sign-in. These are one synthetic observation, not a latency guarantee.

The hosted Cognito owner journey passed through private creation without messages, forced password change, authenticator enrollment, owner reset, MFA after reset, permission enforcement and immediate revocation. The isolated QA membership is revoked.

The hosted billing loop additionally exposed an out-of-order filter reply that could remove the selected resolved case. A deterministic test reproduced the failure before the fix and passes after response sequencing. A second test protects a rapid return to an already loaded period; a third verifies recovery from a failed case-detail request. The final hosted rerun is recorded below.


### Completed hosted release

Both existing Lambda functions are **Active / Successful** on the verified single-manifest AMD64 image `sha256:989c1931adc1f4bb4bd6a4125d783cf83533f5910e9af63bb07c3d2dd5665b73`. The final inspected Terraform plan changed only their image URIs; apply changed two resources, added none and destroyed none. The subsequent plan reported **no changes**. The only earlier runtime permission additions were private account creation and temporary password reset on the existing Cognito pool.

The final hosted billing journey passed in **76.7 seconds**, including distinct Cognito sign-ins, XLSX/CSV imports, saved mappings, source-download/role/CSRF checks, persisted review, both real report downloads, independent selected periods, historical reports, assignment, correction/reimport, $0 difference with two gaps retained, resolved-case history, 320/390/1440px light/dark checks and return to the selected historical period after fresh MFA sign-in. The owner lifecycle and maximum-capacity checks above passed on the same backend before the final frontend-only response-ordering fix; they were not rerun unnecessarily. All 97 source tests and the production typecheck/build passed after that fix, followed by the rebuilt local journey and exact-image container checks.

The production `/demo/` and `/pilot/` shells reference the rebuilt assets. Both deployed JS/CSS files matched local production bytes exactly; the anonymous workspace API returned 401. Read-only checks confirmed mandatory TOTP, the exact callback, encrypted/private S3, certificate-verified restricted Neon connections, forced RLS on all new workflow tables, append-only case-event permissions, the confirmed alert subscription and empty job/dead-letter queues. Cloudflare's static landing and fixed proxy needed no redeployment.

A post-release recovery rehearsal restored **19 tables and 54 private source objects**, matching the database snapshot hash and source bytes in **10.167 seconds**. It used the dedicated local restore database and made no destructive cloud change. This establishes no customer RPO/RTO or SLA.

Manual browser inspection additionally confirmed actual Cognito/TOTP sign-in, the aligned latest result, the retained $200 original evidence/decision, the correction reference and verification link, both historical report choices, 25 visible history rows with pagination, and a bright owner setup at 390px without horizontal overflow. Browser task 6 was finished. Ego screenshot capture timed out; the published product captures come from the passing hosted Chrome journey and were visually inspected. Its optional browser-tool update was left unapplied.

Real customer exports/contract semantics, independent accuracy labels, an unassisted billing-user session and approved data/operating policies remain external acceptance gates. No synthetic test establishes production certification or collected revenue.


## Agency export evaluation and landing release · October 24, 2026

The research-informed [agency evaluation](AGENCY_ADOPTION.md) is deployed at **https://shiftclarity.pages.dev/demo/?view=files**. Authorized minimized CSV/XLSX files are read and reconciled in browser memory, with explicit sheet/header/mapping/status/unit/scope confirmation. No source rows, results or local decisions are uploaded or stored in browser persistence. Direct Excel parsing and literal-cell Excel export use the explicitly approved, pinned SheetJS CE 0.20.3 in a bounded worker; no runtime CDN, model call, migration or paid service was added. The persistent cloud pilot remains synthetic.

Evidence for the final implementation:

- **142** unit/component checks; **126** backend checks; **58** original/demo/own-file browser checks.
- **11** own-file journeys pass through real FastAPI security headers and again at the live Cloudflare URL. Actual CSV/XLSX imports, sheet/header selection, mapping reuse, both financial directions, row corrections, incomplete coverage, source hashes and native PDF/Excel/CSV outputs are exercised. Canary source values never enter HTTP requests or browser storage.
- The private synthetic first/second-period import, independent account approval, review/report, history and correction loop passes locally and on the deployed Cognito/S3/SQS/Neon stack. The hosted run took about 1.2 minutes. Existing owner-lifecycle and maximum-capacity results remain historical; those unrelated checks were not unnecessarily repeated.
- **4** landing checks cover five viewport widths, light rendering on dark devices, WCAG checks, keyboard source tracing, disabled-JavaScript content, a visible primary CTA and real example PDF/XLSX downloads. Desktop/mobile rendered captures were inspected. A third hero action found overlapping during visual inspection was removed before the final landing release.
- **20** original handoff checks and **4** edge-routing tests pass; generated mapping metadata is synchronized. Full and production-only npm audits report zero advisories after a compatible patch to the existing test-only Undici dependency.
- [Claude disposition](CLAUDE_AGENCY_REVIEW.md) records independently verified fixes for numeric Excel locale interpretation, wrong worksheet dimensions, stale fixed authority, approval labels and cutoff/precision safety. Additional workbook cases cover desktop printer metadata, quoted sheet names and formatting extensions while actual formula cells remain rejected.

Both existing Lambda functions are Active/Successful on verified AMD64 image **sha256:24978067e020bd3126b11040fd2fbc0a8668a6939f54caa3b3f9f20e82616ede**. The actual Lambda emulator checked nonroot/read-only execution, restricted Neon access, UI/host rules and anonymous API denial. The network-disabled container smoke checked parsing, independent approval, shared calculation and both report encoders. The saved Terraform plan was inspected: only the web/worker image URIs changed; no creates, destroys or database migration. The post-apply plan reports no drift.

Cloudflare production deployment **e5636b43** serves the agency-focused landing: existing-system workflow, direct own-export CTA, explicitly fictional downloadable evidence, local-data/approval boundaries and scope FAQs. Live landing, demo/pilot shells, main/lazy styles/scripts and the workbook worker match local production bytes. The public fictional Excel sample matches its build bytes; anonymous workspace access is denied.

Post-release recovery matched **19 tables** and **65 private source objects** in **11.824 seconds**, restoring only the dedicated local rehearsal environment. No customer RPO/RTO or SLA is inferred.

The manual Ego workspace disappeared; no replacement was created without the skill-required permission. Actual Chrome outputs, downloaded workbooks/PDFs and desktop/mobile landing captures were inspected instead. The optional browser-tool update remains unapplied. No manual sign-in or real-agency acceptance is claimed for this release.

Research and invented export variants do not establish vendor certification, real-customer accuracy or a measured conversion/savings outcome. Customer-specific approved exports, contract semantics, independent labels and customer-cloud operating approval remain external acceptance work.


### Approved manual follow-up · October 24, 2026

With the user's permission, Ego task 8 manually exercised the live landing CTA, fictional CSV loading, all three confirmed mappings, readiness declarations, the published local workspace, evidence tabs, coverage gaps and report controls. The downloaded ten-sheet Excel report was independently read with OpenPyXL: $460 potential underbilling, $24 potential overbilling, $25 non-hourly charge retained, literal cells and worker identities omitted. The original work-approval event remains explicitly unknown. At 390px, evidence, coverage and the final file-setup header fit the viewport and render on a white background. Task 8 was finished once after verification.

Inspection found a small context mismatch: staged own-file setup showed a finding count from the fictional demo and an irrelevant reset action. The setup now hides those controls; published local records retain their own count and a consistently named “Clear local records” confirmation. The mandatory local-data disclosure has no ineffective dismissal button. Canonical demo dismissal/reset behavior remains covered.

The focused follow-up passed the production typecheck/build, 142 unit/component checks, 14 local browser checks and all 12 own-file tests at the live URL, including the new context/clearing regression. The current README screenshot is the actual hosted Chrome result, captured after its temporary notification closed. Exact-image Lambda verification passed; both existing functions are Active/Successful on digest `c5a61b04ef9fd9f88bb21d70e1aa152911cc99b476da8ec9d85c1b4a46ab6cda`. The saved plan changed only their image URIs; the post-apply plan has no drift. Live demo/pilot shells and main JS/CSS match the local build byte-for-byte; anonymous workspace access returns 401. Cloudflare landing assets were unchanged.

Ego screenshot capture still timed out, so this adds manual interaction/layout evidence, not a new Ego image or Safari/device test. The optional browser-tool update remains unapplied. Backend logic, private-account lifecycle and recovery were unchanged and were not unnecessarily rerun; their earlier evidence remains above. Real-agency acceptance gates remain open.


## Guided file-first release · October 31, 2026

The user authorized implementation and push/deploy of the adoption improvements. The local evaluator now starts with files, bounded CSV header suggestions, actual three-row/field previews, missing-field and code-meaning diagnostics, explicit work-period suggestions, optional control totals, a readiness checklist and linked/focused corrections. Bullhorn transaction-detail and Avionté weekly structures receive preparation guidance, not certification. Direct approved-rate entry feeds the same confirmed source adapter; no invoice-derived authority or fabricated file hash is introduced. Reporting-timezone conversion retains editable invalid/empty drafts and blocks missing/repeated DST times until corrected.

Verification: production typecheck/build and **150 unit/component checks** passed. A full **60-test** original/demo/adoption browser pass covered the earlier candidate; after the final readiness/timestamp refinements, the **14 final adoption journeys** passed through real FastAPI security headers and again at the deployed Cloudflare URL. They exercise CSV/Excel, header selection/suggestion, actual row previews, saved mappings, entered agreement rates, local-to-UTC report evidence, source corrections, incomplete coverage, both financial directions and PDF/Excel/CSV output. The added DST regression verifies that editing another field cannot clear the cutoff error and that clearing/replacing a timestamp remains usable. Existing unit cases retain signed credits, duplicates, precision and billing-scope controls; added cases cover titled/reordered exports, repeated headers/totals, weekly detail gaps, privacy and ambiguous dates.

Manual Ego task 2 inspected the actual local preparation/mapping flow, confirmed all three mappings, checked a 390px preview with its table scrolling inside the page, and verified the deployed file-first headings, rate-entry control, timezone selector and bright 390px layout. Actual rendered desktop/mobile screenshots were inspected; the mobile mapping capture is published with the README. The task was finished once. The optional Ego update was left unapplied. This is agent inspection, not an unassisted billing-manager result or physical Safari/device test.

The exact final AMD64 image passed Lambda runtime checks with nonroot/read-only constraints, restricted Neon connection, shared engine execution, host validation and anonymous API denial. Both existing functions are Active/Successful on digest `130fbdfd4348a4e90821921945e796a5c97915575f77b8e740cc2c184cb081f0`. The saved plan was guarded to only the two image URI updates; no database migration, new service or dependency was added. Post-apply Terraform reports no drift. Both live shells and all five production JS/CSS assets match the local build byte-for-byte; anonymous workspace API access returns 401. The existing Cloudflare static landing needed no change.

The local header test initially could not start because PostgreSQL was stopped; it passed after the existing test instance was started on its configured test port. Backend financial logic, private-account lifecycle and recovery were unchanged and not unnecessarily rerun. Earlier evidence remains historical. README, About, adoption instructions, ADR 0012, C4 component notes and [unassisted acceptance tasks](UNASSISTED_EVALUATION.md) describe the final scope. Proposed 15-minute first/five-minute repeat targets remain unmeasured; actual agency contracts/exports and intended-user observation remain external acceptance work.
