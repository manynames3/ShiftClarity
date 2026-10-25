# Fictional agency evaluation

Use work.csv, invoices.csv and rates.csv together. These are invented, minimized fixtures, not genuine vendor exports or proof of compatibility.

- Service dates: October 5–11, 2026 (both inclusive).
- Files current through: 2026-10-14T00:00:00Z. Billing cutoff: 2026-10-13T00:00:00Z.
- Declare both sources complete only for this fictional scope. Independent totals: 69 work hours and USD 3,501.00 signed posted invoice amount.
- Rate author: AUTHOR-1. Independent approver: APPROVER-2. These are supplied declarations for local testing.
- Map Minutes as minutes, statuses and component values explicitly. Billing Basis non_hourly means outside hourly scope.
- Expected: 8 work records; 6 evaluated (54 of 69 hours), USD 460.00 potential underbilling and USD 24.00 potential overbilling. W4 is missing from a declared-complete invoice export. W7 is pending; W8 callback has no applicable rate. Neither has a financial estimate.
- USD 25.00 non-hourly fee stays in source totals but is not compared to hourly terms. W6 original/credit/rebill nets to USD 700.00.
- Actual approval-event timestamps are unknown; Status Observed Date explicitly records the approved status observation.

Bullhorn-style and Avionté-style files illustrate documented field shapes only. The weekly summary deliberately cannot become dated service records. Bullhorn charge IDs and quantity units require verification before mapping; row-level unique IDs, facility IDs, component basis and approved-status observation may require a detailed/minimized export.

Change one invoice amount by USD 10 and verify the corresponding difference changes by USD 10. Uncheck invoice completeness and verify missing evidence never becomes a financial estimate. Remove a credit-chain ID and verify a coverage gap replaces that calculation. Export the report and inspect source references and limitations.
