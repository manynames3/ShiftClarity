# Pilot stages and acceptance gates

The user explicitly requested phase 4 with realistic synthetic data and approved its backend libraries. Local development continues beyond the original demo gate. The original handoff remains unchanged.

| Phase | Implemented work | Remaining acceptance gate |
|---|---|---|
| 0–3 | Branded interface, exact shared engine, original local demo/preview, five routes, review/approval/export and recorded tests/screenshots. | Original acceptance evidence is recorded. |
| 4 synthetic build | FastAPI, PostgreSQL/Neon, local OIDC and deployed Cognito MFA, server permissions/sessions, immutable evidence/runs, jobs/replay, private imports, authoring, retention tools, actual restore rehearsals, and verified AWS Lambda/SQS/S3 deployment. | Synthetic results are recorded in [verification](VERIFICATION.md). |
| 4 real-data pilot | Security controls have synthetic evidence. | Customer discovery/source semantics; authorized data-use/legal scope; approved customer environment/spend; representative capacity/recovery verification; operating/incident owner and approved retention/backup policies. |
| 5 | Evaluation protocol prepared. | Representative authorized sample, independent labels, held-out period and properly configured incumbent comparison. No results measured. |
| 6 | Productization gates preserved. | Demonstrated recurring value, separately approved connectors/onboarding, operating/commercial limits and public claims. |

Competitor complaints inform failure cases; they are not proof of a customer's actual recurring problem. This application accepts fictional minimized data only. Real records and sensitive notes require the separate real-data gate.

AWS hosts the synthetic pilot through a dedicated deployment role, with Cognito, private S3, Lambda/SQS, and a separate Neon Free branch. These choices support intermittent fictional presentations with minimal idle infrastructure. The October 13 publication approval covers this public source repository and documentation. Real data, paid database upgrades, outgoing communications, production use, and measured-value claims remain separate approvals. See [AWS operations](AWS_AND_DATABASE.md) and [verification](VERIFICATION.md).
