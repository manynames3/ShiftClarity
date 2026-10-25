# Agency evaluation review and disposition

October 24, 2026. The user requested Claude’s second opinion. The subscription-authenticated, read-only Claude Code review inspected the bounded public implementation; it edited nothing and ran no tests. Extra Usage was explicitly confirmed off. Codex reproduced findings, implemented fixes and ran the checks below. No private configuration or prospect records were provided to the reviewer.

| Finding | Verified disposition |
|---|---|
| Local Excel/CSV rate columns looked like authenticated system approvals | Fixed. Local reports now say declared authorization date and declared author/approver reference. Private authenticated reports retain actual system approval separately. |
| Saved fixed dates/statuses could be reused as new authority | Fixed. Authorization/observation dates, approval/posting statuses, document kind and billing-scope fixed values are cleared on reuse. Stable mapping metadata still requires confirmation; new codes stay unconfirmed. |
| Numeric Excel 12.125 could become 12125 under decimal-comma text parsing | Reproduced and fixed in both browser and Python adapters. Numeric-cell typing survives transport and bypasses text-locale parsing. A dedicated regression checks the exact four-place rate. |
| Wrong worksheet dimension could drop cells | Fixed. Bounded actual cell coordinates determine extents; declared dimensions cannot truncate the selected worksheet. A crafted ZIP regression changes the dimension to A1 while retaining later cells. |
| Benign desktop workbook metadata was rejected | Fixed and tested: bounded printer-settings binaries and parenthesized local sheet references are accepted. Formatting extensions are distinguished from actual formula cells, which remain rejected before/after parsing. |
| Approval evidence after a billing cutoff could produce false missing billing | Reproduced and fixed. Closed-period scope is required. Late approvals or unknown timing receive no estimate. Date-only evidence retains its precision and cannot imply approval by a midday cutoff; original event time is never invented. |
| Invalid observation might crash rendering | The existing `parseCustom` already reconciled inside the validation try/catch, so the proposed render crash was not reproduced. Added an earlier row-level diagnostic and range validation. |
| A signed-in cookie might route a local report to a private API | Not reproduced. `/demo/` has no pilot controller; private `files/custom` views are redirected to inputs. Local reports stay local even when a private session exists elsewhere. |
| Rows above a selected header and unmatched posted lines needed disclosure | Added explicit pre-header exclusion counts and unresolved-reference warnings. Blank rows are not financial records. Ambiguous posted lines continue to withhold affected estimates. |

The public schema is generated from Python, and a differential test checks common supported monetary semantics. It does **not** establish universal adapter equivalence or vendor certification: local parsing remains intentionally stricter for certain date formats, cross-file duplicates and overly long combined references.

Verification: 142 unit checks, 126 backend checks, the private two-period/correction browser loop, 11 own-file journeys through real FastAPI security headers, original/demo browser regressions, and the Lambda/offline container checks. Final deployment and landing evidence is recorded in [VERIFICATION](VERIFICATION.md). Test files cover workbook activity, visibility, archive/resource bounds, dimensions, typed numeric locales, explicit sheet/header selection, signed credits, retained non-hourly fees, stale profile values, cutoff timing, no record upload/storage and actual reports.

Research-informed invented fixtures are not genuine agency exports. Customer-specific approval authority, contract semantics, independently measured accuracy and persistent customer-cloud operating approval remain separate acceptance work.
