# Make the standalone demo feel like a finished review workspace

The standalone demo now presents a clear reviewer workflow: surface potential billing differences, inspect the evidence, and keep coverage gaps visible. The demo remains fictional and local; calculation behavior and expected values are unchanged.

- Add one dismissible fictional-data banner with in-banner reset.
- Replace duplicate navigation with one responsive sidebar and mobile drawer.
- Lead with total impact and a prioritized, sortable findings table.
- Replace internal codes and role IDs with plain-language labels and names.
- Standardize date ranges and timestamps across views.
- Raise the type scale and verify WCAG AA contrast in light and dark modes.
- Add responsive loading/error/empty states, undoable review feedback, keyboard shortcuts, and a system-aware manual theme toggle.
- Add fictional owner, priority, and age labels as display-only metadata for synthetic findings.

Validation: `npm test` (80 passed), `npm run build`, and `npm run test:e2e` (39 passed). The screenshot set in [docs/images/README.md](images/README.md) includes before/after Workspace, Evidence, Coverage, mobile Workspace, and a 1920×1080 Workspace capture.
