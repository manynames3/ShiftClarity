# 03 · Deterministic domain contract

## Canonical snapshot
`dataset_id = sc-demo-v1`, `run_id = RUN-001`, as-of `2026-10-12T17:00:00-04:00`, service interval `[2026-10-01, 2026-10-11)` in `America/New_York`. All data is fictional. All money is USD.

14 shifts, 8,880 worked minutes (148 hours). 12 shifts / 7,440 minutes (124 hours) are evaluated. Partition: 6 aligned (3,600 min), 6 flagged (3,840 min), 1 abstained (720 min), 1 not evaluated (720 min). These partitions sum exactly to the received workload. There are 2 financial finding groups and 2 coverage tasks. There is no collected or recovered amount.

## Monetary representation
Rates: nonnegative decimal strings with up to four fractional places; amounts: signed decimal strings with two fractional places. Parse strictly and compute with Decimal/decimal.js equivalent; integer minutes determine duration. For the supplied standard component: `line_expected = quantize(minutes / 60 × rate, 0.01, HALF_UP)`. The fixture has no fractional-cent ambiguity. A production policy must specify rounding per supported billing unit and is not inferred from this demo.

Never calculate monetary comparisons with JS Number/Python float. Integer minor-unit values may represent already-rounded amounts but cannot substitute for exact duration/rate arithmetic. USD only in v1. Negative amounts are valid on supported credit lines; negative worked minutes are not.

## Source authority
Approved synthetic amendment > preceding synthetic rate sheet only because the fixture explicitly records that supersession. Do not generalize this into legal precedence for arbitrary MSA, PO, email, rate card and amendment. Conflicting terms result in abstention until an authorized person resolves them. Every value records its document ID/excerpt, author and approval.

## Effective dates
Intervals are half-open `[effective_from, effective_to)`, with null upper bound meaning open-ended. Use the service-local date at the facility, not import time, time approval date or invoice date. `recorded_at` and `approved_at` remain separate metadata. A shift that crosses a contractual rate boundary must be segmented according to an approved policy, or abstain; do not assign the entire shift to one date by convenience. Overnight/DST examples in tests are not permission to invent a universal billing policy.

## Invoice applicability and signed net
Posted regular invoice/debit amounts are positive; posted credit amounts are negative. Draft/void items do not enter posted totals. Retain invoice ID, line ID, linked original/chain ID and shift references. The fixture's rebill chain has +720, -720 and +780, for a net 780. Do not drop the negative line or declare each document a separate opportunity.

## Matching
Tier 1: explicit source assignment/shift IDs carried in invoice references, with matching facility and currency. Tier 2 (later only): a configured, proven unique composite key. Fuzzy person names or nearest timestamps cannot auto-confirm a financial conclusion.

Many-to-many matching is represented with signed monetary allocation edges. For the fixture's aggregate line, explicit shift IDs all share the same approved rate, each has 480 minutes, and each receives 520.00 of the line's 1560.00. Source minutes and value reconcile. When a single aggregate covers mixed rates, unclear components or missing line detail, compare at the supported aggregate scope only or abstain. Do not invent shift-level precision.

For fractional allocations in later supported policies, specify deterministic rounding/residual assignment keyed to stable IDs. Allocation sums must equal the source amount with the appropriate sign. The same source line cannot be counted twice. A credit offset reduces a charge; it is not a negative work event.

## Missing-billing prerequisite
All must hold: approved supported work; trusted identity; source time coverage available; billing cutoff has passed; invoice extract declares complete posted records through a required as-of no earlier than the cutoff; valid credits/rebills and aggregates considered; no net invoice representation for the eligible work. Otherwise the result is incomplete evidence / not evaluated, not "$X missing".

The fixture defines expected billing cutoff `2026-10-12T12:00:00-04:00`, invoice source-as-of `2026-10-12T16:00:00-04:00`. This is a synthetic rule, not Assist's real billing calendar. Freshness alone does not prove completeness. Expected extract ranges, source row counts and independent source control totals should be reconciled in a real pilot; absent evidence of completeness blocks missing-billing conclusions.

## Finding groups and impact
FND-001: S001–S004, 2,400 approved minutes, effective standard rate 65.0000, expected 2600.00 vs billed 2400.00 = **+200.00** discrepancy (potential underbilling), not a collected amount.
FND-002: S005–S006, 1,440 approved minutes, expected 1560.00 vs billed 0.00 = **+1560.00** discrepancy requiring review, subject to complete synthetic billing coverage.
GAP-001: S012 callback component unsupported → abstained; impact null.
GAP-002: S013 pending time approval → not_evaluated; impact null.

A shift can have more than one finding type. Aggregate financial effect must be computed once from canonical expected vs signed billed position, with component attribution that sums back to it. Do not sum overlapping alert values. Do not net overbilling against underbilling to create a cleaner-looking total. The two canonical nonoverlapping findings total 1760.00 of potential discrepancy, but the workspace does not use this as a hero KPI.

## Coverage semantics
Per received work record, choose exactly one category:
1. `not_evaluated`: no valid financial decision attempted, for example pending approval or incomplete source coverage.
2. `abstained`: evaluation attempted but unsupported/conflicting/ambiguous facts prevent a reliable comparison.
3. `evaluated_flagged`: at least one reliable financial discrepancy under supported rules.
4. `evaluated_aligned`: reliable supported comparison, no discrepancy under those rules.

Priority for the fixture is approval/source prerequisites before supported-rule comparison. Store specific reason codes. If several blockers apply, keep all blocker reasons but use one partition category. Input validation/quarantine counts are reported outside the accepted-record partition with received/rejected counts; do not make rejected rows disappear.

Record coverage and time coverage have different denominators. The fixture evaluates 12/14 records (85.714...%) and 7440/8880 minutes (83.783...%). Display exact counts and rounded labeled percentages only if useful. Monetary coverage is omitted when expected values are not known for every record. Do not call 12/14 "verified hours."

## Reproducibility and review persistence
A run manifest records dataset/batch IDs, canonical source revisions, rule-version IDs, engine version, applicable calendar version and as-of instant. Hash canonicalized inputs deterministically. An evidence fingerprint excludes UI filters, export row order, whitespace and import time when those do not change meaning; it includes relevant amounts, IDs, source versions and rule semantics.

An identical rerun preserves findings and decisions. A changed evidence fingerprint reopens review and keeps historical events. File hashes detect identical uploads, not overlapping extracts; stable source record revisions are also necessary. Newer exports supersede only in an explicit declared snapshot scope, never via arbitrary last-write-wins. Missing rows in a partial export do not mean deletion.

## Manual decisions
Confirm = reviewer agrees discrepancy exists. Dismiss = scoped reason explains why it is not a discrepancy under these inputs. Request evidence = local task, no outbound message. Correction = separate later workflow requiring supporting record. Recovery/collection is unsupported without payment-allocation evidence. Never suppress a case forever just because an earlier version was dismissed.

## Explicit supersession example
The optional rule-approval reference uses `draft_rule.json` and DOC-004. It is not included in RUN-001. If approved later by a separate reviewer, its explicit authorized supersedes link caps the predecessor's applicability in the derived evaluation view at October 13, without editing the predecessor's immutable stored version. Overlap without a valid explicit supersession remains a conflict. Do not mutate an approved rule to make the intervals appear cleaner.
