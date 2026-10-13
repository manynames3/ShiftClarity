# 07 · Test, evaluation and security contract

## What exists in this handoff
`spec-tests/test_fixture_integrity.py` validates synthetic input arithmetic, references, partitions, brand tokens, required file presence and basic contract structure. It is not the application's test suite. `golden_cases.json` and `acceptance.feature` specify additional future application behavior. `qa/HANDOFF_QA.md` records the checks actually executed when packaging.

## Domain tests required for demo
Exact decimal calculations and approved policy rounding; effective-date boundaries; late entry uses service date; missing approval; unsupported components; complete-vs-incomplete invoice extract; billing cutoff before/after; duplicates and overlapping snapshots; aggregate invoice; partial allocation; signed credit/rebill; invalid amounts/currencies/IDs; stable rerun fingerprints; material-change reopening; source conflict; valid overbilling finding; multiple findings without double-counted impact.

Never use fixture expected outputs to generate the tested results. The calculation engine must read normalized inputs. Avoid a circular test that simply compares a hard-coded object with itself.

## Useful properties/invariants
Accepted coverage categories partition records and known minutes exactly. Source allocations reconcile to signed invoice amounts. Expected - net billed equals canonical discrepancy with component attribution. Reimport of the same logical snapshot does not create additional amounts or findings. Reordering inputs changes no results. Splitting/aggregating equivalent records is invariant only when the underlying monetary/rounding policy is equivalent. Material source/rule changes alter the evidence fingerprint; irrelevant UI state does not.

A work record may have an hours and rate finding, but the canonical effect is counted once. Credits require signed equality, not an unsigned "less than" allocation check. Error tests assert behavior, not just absence of a crash.

## Interaction/e2e
Fixture import → workspace counts → finding → source/rate/invoice tabs → confirm with reason → history → evidence change → reopened decision → reset. Dismiss requires a reason. Self-approval is blocked. A stale version produces a conflict in future API tests. Filters do not change underlying coverage. Export states the fixed run/sources and limitations. A failed run retains prior dated results. No-findings-with-gaps stays visibly partial. Reference-only buttons are not mistaken for app functionality.

Test keyboard-only journey, screen-reader names/headings, focus after route changes, dialog trap/return and Escape. Check 200% zoom, long filenames, long facility labels, reduced motion and 320/390/1024/1280/1440 widths. Inspect errors/empty/loading as well as happy path. No fake page-wide "all clear".

## Security before any real-data pilot
Classify/minimize inputs before upload; establish data-use authorization and legal review where required. MFA, least privilege, safe session handling, no shared accounts, no client-supplied identity authority. Every object and action is checked by the API, including nested source files, exports, background operations and guessed IDs. Use CSRF protection for cookie-based sessions; restrictive CORS/CSP appropriate to the chosen deployment; secure cookies/session expiry; no secrets embedded in clients or URLs.

Private storage, quarantined ingest, allowed file types/content verification, resource limits, malware strategy, safe parser execution, formula-safe exports, record-free logs and approved retention/deletion. Test expired signed links, cross-organization guesses, lower-role actions, self-approval, malicious cells, malformed/oversized files, duplicate submissions and concurrent reviewers. A PDF/contract may contain hostile instructions; no AI extraction in the initial pilot.

If future multi-customer deployment is approved, re-evaluate tenant isolation everywhere, not only database rows. A single-customer demo is not evidence of multi-tenant security.

## Recovery
Kill a worker during compute; retry idempotently; assert no partial publication or duplicated findings. Restore a backup to a clean environment and compare source lineage, rules, results and reviewer events. Ensure expired/deleted data cannot silently reappear outside the agreed backup policy. Record real recovery measurements; do not invent RPO/RTO targets without customer/budget agreement.

## Pilot evaluation (future, not measured)
Write the sample, supported scope, label method, comparison baseline and acceptance thresholds BEFORE seeing final outcomes. Independent reviewers establish ground truth from agreements/work/invoices, not the app. Reserve held-out records; include no-issue controls and known-error examples. Compare against the current process AND existing software correctly configured. Measure precision, recall, dollar-weighted misses, coverage/abstention, net reviewer time, setup/maintenance burden and useful incremental findings. No-errors sample cannot prove recall. A synthetic seed suite cannot prove real-world reliability.

A suggested 95% precision goal is a proposed pilot target, not a certification, competitive benchmark or achieved result. Coverage and false assurance are first-class success criteria. The system must never call a record verified when it was not evaluated. Confirmed corrections are not collections; time saved is not automatically payroll savings.

## References
W3C WCAG 2.2 contrast guidance; OWASP File Upload and Authorization Cheat Sheets; HHS cloud/BAA guidance. Links and exact provenance are in `09_SOURCES_AND_ASSUMPTIONS.md`. These inform controls; none makes this app compliant by itself.
