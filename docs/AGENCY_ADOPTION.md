# An agency can test its exports before changing its workflow

October 24, 2026. Implementation research and assumptions, not customer discovery or certified vendor compatibility.

The initial buyer/user hypothesis is a healthcare staffing owner or finance lead and a billing specialist who already close time and invoice periods. They keep their ATS, VMS, payroll and billing system. ShiftClarity is an additional evidence review: approved dated contract terms × approved worked minutes, compared with signed posted billing. Findings need human review; neither a finding nor a confirmation proves payment.

## What the primary sources show

| Source | Verified reality | Product consequence |
|---|---|---|
| [Bullhorn Transaction Master Detail](https://kb.bullhorn.com/middleoffice/Content/BH1/Topics/bh1CanvasTransactionMasterDetailReport.htm) | Detailed pay/bill fields include candidate/placement IDs, transaction dates, earn codes, quantities and invoice references. Its summary rolls up by candidate, placement, week and earn code. Quantities can represent units other than hours, and externally entered billing transactions are excluded. | Request detail, verify hourly units and unique transaction IDs, retain external billing/memos separately. Do not infer service dates from week ending. “Client” is a company name; use an explicit stable facility code consistently. |
| [Avionté Classic Time Entry Sheet View](https://avionteclassicsupport.zendesk.com/hc/en-us/articles/360045311194-Standard-Report-Time-Entry-Sheet-View) | Standard fields include week worked, employee name/phone, pay/bill units and rates. Start/end identify the assignment; paid date is a check date. | Ask for minimized transaction detail with worker IDs and dated service records. The illustrative weekly file deliberately does not satisfy required service-date/worker-ID mappings. |
| [ShiftWise supplier report guide](https://www.shiftwise.com/wp-content/uploads/2020/01/reports-suppliers.pdf) | Different reports expose timeslip status, usage, rate plans and invoice memos; Unit Usage excludes memos. Rate plans can contain modifiers and guarantees. | A hospital statement is not a complete signed ledger without its relevant memo export. Do not import the same charge again as an agency invoice. Unsupported guarantees/modifiers get no invented hourly valuation. |
| [Bullhorn API access FAQ](https://www.bullhorn.com/bullhorn-api-access-faqs/), [API fair-use policy](https://bullhorn.github.io/api-fair-use-policy/), [Avionté API program](https://www.avionte.com/api-integrations/) | API access has provider/contract/permission prerequisites. Published fields do not prove a customer has the needed endpoints or exports. | Start with explicit file mappings. There is no fake Connect button, borrowed credential, unvalidated native integration or claim that every agency uses one stack. |

These findings support an **export-first** path, not a claim that incumbents lack reconciliation or that errors occur at any measured rate. The need to build an independent rate register and the ability to obtain dated records remain the largest adoption assumptions. No agency, customer data or customer acceptance results were available.

## A prospect’s first review

1. Open **Test your own exports** from the landing page or **Test your own files** in the demo. No account or cloud upload is required.
2. Start with one facility and a closed weekly/biweekly period. Use the realistic fictional CSV or Excel files first if desired; their expected results and manual checks are downloadable.
3. Export approved time and posted billing from the current systems. Include stable pseudonymous worker/work/invoice-line IDs, service dates, explicit hourly components and signed credits/rebills. Remove personal, contact and clinical columns. Select values-only XLSX directly and confirm its worksheet/header row, or use CSV UTF-8. Only explicitly selected sheets enter the review.
4. Supply approved contract bill rates separately, with effective/authorization dates and two distinct author/approver references. Local declarations are not authenticated; verify them against the actual agreement. Do not copy invoice rates as proof of agreed rates.
5. Confirm mappings, each source code’s meaning, time units, date/decimal formats and source scope. Missing approval evidence remains missing. When the approval-event date is unavailable, an explicitly supplied approved-status observation is labeled separately. Unknown components can be retained as unsupported/manual review.
6. Compare independent source totals when available. All nonblank data rows are accounted for, identical duplicates are disclosed and conflicts block publication. Fees can be explicitly classified outside hourly scope; they remain in invoice totals without an estimated difference. Incomplete/ambiguous records have no financial estimate.
7. Open the review. Inspect potential underbilling **and** overbilling, affected records, dated terms, allocations, coverage gaps and source file hashes. Record a scoped local decision and download Excel/CSV or print/save PDF before leaving.
8. Keep mapping metadata private and reuse it on the next export. New codes remain unconfirmed; fixed approval/authorization dates, approval/posting statuses and billing-scope assertions are cleared. Refresh clears source records and local decisions. The invite-only synthetic workspace separately offers persistent periods, actual account-based independent approval and server XLSX/PDF reports.

## Included manual evaluation

[Files and independent expected results](../public/examples/agency-evaluation/EXPECTED_RESULTS.md): 8 work records / 69 hours received; 6 / 54 hours evaluated; $460.00 potential underbilling; $24.00 potential overbilling. Signed posted source total $3,501.00 includes a $25.00 non-hourly fee. Original/credit/rebill for W6 nets to $700.00. Pending time and a callback without applicable terms have no estimate. These invented cases demonstrate behavior, not typical error prevalence or projected ROI.

Change one amount by $10; verify the corresponding difference changes by $10. Uncheck coverage; verify no missing evidence becomes underbilling. Break the credit chain; verify an evidence gap replaces that calculation. Add a new status code; verify it needs an explicit mapping. Try the weekly summary; request better service-level detail rather than manufacturing shifts.

## Boundaries and acceptance

Own-file evaluation accepts CSV and values-only XLSX, USD and explicitly supplied hourly components, with whole-minute time and 1–93-day periods. Limits: 2 MiB/file, nine files, 2,500 rows/file, 1,000 work records, 2,000 invoice lines, 150 rates. XLSX parsing runs in a lazy worker with an eight-second deadline, 16 MiB archive expansion, 150 entries, eight visible sheets, 100,000 cells and 2 MiB expanded cell text. Formulas, external links, hidden data, merges and unsafe archives are rejected. No OCR, native connector, automatic overtime/rounding, invoice writeback, collections or customer-cloud upload. Browser input is memory-only, not a security/compliance certification or substitute for the prospect’s authorization.

| ID | Requirement | Evidence |
|---|---|---|
| AD-01 | Source-aware first review and realistic manual kit | `SourceGuide.tsx`, fictional layouts, expected-results manual |
| AD-02 | Own-file input with no server/model upload | `local-tables.ts`, `LocalFiles.tsx`, request/storage browser assertions |
| AD-03 | Unit/status/privacy guards and retained unsupported/non-hourly records | Domain/backend adapter tests, real private API/report replay |
| AD-04 | Less repeat-period preparation | Exact-header local mapping downloads, new-value checks, private next-period helper/profile diagnostics |
| AD-05 | Useful, traceable output | Both billing directions, coverage, all local invoice rows, file SHA-256/batch/native references, notes opt-in |
| AD-06 | Consistent verified release and truthful claims | [Verification](VERIFICATION.md), ADR 0011, C4 component/sequence, screenshots |

Before a paid operational rollout: validate actual approved exports and contract semantics, measure first/second-period effort against the agency’s configured incumbent process, independently label findings and aligned samples, and approve customer-cloud handling/operating policy separately. Synthetic tests cannot establish those results. The practical presentation is a functioning evaluation tool with explicit scope, rather than a promise of universal compatibility.


## File-first preparation · October 31, 2026

The local evaluator now puts file selection before period declarations. CSV header suggestions are bounded to the first twenty rows and retain explicit excluded-title counts; Excel still requires selecting its worksheet/header. Every mapping has a three-row preview, example values, required-field diagnostics and unconfirmed-code guidance. Recognized Bullhorn transaction-detail and Avionté weekly-report structures are guidance, not certified integrations. Weekly summaries never acquire invented service dates. The existing source guide gives the export recipe and provider reference.

Use dates found in mapped work records to propose the period, then confirm actual scope. Reporting cutoffs accept UTC or the offered source timezone, including the browser's timezone; timestamps are normalized to UTC. Nonexistent/repeated daylight-saving times block validation and request the exact UTC timestamp. Completeness, time units, status meanings, authority and approval dates are never inferred. Control totals are optional and collapsed until requested.

For agencies without a rate-register export, the local approved-terms form supports separate hourly components, effective versions, amendment links and source authorization dates. It feeds the same mapping/validation/calculation path. Manually entered terms have no original-file hash; declarations remain unauthenticated. Rates cannot be derived from the invoice being checked.

The readiness checklist explains missing source/period/approval preparation before running. Error messages focus the correction panel and link back to mappings and scope; row-level correction downloads remain available. [Unassisted evaluation tasks](UNASSISTED_EVALUATION.md) separate automated correctness from actual customer usability and define proposed 15-minute first/five-minute repeat targets without claiming achieved results.
