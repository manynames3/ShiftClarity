# Spreadsheet adoption MVP

October 22, 2026. Approved user scope: implement an evaluable, fictional-data MVP in the existing application, then update GitHub README/About. Actual customer records and live deployment remain gated. The original handoff is preserved. No new cloud service or paid AI is required.

## Adoption decisions

Start with one facility and one billing period. Upload existing CSV/XLSX exports, select the worksheet/header, confirm suggested column and value mappings, review all validation results, obtain independent approval for new rate versions, and explicitly accept the source selection. Reuse the existing durable job and evidence/review screens. For the next period, saved workspace mappings are suggestions requiring confirmation; unchanged approved rates are reused. Provide fictional files and a documented two-person walkthrough.

Amounts use exact decimals. Each row represents one explicit hourly billing component; regular/overtime/holiday/weekend/on-call/callback require their own documented rates. No inferred calendars, overtime splits, multipliers, minimum guarantees or non-hourly charges. Mixed-rate aggregates and ambiguous matches remain evidence gaps. Blocking rows cannot be silently excluded. Source counts/totals calculated by the importer are parse controls, not independent completeness evidence; allow separately supplied control totals.

Preserve actual approval timestamps. An optional historical source authorization date is independently attested during approval and never replaces the system event time. Uploaded approval flags confer no authority. Keep native IDs, original bytes, worksheet/row references, mapping versions and review history. Dataset identity is stable per facility/period, so decisions from unrelated periods cannot merge.

## Milestones and exit checks

1. **Import foundation:** isolated bounded CSV/XLSX parsing; formula/macro/external-content rejection; worksheet/header selection; deterministic mappings and configurable values/date/decimal/end-date conventions; complete row diagnostics and safe error CSV; profiles persisted under forced organization RLS. Test alternate headers, malformed rows, archive/XML limits, dates, duplicate IDs and mapping signatures before continuing.
2. **Reconciliation compatibility:** normalize to canonical Inputs, with explicit source coverage/cutoff declarations; exact-reference or unique composite matching; batch independent rate approval, temporal authorization, credits/voids/partial and reverse billing. Reuse immutable imports/jobs and preserve prior results on failure. Verify original oracle, explicit additional components, ambiguity, incomplete coverage, exact money, replay and cross-workspace denial.
3. **Customer UX:** branded guided upload/map/validate/approve/accept/run flow; drag/drop and multiple files, progress and recoverable errors, profile reuse and next-period navigation, readable dashboard under/overbilling and review progress. Demonstrate a complete fictional import and review at desktop/mobile, including keyboard and accessibility checks.
4. **Reporting:** authorized filterable XLSX and branded PDF with executive summary, both exposure directions, all finding states, itemized calculations, source references/lineage, review history, stale warnings and coverage gaps. Force spreadsheet text literals, escape PDF markup, omit worker identity and reviewer free-text by default. Test exported values/types, injection and visual pagination.
5. **Security and verification:** exercise each new endpoint's authentication, role/CSRF/tenant boundaries, immutable accepted snapshots, retention/purge, interrupted upload/run, concurrency and repeated imports. Run original regression tests and the complete fictional-data browser journey. Record real results and screenshots; no customer readiness/certification/ROI inference.

## Claude review disposition

Accepted: confirmed value maps, source authorization versus real approval time, no partial imports, no inferred allocations, per-period dataset identity, bounded parser subprocess, explicit mapping signatures, current-review reports rather than publish-time snapshots, and retention coverage for all new tables. Wide component columns are not silently exploded into invented shifts: this release accepts explicitly segmented hourly rows and explains that boundary. Vendor-style fictional examples are test inputs, not verified Bullhorn/Avionte/QuickBooks/VMS compatibility or connectors.

## Real-customer gates

Representative scrubbed exports and verified source semantics; documented legal/data-use/retention/incident responsibilities; customer-specific independent accuracy and effort measurement; representative capacity/recovery tests; explicit real-data and deployment approval. Synthetic checks cannot establish these.

## Verified completion

All five milestones have local fictional evidence in [VERIFICATION.md](VERIFICATION.md) and MVP-01 through MVP-10 in [the acceptance checklist](../ACCEPTANCE_CHECKLIST.md). The manual path and supplied second-period files are in [the walkthrough](SPREADSHEET_WALKTHROUGH.md). The GitHub update publishes source/docs only; live migration/deployment and customer-data authorization remain separate.
