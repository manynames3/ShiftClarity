# Synthetic release verification

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

Real customer records, authorized source semantics, representative capacity/cost measurement, independent accessibility/security audits, production restore targets, incident contacts, and approved retention/backup policies remain unverified. See [pilot gates](PILOT_GATES.md) and the [evaluation plan](EVALUATION_PLAN.md).

No recovered/collected-money, competitor-superiority, legal compliance, certification, or production-readiness claim follows from the synthetic checks.
