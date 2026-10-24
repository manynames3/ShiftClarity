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
