# ShiftClarity workspace instructions

This file is intended to become `AGENTS.md` at the root of a NEW ShiftClarity application workspace. Do not overwrite unrelated existing instructions.

The canonical build handoff lives in `./handoff/`. Before implementation, read and apply `handoff/AGENTS.md`, `handoff/contracts/scope-lock.json`, the numbered requirements/domain/design docs, and `handoff/docs/06_BUILD_PLAN.md`. Resolve paths inside handoff instructions relative to `handoff/` unless explicitly stated otherwise.

Current authorization: LOCAL SYNTHETIC DEMO ONLY, stages 0–3. No real customer records, cloud provisioning, paid APIs, live integrations, source-system edits, outgoing messages, commits, pushes or deployment.

Do not restyle or broaden the product. Match the supplied ShiftClarity SVGs, design tokens and canonical interface references. Calculate results from synthetic inputs; expected results are a test oracle, never an implementation shortcut. Keep coverage, unknown values, effective dates and independent rule approval intact.

At every checkpoint, update IMPLEMENTATION_STATUS.md, map work to acceptance IDs, run the relevant tests, inspect screenshots and record deviations. Do not claim completed application tests or security properties without evidence. Stop at the demo release gate; report remaining pilot requirements.
