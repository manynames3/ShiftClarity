# Build ShiftClarity from this handoff

Act as a senior product engineer and design engineer. Build **ShiftClarity**, a Supreme AI Ventures web product for **contract-to-invoice verification for healthcare staffing**.

The full handoff is in `./handoff/`. If it is elsewhere, locate the extracted `ShiftClarity_Build_Kit_v1` folder before proceeding. Do not guess its contents or fetch a different project.

## First
Read `handoff/AGENTS.md`, `contracts/scope-lock.json`, `docs/01_PRODUCT.md` through `docs/07_TEST_AND_SECURITY.md`, the synthetic dataset, and the canonical visual reference. Open the supplied desktop, mobile, evidence, rules and coverage PNGs. Do not infer the UI from this prompt alone.

Inspect the target workspace and any existing instructions. Keep all work in a NEW dedicated ShiftClarity repository/workspace; do not modify the Supreme AI Ventures website or any other project. Preserve unrelated files. Before implementation, output a short stage plan, conflicts/unknowns, and a test matrix tied to acceptance IDs. Do not ask optional styling questions already answered by the kit.

During stage 0, establish root-level project instructions from `handoff/WORKSPACE_AGENTS.md` in the new app workspace. Preserve any existing applicable instructions; do not overwrite them silently. The root instructions must continue to point to this handoff after context resets.

## Authorized build
Implement stages 0–3 in `docs/06_BUILD_PLAN.md`: a polished, functional **local synthetic-data demo** with no live integrations, no cloud provisioning, no real records, no production claims, and no external model/API calls. Stop at the demo release gate. Later backend, security and real-data pilot stages are SPECIFIED but NOT authorized by this prompt.

Use React + TypeScript + Vite for the demo, a pure typed domain module, decimal arithmetic, and local demo state. Share contracts and canonical fixtures. Choose supported stable library versions and lock them. No backend is required for the first demo; do not add one just for scaffolding. The future FastAPI/PostgreSQL contract is a boundary to preserve, not an instruction to build it now.

Implement the complete in-scope journey:
1. A visible fictional-data disclosure and fixed run snapshot.
2. A workspace showing evaluated records, findings and explicit coverage gaps.
3. Contract-change verification, including correct effective dates and late-entered time.
4. Matching approved work with the fixture's posted invoices, including a correct aggregate and credit/rebill chain.
5. An evidence detail view with source excerpts, expected/invoiced comparison, line allocation, immutable rule references and review history.
6. Confirm, dismiss-with-reason, request-evidence and reopen workflows in demo state. A changed underlying evidence fingerprint reopens a prior decision.
7. Inputs & rules, fixture-only import, import validation failures, separate author/approver role simulation clearly marked DEMO, and denied self-approval.
8. Coverage gaps, incomplete-data state, no-findings-but-partial-coverage state, and reset-demo.
9. A truthful reviewed-findings export with formula-safe text and no "recovered" claims.

Build computations from `data/synthetic/` inputs. Do NOT hard-code the expected findings as results; use `expected_results.json` only as a test oracle. Supplemental golden scenarios in `spec-tests/golden_cases.json` must be exercised too.

## Design contract
Match `brand/tokens.css`, `brand/tokens.json`, `docs/05_BRAND_AND_UI.md`, `reference/index.html` and the canonical screenshots. This is a bespoke product in Supreme AI Ventures' navy/teal/white family: editorial typography, precise rules, restrained geometry, purpose-built evidence views. Use the supplied SVG mark and wordmarks. No generic SaaS restyling, purple gradients, stock medical imagery, financial "money recovered" hero, fake trend charts, oversized pills or chatbot homepage.

The minimum screen set is workspace, finding evidence, inputs & approved rules, rule approval and coverage details. Product-intro and brand-board references guide branding; do not add a public marketing/pricing site to this stage.

## Required verification
Run fixture tests first. Add engine unit/property tests, component interaction tests, keyboard/accessibility checks, and Playwright end-to-end tests. Reproduce all reference states at 1440×1000, 1280×900, 1024×900 and 390×844. Inspect screenshots, not only test exit codes. No horizontal page overflow; a contained table scroller is allowed where specified. Honor reduced motion and keep focus visible.

After each checkpoint: show changed files, commands/results, screenshots, deviations, unresolved decisions and next gate. Do not claim an independent Claude review, application test, security control or integration ran unless it did.

No commits, pushes, deployments, paid API requests, emails or real-data uploads. Finish with a working local demo, exact run/test commands, `IMPLEMENTATION_STATUS.md`, an acceptance-ID checklist, known limits, and a clear stop before real-data work.
