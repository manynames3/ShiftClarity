# ADR 0007: Confirm spreadsheet meaning before reconciliation

Status: accepted for the local fictional MVP, October 23, 2026. Live deployment and customer data remain separately gated.

## Context

Finance teams already have spreadsheets. Requiring canonical JSON transfers integration work to the evaluator. Guessing dates, overtime, invoice matches or approval authority would make onboarding easier at the cost of unreliable conclusions.

## Decision

Use bounded OpenPyXL/standard-library CSV adapters outside the existing exact-decimal engine. Deterministic aliases suggest columns and values; a person confirms worksheet/header, mappings, fixed values, USD/date/time/end-date conventions and source scope. Save workspace-scoped mappings with exact header signatures. On reuse, keep known custom mappings and expose new values for explicit confirmation. No LLM or vendor connector is required.

Normalize into the existing canonical Inputs and immutable import/job pipeline. Exact native work references or one unique composite match establish an allocation. Ambiguity remains an evidence gap. Errors block the whole source selection. Identical native rows/imports are reused; conflicting revisions require a corrected source version.

New terms are proposals from the uploader. Another permitted account independently attests the source authorization date and effective interval. A workspace lock serializes approval across sessions. Historical authorization never replaces the actual system event timestamp. Only explicitly segmented flat hourly components are supported.

Keep original bytes private, with sheet/row/file-hash lineage. Reject active workbook content and unsafe archives; bound size, expanded text, rows, subprocess CPU/memory/time and concurrency. Strip service credentials from the parser environment. This is process isolation and bounded parsing, not an OS exploit sandbox or malware certification.

Migrations 004/005 add forced-RLS sessions/files/profiles and accepted-source immutability. Failed guided acceptance preserves the earlier review and returns a useful error. Raw previews are role-restricted while staged and removed at acceptance. Original bytes expire after one/30 days; derived immutable evidence persists until owner purge. Profiles can be removed without changing accepted evidence.

## Consequences

Evaluators can import and repeat reviews without code changes. First-time rates require two accounts; subsequent identical rates reuse approval. Limits, stable pseudonymous IDs, whole-minute time and signed credit conventions must be explained. Vendor compatibility, source completeness, rounding policies, real-data authorization and customer accuracy require representative evidence beyond these fictional examples.
