# Synthetic release verification

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
