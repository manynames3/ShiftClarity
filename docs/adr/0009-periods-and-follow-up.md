# ADR 0009: Keep each period review and track follow-up across reruns

Status: accepted, October 24, 2026. Supersedes ADR 0008's current-run-only restriction.

## Context

Staffing billing repeats. Downloading a report before the next import is an avoidable dependency, and one shared latest workspace interferes with two people reviewing different periods. A confirmed discrepancy also needs an owner and a correction trail after it disappears from a later aligned calculation.

## Decision

Retain immutable `completed_runs` source/calculation snapshots. Add `review_workspaces`, keyed by organization and run, for versioned decisions and tasks. Pin the selected run in the browser URL and preserve it through reauthentication. Ignore stale period/filter replies so older network responses cannot replace the current selection. A historical review write changes its own workspace; it never switches the organization's latest published run. A database trigger protects each review's original run and source selection. Reports read the selected period's reviews. Current rule drafts/approval versions are exposed separately from the selected financial period, so historical review does not make the live approval register stale.

Add `billing_cases` for each period/facility/issue and append-only `case_events`. Keep case ownership and correction/evidence references separate from financial review decisions. Reviewers manage cases; an assigned active member may supply evidence without gaining review or approval permissions. An old run's review does not rewrite a case's newer source facts.

A rerun resolves a financial case only when complete declared sources include **every affected work reference**, in the same facility and exact service interval, and every record evaluates aligned. Missing, pending, ambiguous, unsupported or partly corrected records cannot close it. Coverage cases resolve when all affected records become evaluable; that may reveal a financial finding. Discrepancies that return reopen their issue. Resolution never means invoice payment or collection.

The PDF and ninth Excel sheet distinguish original financial evidence from latest follow-up status as of report generation. Notes remain opt-in. No email, invoice-editing service, accounting ledger or new cloud service is added.

## Migration and bounds

Owner-side migrations 006–009 preserve original snapshots and recover available review events into historical workspaces. Server fingerprints use SHA-256 of the same canonical strings, using Node/Python standard libraries. The browser demo retains its existing behavior. A migration test verifies original snapshots, decision recovery, normalized fingerprints and publication dates.

Measured synthetic capacity is 1,000 work records and 2,000 invoice lines per review, with 150 rate versions, nine files, 2 MiB/file, 2 MiB normalized sources and a 4 MiB result ceiling. A 2,000-work/4,000-invoice experiment exceeded that result ceiling; the ceiling was retained. Larger reviews must be split by facility/period. These local measurements establish no customer accuracy or cloud latency SLA.
