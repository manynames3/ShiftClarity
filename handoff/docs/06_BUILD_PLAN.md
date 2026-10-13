# 06 · Build plan and gates

## Authorization
This handoff authorizes Codex to build stages 0–3 as a local synthetic demonstration once the user starts the prompt. It does not authorize real customer data, deployment, communications or spend. Estimated task order is not a delivery-date promise.

## Stage 0 · Read, inspect, lock
Read the entire required handoff, inspect the target workspace, inventory applicable instructions and determine whether it is safe to create the new app. Run the handoff integrity tests. Record stack versions, scope, source priority and unresolved questions. Create local `DECISIONS.md`, `IMPLEMENTATION_STATUS.md` and acceptance checklist.
**Exit:** no unresolved safety/scope conflict; exact asset/data locations found; expected oracle understood; no unrelated repository modified.

## Stage 1 · Brand-exact shell and synthetic domain engine
Scaffold React/TypeScript/Vite with a pure domain boundary and decimal arithmetic. Load the original mark/tokens. Implement the responsive shell and fixture validation. Write tests for exact money, effective dates, aggregate references, credit/rebill, coverage partition and idempotency before wiring findings into the UI. Use the expected results only as a test oracle, not a UI dataset shortcut.
**Exit:** SC-01–11, SC-24 exercised; expected baseline totals exactly match; no LLM/API/backend/cloud dependency; shell screenshots inspected at desktop and mobile.

## Stage 2 · End-to-end review journey
Implement workspace, evidence, inputs/rules, approval and coverage routes; filters; source tabs; review dialog; decisions with required reasons; evidence-change reopening; demo-only author/approver role simulation; denied self-approval; fixture-only imports; run failure/incomplete state; exported reviewed findings; reset. Dynamic summaries must derive from underlying demo state.
**Exit:** SC-12–21 exercised; every visible CTA works or is explicitly scoped; source tabs refer to real supplied fixture excerpts; keyboard navigation and focus behavior verified.

## Stage 3 · Demo quality gate and handover
Run all tests and inspect each required state/viewport. Add end-to-end paths, negative cases, property checks and accessible semantics. Compare to canonical PNGs after the Inter font is available. Fix drift. Produce a short demo walkthrough, limitations, run/reset/test commands, screenshots and final acceptance matrix. Use independent read-only review when available/authorized and verify actual findings.
**Exit:** SC-01–24 all passed or explicitly blocked with reasons; no false completion claim. The demo is labeled "synthetic demonstration", not production. STOP HERE unless separately authorized.

## Gate before Stage 4 · Discovery and real-data permission
Verify a real recurring problem, current software capabilities/configuration, usable authorized source exports, document/rate approval workflow, billing cutoff semantics, expected volume, legal/data obligations, and commercial pilot scope. Decide whether the tool offers incremental value versus existing reports/configuration. Written approval is needed for the pilot and its environment/spend.

## Stage 4 · Secured single-customer pilot (not authorized now)
Build FastAPI/PostgreSQL/private storage/identity integration. Move calculation authority to server, implement durable revisions/runs/audit, roles, MFA, safe ingest, concurrency and retention. Remove demo switches from pilot mode. Threat-model and test access control, uploads, backups/restore, replay, retries and sensitive-data handling before any real records.
**Exit:** SC-25–29, SC-31 with reviewed evidence; real-data authorization complete; no unresolved material security issue.

## Stage 5 · Independent measurement (not authorized now)
Use an authorized representative sample, independent human labels and a held-out period; compare with the existing process and a properly configured incumbent. Predetermine thresholds with the billing lead. Include export/mapping/rule-maintenance time, false positives, missed errors, coverage, unknowns and actual correction outcomes. Insufficient sample = inconclusive, not success.
**Exit:** SC-30 and a written go/no-go recommendation. A diagnostic may conclude that a one-time configuration project is preferable.

## Stage 6 · Repeatable product (future)
Only after recurring value is demonstrated: decide onboarding, repeatable connectors, tenant isolation, support/SLOs, pricing limits, payment evidence, security assurance and permitted public claims. Do not turn the initial $995 pricing idea into an unlimited-support commitment.

## Checkpoint output format
1. Changed files and why.
2. Acceptance IDs completed.
3. Commands actually run and exact results.
4. Browser screenshots at named viewport(s), visually inspected.
5. Deviations, limitations, questions.
6. Next authorized checkpoint, or the explicit stop gate.

## Definition of a working demo
A billing lead can load the fixture, understand what was checked, inspect the 200.00 rate discrepancy, see the correctly aligned late-time and aggregate controls, explain the 1560.00 unbilled finding's prerequisites, review a rule with separate author/approver, resolve/reopen a demo finding, export a truthful review record, and reset. The same journey is keyboard accessible and does not depend on a paid model or live system.
