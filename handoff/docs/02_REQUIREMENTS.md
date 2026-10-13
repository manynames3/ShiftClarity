# 02 · Requirements and behavior

Labels: **D** required in synthetic demo; **P** required before real-data pilot; **L** later, not authorized. Each ID must map to tests and a build checkpoint.

| ID | Stage | Requirement / acceptance |
|---|---|---|
| SC-01 | D | Persistent "Synthetic demo" disclosure; fictional run time, facilities, workers and documents; no real customer attribution. Demo reset returns the exact canonical state. |
| SC-02 | D | Workspace displays total input work records, evaluated records, open financial findings, and coverage gaps as different counts. Total record and minute partitions reconcile. |
| SC-03 | D | Coverage categories are disjoint: evaluated_aligned, evaluated_flagged, abstained, not_evaluated. A shift with multiple findings is counted once. Hours/minutes coverage is separate from record coverage. |
| SC-04 | D | Unknown monetary values remain unknown/null. Incomplete data never produces a "clean", "verified", or recovered-money summary. |
| SC-05 | D | Every run identifies its input batches, source-as-of times, expected service interval, completeness declarations, rule versions, engine version and completion state. Demo declarations are fixtures, not discovered truths. |
| SC-06 | D | Rate selection uses approved rules for service date and supported facility/role/component. Late entry does not change the applicable rule. Unsupported or conflicting terms abstain. |
| SC-07 | D | Use decimal arithmetic for rates and money and integer worked minutes. Display signed impact clearly; separate underbilling and overbilling. |
| SC-08 | D | Only approved work is financially evaluated. Missing approval creates a nonfinancial not_evaluated coverage task. |
| SC-09 | D | Only supported, posted, nonvoid invoice lines enter billed totals. Credit/rebill chains net using signed amounts and stable lineage. |
| SC-10 | D | Fixture aggregate line can cover several explicit shift IDs. No heuristic fuzzy match is silently treated as exact. Missing identifiers or ambiguous mapping require evidence. |
| SC-11 | D | Missing-billing finding requires supported approved work, passed billing cutoff, complete invoice coverage through the required as-of time, and no qualifying net allocation. Otherwise show a gap. |
| SC-12 | D | Each finding shows inputs, source excerpt, expected/billed calculation, supporting record references, reason code, coverage limitation and reviewer state. |
| SC-13 | D | Review transitions are needs_review → confirmed / dismissed / evidence_requested. Dismissal and evidence requests require a reason. No outcome claims funds are collected. |
| SC-14 | D | Relevant evidence/rule change reopens a decided finding. Earlier history is preserved; unchanged inputs preserve the decision. |
| SC-15 | D | Evidence requests create a local task/draft only. No sending. Confirmation does not alter an invoice or contract. |
| SC-16 | D | Inputs & rules shows validated, incomplete, unsupported, quarantined and failed conditions distinctly; prior complete run remains visible when a new run fails, marked stale. |
| SC-17 | D | Demo import is limited to supplied fixtures; reject nonfixture input without uploading it. State clearly that general import is not implemented. |
| SC-18 | D | Human-approved rule drafts reference source text, author, approver and effective dates. Demo role simulation is conspicuous. Self-approval is denied. |
| SC-19 | D | Search/filter is deterministic; visible empty-filter state differs from "no findings". Show result count and clear-filter action. |
| SC-20 | D | Review export includes source/run IDs, coverage limitations, decision/reason and signed discrepancy; neutralize spreadsheet-formula-leading text. No ePHI or sensitive free-text fields. |
| SC-21 | D | Required routes: workspace, finding detail, inputs/rules, rule approval, coverage detail. Navigation, back links, source tabs, filtering, dialogs and reset work. No fake "connected" state. |
| SC-22 | D | Keyboard operation, visible focus, semantic headings/tables, accessible dialogs, status announcements, text status labels, reduced motion, responsive evidence stacking and no page overflow. |
| SC-23 | D | All screenshots and known states conform to design tokens, original logo, viewport contract and visual acceptance checklist. |
| SC-24 | D | Application computes from inputs; golden expected results are used only by tests. Domain module has no UI/network/clock dependencies. |
| SC-25 | P | Durable API authorizes every resource/action server-side; role claims come from verified identity, not request body or demo switch. MFA and no shared accounts. |
| SC-26 | P | Versioned immutable batches/rules/runs; canonical source-row revisions and overlapping exports handled idempotently. Decisions use optimistic concurrency and a stable evidence fingerprint. |
| SC-27 | P | Secure upload quarantine/allowlist/limits, malware handling as appropriate, private storage, authorization-gated document download and safe parser resource limits. |
| SC-28 | P | Data classification/minimization before upload, documented allowed fields, data-use authorization, retention/deletion plan, backups/restore, logs without raw records and incident contact. Assess legal/BAA obligations where applicable. |
| SC-29 | P | Atomic publication of completed runs, durable jobs/retries, idempotent writes, exact source selection, failure diagnostics and replay tests. |
| SC-30 | P | Independently reviewed evaluation on actual authorized samples against existing process and properly configured incumbent. Agreement on coverage, precision, recall, review effort and total value before testing. |
| SC-31 | P | No production pilot until discovery, security and commercial gates are explicitly approved; no SLA or certification claims based on this kit. |
| SC-32 | L | Live connectors, public marketing site, SSO, multi-customer SaaS onboarding, payment attribution and additional billing components require separately approved scope. |

## Finding state machine
A newly computed financial finding starts `needs_review`. A reviewer can `confirm` it, `dismiss` with a reason, or `request_evidence` with a specific question and owner. It can return from `evidence_requested` to `needs_review` after a local evidence change. A material input change creates a new evidence fingerprint and reopens any prior decision. Previous events remain read-only.

Do not use "resolved" for "we read the finding." The pilot may later track a correction outcome with supporting evidence. An app cannot assert the source system was corrected unless that is actually verified. Closed task states do not imply payment.

## Rule state machine
`draft → pending_approval → approved` or `rejected`. Approval requires a different authorized person, a source excerpt, a defined applicability interval and no unresolved overlap. An approved rule cannot be edited in place. A superseding version is a new record. Record effective date independently from recording/approval timestamps. Discovery must decide whether retroactive contractual approval is supported; the demo rules are all approved before the evaluated work.

## Loading / empty / error / permission states
Skeletons preserve layout, with an accessible loading label. Zero imports prompts fixture load, not a zero-issues message. Zero filtered results offers reset. No financial findings with gaps says "No discrepancies found in the checked records" and retains the gap panel. An invalid row shows an actionable reason and source row; a failed run never blanks prior results. Unauthorized role changes return a denial with no write. Simulated roles never claim real security. Distinguish saved demo state from stored production data.

## Responsive behavior
Desktop/tablet support full workflow. At narrow mobile widths, evidence sections stack, actions remain reachable, and tables may use a contained labeled scroller or accessible cards. No automatic financial approval on tap-to-open. Mobile is an inspection/review experience, not a separate feature family. A desktop recommendation may be shown for long imports, but critical meaning and controls must remain accessible.
