# Synthetic release verification

## October 23, 2026 · Spreadsheet adoption MVP (local only)

The CSV/XLSX-to-review-to-report upgrade is implemented locally and documented for fictional evaluation. It has **not** been deployed to AWS/Neon/Pages. The earlier hosted release evidence below remains historical.

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
