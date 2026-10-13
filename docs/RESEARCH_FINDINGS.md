# User complaints and implementation response

Research date: October 12, 2026. Review statements are self-reported, vendor/version/context-dependent observations. Search snippets were available; direct review-page retrieval returned unsupported-content errors. These are discovery hypotheses, not a validated problem at Assist, measured prevalence or a claim that ShiftClarity outperforms existing tools.

| Signal and source | Bounded response in this build | Evidence |
|---|---|---|
| Reporting limits are described in the [G2 staffing category](https://www.g2.com/categories/staffing). | Explicit checked-record/minute denominators, run source selection, coverage tasks and a reviewed-only CSV with traceable IDs. | Domain partitions, review export and browser tests. |
| Navigation, search and duplicate-detection complaints appear in that same category. | Deterministic filters, visible counts/clear action, direct evidence navigation, exact source IDs, duplicate snapshot idempotency and conflict rejection. | Filter, duplicate and conflicting revision tests. |
| Some [Bullhorn reviewers on Capterra](https://www.capterra.com/p/140531/Bullhorn-Recruiting-Software/reviews/) describe session interruption and limitations in standard reporting. | Review dialogs preserve focus and scoped evidence history during the current session; export makes review output inspectable. **The standalone demo remains memory-only; phase 4 now persists reviews/runs in Neon.** | Keyboard/dialog and export tests. Durable reload and local/Neon restore checks are recorded in the phase 4 evidence. |
| [Avionté's own product page](https://www.avionte.com/payroll-billing/) describes integrated time capture, payroll and invoicing. | Preserve the independent verification scope instead of recreating scheduling/payroll. Verify the customer's licensed product/configuration before asserting incremental value. | No live connector or source-system write. |

The original fixtures already address high-value error classes: effective-date drift, late-entry false alarms, missing approvals, unsupported terms, incorrect aggregate matching and unsigned credit handling. These are tested fictional cases, not quantified competitor defects. The own-data extension adds strict schema validation, source totals and preview-before-publication to make data problems visible.

Not inferred: William's recurring problem, his installed modules, legal agreement precedence, actual source completeness, willingness to pay, precision/recall on real records, or competitor superiority. Those remain discovery/evaluation gates.
