# From existing exports to a billing review

This MVP is for fictional evaluation. The new spreadsheet workflow runs in the signed-in **local pilot**. It is not deployed to the hosted pilot yet. No JSON conversion, vendor connector or paid AI is required.

## Start the local application

Follow [Development](DEVELOPMENT.md#persistent-local-pilot), then open `http://127.0.0.1:5180/pilot/`. Sign in with the generated **reviewer** account and enroll its personal authenticator. Use the distinct **approver** account in another browser profile/private window. Credentials remain in ignored `.local/accounts.json`; never put them in GitHub or a shared report.

First-time rate approval intentionally requires a second account. Reusing identical approved rates does not require another approval. Assigned accounts remain required; this release adds no public signup.

## First review: October 1–10

1. Choose **Files & rate approvals**. Select facility **FAC-A**, October 1–10, files current through **October 12 at 17:00 UTC**, billing cutoff **October 12 at 12:00 UTC**. Confirm both completeness declarations only for this supplied fictional example.
2. Create the review. Download and upload **Contract rates**, **Approved work** and **Invoices & statements** from the built-in example. Use all three XLSX files or their [CSV equivalents](../public/examples/spreadsheets/).
3. Inspect each worksheet and source preview. Confirm the columns, value mappings, ISO dates, decimal-point USD amounts and hours. Save the work mapping as **Monthly work export**. Suggestions and saved profiles require confirmation.
4. Select **Validate all sources**. Any row error blocks acceptance. Correct its file/mapping, remove the earlier staged file if necessary, and validate again. **Download all corrections** lists every error without echoing raw cell values.
5. In the separate approver account, open the listed review. Read the rate originals and inspect the three hourly versions, effective dates and source authorization dates. Enter a specific reason and approve. The actual approval time is recorded separately from the historical source declaration.
6. Back in the reviewer account, refresh status, check the displayed counts/totals and any warnings, explicitly **Accept sources**, then **Run billing review**.
7. Open the finding. Inspect the contract, work and invoice evidence, then confirm, dismiss or request specific evidence with a reason. A decision is a review record; it does not edit an invoice or send a message.
8. Download **Excel** and **PDF** before moving to the next period. Reports include every finding state, current decisions, calculations, source references and coverage gaps. Worker identity fields and reviewer notes are omitted by default; include notes only when authorized to share them.

Expected results are independently written in [expected-results.json](../public/examples/spreadsheets/expected-results.json); application calculations do not read that file.

| Measure | Expected fictional result |
|---|---:|
| Work received / evaluated | 8 / 6 records; 59 / 48 hours |
| Evaluated expected / invoiced | $3,305 / $3,105 |
| Potential underbilling / overbilling | $200 / $0 |
| All posted invoices, including unchecked work | $3,775 |
| Coverage gaps | 2: unsupported callback and pending time approval |

The $200 comes from four 10-hour shifts at $65/hour compared with $60/hour invoiced. Explicit overtime ($97.50/hour) and weekend ($85/hour) rows align. The callback has no approved matching rate. The pending time has no approval. Neither unchecked row receives a financial estimate. Potential amounts establish no collectibility or recovered revenue.

## Repeat: October 11–20

Create a new review for FAC-A, October 11–20, with source/cutoff October 22 at 17:00/12:00 UTC. Download **Next-period work CSV** and **Next-period invoice CSV** from the example disclosure; reuse the original rates. The files are also [here](../public/examples/spreadsheets/period-2-work.csv) and [here](../public/examples/spreadsheets/period-2-invoices.csv).

Apply **Monthly work export**. Its header signature matches even though this source is CSV rather than XLSX. The new export code **RG** appears with an empty component mapping: explicitly choose **standard**, then confirm. Existing custom value mappings are retained. Validate and accept; unchanged registered rates need no second approval. The next review again shows $200 potential underbilling and two coverage gaps, with **Needs review** rather than carrying over the earlier decision.

Only the current run is editable/exportable in this MVP. Accepted source selections and immutable completed runs remain in history; reopening a prior run's review workspace/report is not implemented. Save each report before advancing.

## Files you can use

Three categories are required: independently approvable rates, work and invoices. Multiple CSV/XLSX files are allowed; choose the intended sheet/header. Blank CSV templates are supplied as a ZIP to unzip locally, not to upload. Alternate generic [time](../public/examples/spreadsheets/layout-b-work.csv) and [hospital statement](../public/examples/spreadsheets/layout-c-statement.csv) layouts exercise alias and composite matching. They establish no certified Bullhorn, Avionté, QuickBooks or VMS compatibility.

Use stable reference codes (letters, digits, underscore, hyphen; maximum 80 characters), not names. Remove patient, clinical, contact, banking and personal-name columns. Header checks are only a safeguard and cannot classify every sensitive value. This build requires fictional records regardless of which files are chosen.

| Convention | Required behavior |
|---|---|
| Time | Whole minutes, or decimal hours that convert exactly to whole minutes. For rounded exports such as 7.33 hours, map the original minutes column. No guessed rounding. |
| Components | One explicit hourly component per work row; separately approved flat USD rates. No inferred overtime threshold, holiday calendar, multiplier, guarantee or non-hourly fee. |
| Dates | Confirm ISO, month/day/year or day/month/year. Excel date cells are unambiguous. Confirm inclusive/exclusive rate end dates. Source/cutoff timestamps use the explicitly labeled UTC fields. |
| Authorization | A supplied source authorization date, including an explicitly confirmed fixed date when the whole file shares it. A separate approver attests it; the system event time is never backdated. |
| Credits | Negative credit amounts, nonnegative invoice/debit amounts. Explicit credit quantities may be negative and normalize to absolute minutes. Credits need a valid original/rebill chain; no sign or allocation is guessed. |
| Matching | Exact work references, or one unique facility/worker/date/role/component match. Ambiguity creates a gap, conservatively at facility level when affected work is unknown. |
| Completeness | Source declarations and independently supplied controls are explicit. Parsed totals are not independent proof. An empty invoice extract requires a complete declaration and an independent posted total of zero. |

## Bounds and recovery

Each review supports nine files, 1 MiB/file, 1,000 data rows/selected sheet, 50 columns, eight worksheets/workbook, 500 work records, 1,000 invoice lines and 100 rate versions. Normalized sources must fit 1 MiB; projected reviewed state must fit 4 MiB. Split larger exports by facility/period. Macros, formulas, external relationships, embedded objects, merged/hidden sheets and unsafe archives are rejected. Workbook expanded text, parser CPU/memory/time and concurrent parser/report work are bounded. The workspace allows 20 new sessions and 120 parsing/validation attempts per hour; failed file attempts count.

An identical native row/import is reused, not appended. Conflicting IDs/source versions block acceptance. Correct the source version rather than overwriting history. Failed/interrupted work does not publish partial results; the prior completed result remains available. A failed guided acceptance gives an actionable error without invalidating the earlier review.

Quarantine originals and abandoned previews expire after one day; accepted original bytes after 30 days. Raw previews are removed when accepted. Derived immutable source/rate/run/review evidence persists until the owner performs the separately authorized workspace purge. Saved profiles persist until removed or purged. [Owner retention tools](PHASE_4.md) remain outside the application API. Local expiry requires running the maintenance command; S3 byte lifecycle alone does not redact database evidence. No customer retention/BAA policy is implied.
