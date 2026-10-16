# Synthetic staffing reconciliation exercise

This vendor-neutral bundle is a manual walkthrough and regression sample for the supported normalized JSON format. Every facility, worker, agreement, shift, invoice and amount is fictional. It contains no patient or personal data.

## Run the walkthrough

Open the [standalone demo](https://shiftclarity.pages.dev/demo/) and choose **Load synthetic fixture files**. The demo has built-in changed-invoice, incomplete-source, invalid-row and no-findings scenarios. To exercise the server import path, an assigned reviewer/importer can open the signed-in pilot, choose **Inputs & rules → Import synthetic snapshot**, and upload [`bundle.json`](bundle.json). The file follows the current 1 MiB normalized JSON template; it is not a vendor export.

## Expected baseline

The independent oracle is [`expected-results.json`](expected-results.json). The baseline should show:

- 14 shifts received; 12 evaluated (124 of 148 hours).
- 6 aligned shifts and 6 flagged shifts.
- Two review findings: **+$200** for a rate mismatch and **+$1,560** for approved work absent from the declared complete invoice extract. Total potential underbilling: **+$1,760**.
- One unsupported callback and one pending time approval. Both remain unestimated; the amount is unknown.
- A credit/rebill allocation and a late-entered shift are included in the source records.

Check the finding source tabs, affected shift IDs, hourly-rate math, coverage categories, and the fact that a review decision records a judgment without changing an invoice or asserting collection.

The calculation test in `src/adapters/custom.test.ts` runs this exact bundle through the shared parser and reconciliation engine and compares it with the separate expected-results file. Passing it establishes consistency for these declared cases; it does not establish accuracy on any customer's data.
