# ADR 0008: Export the current reviewed evidence

Status: accepted for the local fictional MVP, October 23, 2026.

## Context

The earlier CSV export contains reviewed findings only. A billing manager needs a shareable report that also shows undecided work, overbilling, source evidence and limits. A run's immutable publish-time snapshot does not contain later decisions.

## Decision

Generate Excel/PDF on demand from one current workspace-head snapshot, authorized by the server. Preserve every finding state and separate evaluated-work invoice allocations from the all-posted total. Show confirmed differences without treating review confirmation as collection or an invoice adjustment. Label retained stale results. Include source rows/hashes, exact rate terms, historical authorization, real approval time, calculations, coverage gaps and current decision history.

OpenPyXL produces filterable sheets with literal strings and separate allocation rows. ReportLab produces branded, paginated PDFs using an embedded font and the authentic outlined wordmark. Escape all untrusted paragraph content. Display PDF hours to two decimals beside exact whole minutes. Exclude worker identity fields and reviewer free text by default; notes need explicit opt-in. Hash raw engine fingerprints before export, since their canonical source serialization contains record content.

Reports are private/no-store, audited and limited to two concurrent encoders. This release exports the current run only. Download before advancing to the next period. Earlier immutable runs and source selections remain retained; reopening their review/report workspace requires a separately implemented history feature.

## Consequences

No new service, report store or accounting implementation is needed. Excel remains useful for detailed filtering; PDF provides a readable management summary. Source limits bound report size, with a declared-capacity synthetic check. A desktop/local check establishes no Lambda latency SLA, real-customer capacity or permission to send a report outside the workspace.
