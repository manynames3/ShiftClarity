# ShiftClarity agent instructions

## Mission
Build a credible, evidence-first healthcare staffing verification demo, not a generic dashboard and not a replacement staffing system. Preserve Supreme AI Ventures' brand family with ShiftClarity's own mark. Optimize for a billing lead's trust and an owner's comprehension.

## Scope and authority
Read `contracts/scope-lock.json` and the numbered docs BEFORE changing application files. This handoff is reference material, not the app. Work in a separate new app repository; never modify `manynames3/supremeai` or unrelated projects. Inventory an existing target workspace before using it and preserve unrelated work. Do not overwrite its instructions silently.

Do not create a new feature, service, dependency family, user role or public claim simply because a template includes it. For unresolved material ambiguities, log the question in `DECISIONS.md`; proceed only with independent safe work. Minor decisions may use a clearly recorded reversible default. Never weaken a correctness or safety requirement to match a screenshot.

## Stage lock
Current authorization = LOCAL_SYNTHETIC_DEMO. Implement no real-data ingress, live system integration, cloud provisioning or external communications. Demo upload accepts only the provided synthetic fixture formats/content, with conspicuous synthetic labels. Never imply fixture-only import is a production importer.

No commit, push, deploy, publish, mass download, real email, production credential request or paid API call without explicit permission. Keep sensitive records out of consumer/subscription model tools. Existing Codex/Claude subscriptions do not supply application API credits.

## Product invariants
- Money and rates travel as decimal strings; use a decimal library/server Decimal. Never binary floating-point accounting.
- Contract service dates, approval dates and recorded dates are different facts.
- A clean queue is not a clean bill of health. Always show coverage, gaps, freshness and the scope of each run.
- Missing invoice coverage, unsupported components, conflicting terms and ambiguous identity cause explicit abstention, not invented discrepancies.
- A finding is not confirmed savings or recovered cash.
- Keep underbilling and overbilling visible separately. Deduplicate overlapping impacts rather than netting them into a misleading opportunity total.
- Rule authors cannot approve their own rule. Server authorization, immutable versions and durable audit are required before real data.
- No automatic invoice/payroll/contract changes or messages.
- No fake certifications, compliance badges, client testimonials, uptime figures or competitor-superiority claims.

## Design invariants
Use the provided logo, tokens and canonical HTML. Do not substitute a generic shield/checkmark logo, purple AI gradient, money-focused hero, stock medical photo, glass panels, decorative analytics charts, oversized rounded cards, dense icon rail, or chatbot-first layout. No stock dashboard theme. Use custom tokens even if accessible primitives come from a library.

Apply the exact information hierarchy before adding decoration. Use readable text, consistent alignment, row-level explanations, keyboard paths, text status labels, an evidence panel and a persistent synthetic banner. No unexplained AI confidence score. Never hide a denominator or unknown value behind a tooltip alone.

## Implementation discipline
Work checkpoint by checkpoint from `docs/06_BUILD_PLAN.md`. No one-shot full platform generation. Share domain types, fixtures and status labels across front and back. Engine results are computed, not copied from `expected_results.json`; expected results are the independent oracle.

Before each checkpoint, list touched files, tests and acceptance IDs. After each checkpoint, run the relevant checks and report exact results. Capture browser screenshots at the reference viewports, inspect them, and fix overflow/drift. A static PNG is not evidence that a workflow works.

Run end-to-end tests for visible controls. Buttons must work within scope, be disabled with an explanation, or be removed. Never simulate a successful upload, approval, send or connection that did not occur. In the static reference, illustrative buttons explain the planned action; the real demo must implement its approved transitions.

Choose current supported stable dependencies when scaffolding and record versions/lockfiles. Do not install arbitrary plugins or unsupported prereleases. No global package changes. No unnecessary microservices, Redis, queues-as-a-service, vector store, LLM agents or live model dependency.

For independent review, use the user's installed `claude-review` workflow if available and explicitly authorized, in read-only mode with subscription cost checks. Do not invent a successful review or bypass its checks. Codex owns verification and merge decisions.

## Delivery honesty
Separate: implemented / exercised / tested / not tested / gated. Supply known limitations and exact commands. Never label a synthetic demo "production-ready", "HIPAA compliant", "SOC 2 certified", or "better than competitors". Keep `IMPLEMENTATION_STATUS.md` current and include a reset-demo control.
