# ADR 0012: Guide local preparation without inferring billing authority

Date: 2026-10-31. Status: accepted for the user-authorized file-first release.

The local evaluator already had strict parsing and reconciliation but exposed period settings before files and required users to translate exports without seeing actual row examples. Preparing a separate rate register and converting local reporting cutoffs to UTC added first-review friction.

Keep the existing browser-memory boundary and shared reconciliation engine. Add bounded CSV header suggestions, source-structure diagnostics, row/field previews, explicit period suggestions, timezone conversion and a direct approved-terms editor. Entered rates become the same LocalSource shape and undergo mapping confirmation, source checks and reconciliation. They have no fabricated original-file hash. No new service or production dependency is required.

Suggestions never establish completeness, approval authority, status meaning, units or unknown contract policy. Existing privacy guards run during header detection; repeated totals/headers and bad rows are retained as errors. A recognized vendor structure is not certified compatibility. Ambiguous service dates remain unresolved; repeated or missing DST times require the exact UTC source timestamp. Local rate declarations remain unauthenticated.

This reduces preparation steps while preserving inspectable evidence. It adds a small preparation helper and rate form inside the existing frontend component, without changing the C4 deployment boundary or private pilot permissions. Actual unassisted billing-user completion remains an external acceptance result; software tests and proposed timing targets cannot substitute for it.
