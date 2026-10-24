# Billing compatibility for the spreadsheet MVP

Amounts are potential differences, with collectibility unknown. Every supported case requires explicit approved USD hourly terms and source coverage. The canonical demo remains unchanged.

| Case | Behavior |
|---|---|
| Standard rates, multiple facilities and roles | Exact facility/role/component/service-date rule match |
| Effective-dated amendments | Explicit predecessor and nonconflicting interval; end-date convention confirmed during mapping |
| Overtime, holiday, weekend, on-call, callback | Explicitly segmented work rows and separately approved flat hourly rates; no inferred calendar or multiplier |
| Unapproved/missing time approval | Unevaluated coverage task; no financial estimate |
| Missing invoice allocation | Finding only after explicitly complete invoice coverage and passed cutoff |
| Partial billing and duplicate billing with distinct line IDs | Compare the sum of posted qualifying allocations against approved work |
| Identical rows with native IDs | Reused once and reported as duplicates; conflicting versions/IDs block import |
| Credits, voids, adjustments and rebills | Signed posted debit/credit chains; void/draft lines excluded; unsupported lineage becomes a gap |
| Hospital or reverse-billing statement | Explicitly mapped posted invoice lines, tested with fictional layouts; no live VMS compatibility claim |
| Missing direct work reference | Unique facility/worker/date/role/component match only; otherwise visible evidence gap, conservatively blocking the facility when affected work is unknown |
| Mixed-rate aggregated invoice line | Explicit evidence gap; no invented pro-rata allocation |
| Missing/incomplete invoice coverage | Unevaluated records, retained denominator, no zero-billing inference |
| Source errors or out-of-period rows | Reject source selection, keep the previous completed run; no silent row dropping |
| Non-hourly fees, guarantees, rounding policies, per diem, inferred overtime | Unsupported; require separate modeling and acceptance, never fabricated rates |

Imported roles/components are confirmed mappings. A contract authorization date is a source declaration independently attested by the approver; actual system approval retains its real timestamp. First-time terms require a second account. Repeated identical approved terms do not require repeated approval.

Time must resolve to whole minutes; use a source minutes column instead of rounding a decimal-hour export. Credits require negative signed amounts; explicitly negative credit quantities normalize to absolute minutes. Nonposted lines with blank work references are retained and excluded from billing. A confirmed fixed source authorization date is allowed when the rate export shares that date, subject to independent attestation.

Selected-period Excel/PDF reports include all finding states, itemized allocations and separately labeled latest follow-up. Period history reopens earlier reviews and reports; the team queue retains ownership, correction references and verification-run history. The complete source-format and security limits are in the [walkthrough](SPREADSHEET_WALKTHROUGH.md).
