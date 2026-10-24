# Acceptance checklist

Evidence is app-specific; the original handoff matrix remains untouched. Demo results apply to synthetic/local preview behavior, not pilot security or real-world detection accuracy.

- [x] **SC-01** — Persistent "Synthetic demo" disclosure; fictional run time, facilities, workers and documents; no real customer attribution. Demo reset returns the exact canonical state.
- [x] **SC-02** — Workspace displays total input work records, evaluated records, open financial findings, and coverage gaps as different counts. Total record and minute partitions reconcile.
- [x] **SC-03** — Coverage categories are disjoint: evaluated_aligned, evaluated_flagged, abstained, not_evaluated. A shift with multiple findings is counted once. Hours/minutes coverage is separate from record coverage.
- [x] **SC-04** — Unknown monetary values remain unknown/null. Incomplete data never produces a "clean", "verified", or recovered-money summary.
- [x] **SC-05** — Every run identifies its input batches, source-as-of times, expected service interval, completeness declarations, rule versions, engine version and completion state. Demo declarations are fixtures, not discovered truths.
- [x] **SC-06** — Rate selection uses approved rules for service date and supported facility/role/component. Late entry does not change the applicable rule. Unsupported or conflicting terms abstain.
- [x] **SC-07** — Use decimal arithmetic for rates and money and integer worked minutes. Display signed impact clearly; separate underbilling and overbilling.
- [x] **SC-08** — Only approved work is financially evaluated. Missing approval creates a nonfinancial not_evaluated coverage task.
- [x] **SC-09** — Only supported, posted, nonvoid invoice lines enter billed totals. Credit/rebill chains net using signed amounts and stable lineage.
- [x] **SC-10** — Fixture aggregate line can cover several explicit shift IDs. No heuristic fuzzy match is silently treated as exact. Missing identifiers or ambiguous mapping require evidence.
- [x] **SC-11** — Missing-billing finding requires supported approved work, passed billing cutoff, complete invoice coverage through the required as-of time, and no qualifying net allocation. Otherwise show a gap.
- [x] **SC-12** — Each finding shows inputs, source excerpt, expected/billed calculation, supporting record references, reason code, coverage limitation and reviewer state.
- [x] **SC-13** — Review transitions are needs_review → confirmed / dismissed / evidence_requested. Dismissal and evidence requests require a reason. No outcome claims funds are collected.
- [x] **SC-14** — Relevant evidence/rule change reopens a decided finding. Earlier history is preserved; unchanged inputs preserve the decision.
- [x] **SC-15** — Evidence requests create a local task/draft only. No sending. Confirmation does not alter an invoice or contract.
- [x] **SC-16** — Inputs & rules shows validated, incomplete, unsupported, quarantined and failed conditions distinctly; prior complete run remains visible when a new run fails, marked stale.
- [x] **SC-17** — Demo import is limited to supplied fixtures; reject nonfixture input without uploading it. State clearly that general import is not implemented.
- [x] **SC-18** — Human-approved rule drafts reference source text, author, approver and effective dates. Demo role simulation is conspicuous. Self-approval is denied.
- [x] **SC-19** — Search/filter is deterministic; visible empty-filter state differs from "no findings". Show result count and clear-filter action.
- [x] **SC-20** — Review export includes source/run IDs, coverage limitations, decision/reason and signed discrepancy; neutralize spreadsheet-formula-leading text. No ePHI or sensitive free-text fields.
- [x] **SC-21** — Required routes: workspace, finding detail, inputs/rules, rule approval, coverage detail. Navigation, back links, source tabs, filtering, dialogs and reset work. No fake "connected" state.
- [x] **SC-22** — Keyboard operation, visible focus, semantic headings/tables, accessible dialogs, status announcements, text status labels, reduced motion, responsive evidence stacking and no page overflow.
- [x] **SC-23** — All screenshots and known states conform to design tokens, original logo, viewport contract and visual acceptance checklist.
- [x] **SC-24** — Application computes from inputs; golden expected results are used only by tests. Domain module has no UI/network/clock dependencies.
- [ ] **SC-25** — Durable API authorizes every resource/action server-side; role claims come from verified identity, not request body or demo switch. MFA and no shared accounts.
- [ ] **SC-26** — Versioned immutable batches/rules/runs; canonical source-row revisions and overlapping exports handled idempotently. Decisions use optimistic concurrency and a stable evidence fingerprint.
- [ ] **SC-27** — Secure upload quarantine/allowlist/limits, malware handling as appropriate, private storage, authorization-gated document download and safe parser resource limits.
- [ ] **SC-28** — Data classification/minimization before upload, documented allowed fields, data-use authorization, retention/deletion plan, backups/restore, logs without raw records and incident contact. Assess legal/BAA obligations where applicable.
- [ ] **SC-29** — Atomic publication of completed runs, durable jobs/retries, idempotent writes, exact source selection, failure diagnostics and replay tests.
- [ ] **SC-30** — Independently reviewed evaluation on actual authorized samples against existing process and properly configured incumbent. Agreement on coverage, precision, recall, review effort and total value before testing.
- [ ] **SC-31** — No production pilot until discovery, security and commercial gates are explicitly approved; no SLA or certification claims based on this kit.
- [ ] **SC-32** — Live connectors, public marketing site, SSO, multi-customer SaaS onboarding, payment attribution and additional billing components require separately approved scope.

SC-17 passes in the canonical Load sample files workflow. A later explicit user instruction adds a separate schema-restricted local preview for their own minimized records. This is a deliberate, recorded scope extension, not a fixture-only production importer.

Historical October 12 baseline: 69 unit/component tests; 20 handoff integrity tests; 21 browser cases including six automated accessibility route checks. All G01–G20 are exercised across engine/demo tests. Visuals: 81 screen/state captures, with layout inspection sheets and selected full-resolution manual inspection. No independent Claude review, production audit, live integration or real-data evaluation was run.

## Phase 4 synthetic checkpoint

- SC-25: real local OIDC/MFA, server membership/resource/action checks, short hashed sessions, CSRF and negative identity/role tests; Neon runtime role/TLS exercised. Live Cognito MFA/subject verification and separate-role AWS deployment now have synthetic evidence.
- SC-26: immutable accepted imports/revisions/rules/documents/runs, source lineage, receipts, exact source selection and optimistic review/fingerprint conflicts tested.
- SC-27: schema-bound JSON quarantine, resource/content limits, safe diagnostics, private local/S3 adapter controls, authorization/expiry downloads and interrupted quarantine recovery tested. Private S3 controls, anonymous denial and authorized retrieval are verified on AWS.
- SC-28: synthetic classification, documented minimized fields, record-free diagnostics, privileged retention/purge and local/Neon restore rehearsals. Customer legal/data-use/retention/incident policy remains a gate.
- SC-29: atomic publication, lease fencing, bounded retries, actual killed worker, idempotency and replay tested.
- SC-30: independent actual-sample measurement remains unperformed.
- SC-31: no real data or production deployment based on this synthetic build.

See IMPLEMENTATION_STATUS.md and the updated matrix for actual evidence and limits.


## October 13 AWS synthetic checkpoint

52 backend tests, 70 domain/component tests, 20 original integrity tests, 21 original browser regressions and 8 complete AWS browser journeys passed. 26 cloud captures and actual Cognito branding were inspected. Private S3 original access, FIFO jobs and a matched Neon/S3-to-local restore were exercised. Verified image IDs, OS scan, runtime settings and Terraform drift identify the deployed environment. The final wording-only update passed build/component/container and anonymous API/resource checks. The user ended the manual browser task before its additional authenticated recheck; the complete eight live journeys passed before that wording-only update.

SC-25,26,27,29 pass within the authorized synthetic AWS scope. SC-28 has synthetic minimization/storage/restore evidence; actual customer policies and incident contacts remain gated. SC-30 independent measurement and SC-31 production/real-data acceptance remain separate. No live connector, public SaaS onboarding, payment attribution or production/security certification was added.

## Spreadsheet adoption MVP · October 23, 2026

These checks describe the implemented and deployed synthetic upgrade, including the October 23 owner-authorized release. They do not mark real-customer SC-28/30/31 gates complete.

- [x] **MVP-01 — Existing files:** CSV/XLSX in all three source categories, multiple files, worksheet/header preview, deterministic normalization, explicit acceptance and original row/file lineage. Parser/adapter tests and full API/browser journey.
- [x] **MVP-02 — Meaning confirmed:** columns, values, fixed source fields, date/decimal/time/end-date formats, normalized previews and all-row diagnostics. Unresolved errors block the source selection.
- [x] **MVP-03 — Reuse:** workspace-RLS profiles with exact header signatures; preserve known custom values and explicitly map a new code in the second-period browser journey. No invented vendor verification.
- [x] **MVP-04 — Independent terms:** real event timestamps separate from source authorization; self-approval denied, conflicting concurrent approvals serialized, unchanged approved rates reused.
- [x] **MVP-05 — Billing compatibility:** same exact-decimal engine; dated amendments, explicit hourly components, missing/partial/duplicate billing, signed credits/voids/rebills, reverse statements, ambiguity and incomplete-coverage gaps. Original oracle unchanged.
- [x] **MVP-06 — Review:** accepted source counts, evaluated work, both difference directions, missing allocations, coverage tasks, review progress and evidence requests; source detail and persisted decisions.
- [x] **MVP-07 — Reports:** current reviewed state, every finding state, itemized allocations, approved terms, source rows/hashes and gaps; literal/filterable XLSX, branded paginated PDF, no default worker identities/notes/raw canonical fingerprints. Actual browser downloads and rendered PDF inspection.
- [x] **MVP-08 — Security/recovery:** every new endpoint identity/role/CSRF cases, cross-workspace RLS, immutable accepted files/sessions/profiles, guarded downloads, expiry/purge, failed byte-copy retry, simultaneous acceptance, revision conflict and committed failed-parse budget.
- [x] **MVP-09 — Repeatable fictional evaluation:** supplied first/second-period files, fresh second-period decisions, reuse without new code or another unchanged-rate approval; narrow-screen overflow and automated accessibility checks.
- [x] **MVP-10 — Compatibility:** original standalone/browser/oracle checks, full backend tests, production build, local nonroot/read-only/network-isolated container parser/engine/report smoke. Current actual totals and remaining limits are in [verification](docs/VERIFICATION.md).

Hosted release evidence additionally covers real Cognito MFA and unassigned-account denial, S3 byte-matched originals and role/CSRF denials, persistent reviews/reports, repeat-period use, additive migrations with unchanged prior record hashes, and an isolated restore of 15 tables and 34 private objects. Both functions are Active/Successful; Terraform has no drift. See [verification](docs/VERIFICATION.md).

Not implemented/established: certified vendor connectors, inferred rate policies or fractional-minute rounding, historical review/report navigation, customer data/legal/operations acceptance, or independent real-sample accuracy/effort measurement. The locally provisioned test sessions do not bypass production identity code.
