# ADR 0011: Browser-local prospect export evaluation

Status: accepted for the user-authorized own-file evaluation; release evidence in VERIFICATION.md. October 24, 2026.

## Context
Prospects need to see value from their exports before obtaining private accounts or approving customer records for our AWS/S3/Neon environment. Primary vendor documentation supports detailed exports but does not establish native connector compatibility. The existing cloud pilot remains synthetic.

## Decision
Add a lazy-loaded browser-local CSV/XLSX adapter and confirmed mapping UI. Use the existing exact TypeScript engine and report/review UI. Keep records in React memory; download mapping metadata only at the user’s explicit action. Never upload files or derived records. Use native print/save PDF, the existing formula-safe CSV report and a locally generated literal-cell XLSX report. The existing private Python/OpenPyXL adapter continues supporting synthetic CSV/XLSX and authenticated persistence.

Generate column/enum/privacy metadata from the Python adapter and cross-check both implementations on the same independently specified fictional financial cases. Header suggestions are not authority. Date/unit/code confirmation, supplied source totals and completeness remain explicit. Separate approval-event dates from observed source status. Explicit non-hourly charges remain in source totals but have no hourly comparison; unsupported components remain evidence gaps.

## Consequences
One explicitly approved production dependency: SheetJS CE 0.20.3 from the official distribution archive with lockfile integrity and Apache-2.0 notices. It runs in a lazy browser worker; ZIP metadata/expansion, XML active content, sheet visibility, grids and text are bounded, and the worker is terminated after eight seconds. No database migration or new cloud service. Local declarations cannot provide authenticated segregation of duties. Native integrations, customer-cloud ingestion, ongoing retention and measured customer accuracy require separate acceptance. Neither workbook parsing nor local report generation uses a runtime CDN or any model/network service.

Mapping metadata includes headers, code translations and fixed values and must be kept private; it is not an anonymization guarantee. Neither header checks nor a local-only processing boundary can detect all sensitive input. UI and documentation require authorized minimized records and do not claim HIPAA certification. Existing private account, source-retention, permission, MFA and immutable-run boundaries are unchanged.
