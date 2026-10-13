# ShiftClarity · Build Kit v1.0
**A Supreme AI Ventures product concept. Prepared October 12, 2026.**

**Every shift. Clearly aligned.**
Contract-to-invoice verification for healthcare staffing.

## Start here
1. Open `reference/index.html` in a browser. It works locally without an installation. Its navigation switches between the canonical design references. It is NOT the application.
2. Read `docs/01_PRODUCT.md`, `docs/02_REQUIREMENTS.md`, and `docs/06_BUILD_PLAN.md`.
3. Extract this entire folder into a NEW, dedicated ShiftClarity workspace. Do not extract over another repository.
4. Give Codex the text in `START_HERE_CODEX.md`. Keep this folder available as `handoff/` in that workspace.
5. Codex first reports its plan, conflicts, and test strategy, then builds the authorized **synthetic-data demonstration** in checkpoints. Real data, customer integrations, cloud deployment and external communications require separate approval.

## What this package is
A build contract: original SVG brand assets, exact design tokens, navigable HTML visual references, desktop/tablet/mobile PNG references, product and domain requirements, an API contract for the later backend, synthetic input records, golden scenarios, and staged implementation instructions.

It is not a production app, security certification, third-party product endorsement, or evidence of losses at Assist. All names of sample facilities, workers, amounts, contracts, and activity entries are fictional. "Assist Healthcare / sample workspace" personalizes a private demo; it does not imply Assist is a client. No operational credentials or real patient/worker records are included.

## Read order and authority
Newest explicit user decisions > `AGENTS.md` and `contracts/scope-lock.json` > requirements/domain rules > data/API contracts > brand tokens and interface specification > canonical HTML and PNG references. A conflict is a defect to report, not permission to choose whichever is easier. Generated inspiration, if supplied separately, is not a specification.

## Contents
- `START_HERE_CODEX.md`: paste-ready implementation request.
- `AGENTS.md`: hard boundaries and anti-drift instructions.
- `WORKSPACE_AGENTS.md`: root-level instruction template for the new application workspace.
- `docs/01_PRODUCT.md`: audience, positioning, scope, private commercial assumptions.
- `docs/02_REQUIREMENTS.md`: numbered functional requirements and state behavior.
- `docs/03_DOMAIN_RULES.md`: exact accounting, matching, coverage and decision rules.
- `docs/04_ARCHITECTURE.md`: staged application architecture and data model.
- `docs/05_BRAND_AND_UI.md`: design direction, typography, layout, responsiveness, states and motion.
- `docs/06_BUILD_PLAN.md`: implementation stages and acceptance gates.
- `docs/07_TEST_AND_SECURITY.md`: domain, interaction, security and release tests.
- `docs/08_DEMO_SCRIPT.md`: owner-facing walkthrough and discovery questions.
- `docs/09_SOURCES_AND_ASSUMPTIONS.md`: source provenance and unverified assumptions.
- `docs/10_CHANGE_CONTROL.md`: change requests, stage records, definition of done.
- `brand/`: original vector marks, tokens and parent-brand provenance. No font files.
- `contracts/`: scope lock, domain JSON Schema, future backend API specification, acceptance matrix.
- `data/synthetic/`: canonical fictional inputs, results and supporting document excerpts.
- `spec-tests/`: runnable fixture checks plus application test specifications. These are not an implemented reconciliation engine.
- `reference/`: local HTML design reference, PNG baselines and viewport manifest.
- `prompts/`: checkpoint and read-only review prompts.
- `qa/`: actual handoff validation results. Future application tests remain unrun.

## Preview and fixture checks
Double-click `reference/index.html`, or optionally serve only this directory locally:
```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory handoff/reference
```
Then open `http://127.0.0.1:8765` locally. The reference does not upload files or make network requests.

From this handoff directory:
```sh
python3 -m unittest discover -s spec-tests -p 'test_*.py' -v
```
These checks validate the handoff's fictional data, expected amounts, partition totals and asset references, not a future app. Separate schema and browser-reference validation results are recorded in `qa/`.

## Important stage distinction
**Now authorized:** implement a functional, local synthetic demo after reviewing this kit, with real deterministic calculations on supplied synthetic records, working review decisions and demo-only imports.
**Not authorized:** real-data processing, live APIs, cloud spend, production authentication claims, automated invoice edits, sending messages, publishing Assist branding, commits/pushes/deployments, or introducing paid model usage.

A price is not a shipped feature. The earlier $2,500 diagnostic / $995 monthly idea remains a private pricing hypothesis. There is no public pricing page in v1.
