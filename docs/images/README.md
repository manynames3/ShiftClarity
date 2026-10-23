# Product screenshots

## Spreadsheet MVP · October 23, 2026

Actual local browser captures with fictional files. Test sessions are provisioned only in a disposable database; these are not new Cognito/cloud captures. The approved bright visual system remains shared with the original demo.

| File | View/state |
|---|---|
| [mvp-onboarding.png](mvp-onboarding.png) | Loaded facility/period and explicit coverage setup, 1440×1000 |
| [mvp-mapping.png](mvp-mapping.png) | Real XLSX worksheet/header, column suggestions and value mappings, 1440×1000 viewport |
| [mvp-workspace.png](mvp-workspace.png) | Nineteen accepted source records; 6/8 work evaluated; $200 derived potential difference; persisted confirmation and report controls, full page |
| [mvp-import-mobile.png](mvp-import-mobile.png) | New import flow at 390px, with confirmed mappings collapsed |
| [mvp-report.png](mvp-report.png) | Render of page one of the actual downloaded, three-page fictional PDF |

All five images were inspected. The report was generated from current server review state, not a mocked design. See the [full PDF](../examples/fictional-billing-review.pdf) and [filterable Excel](../examples/fictional-billing-review.xlsx); notes and worker identity fields are omitted by default. Earlier screenshots below are historical and remain labeled.


## Current approved overview · October 16, 2026

These are unmodified 1505×1045 browser captures of the production frontend build running locally with the standalone synthetic fixture. They show the approved open overview and shared horizontal navigation. They do not depict an authenticated or persisted pilot session. The signed-in pilot shares these components and styles.

| File | View and state |
|---|---|
| [review-workspace.png](review-workspace.png) | Two findings awaiting review, prominent potential-underbilling summary, coverage in the right margin |
| [finding-evidence.png](finding-evidence.png) | $2,600 expected, $2,400 invoiced, $200 potential difference, source text and decision controls |
| [review-coverage.png](review-coverage.png) | 12/14 records and 124/148 hours checked; unsupported callback and pending approval retain unknown value |
| [approved-inputs.png](approved-inputs.png) | Validated synthetic source batches and immutable rule versions |
| [rule-approval.png](rule-approval.png) | Pending October 13 proposal with source/predecessor and self-approval denial |

The [approved image](../design-reference/README.md) is stored separately from implemented screenshots. Dates, SVG branding and role labels in the app come from the real fixture and product semantics rather than generated concept text.

## October 15 standalone demo polish · before and after

The before captures show the local standalone demo before the eight-item polish. The after captures show the finished local demo with the same fictional records; all outcome values and engine behavior remain unchanged. The 1440×1080 Workspace captures show the complete findings table in the first viewport. Evidence and Coverage are full-page captures; mobile Workspace is a 390×844 viewport capture. The additional 1920×1080 Workspace capture verifies the wide desktop layout.

| View | Before | After |
|---|---|---|
| Workspace | [1440×1080](before-demo-workspace-1440.png) | [1440×1080](after-demo-workspace-1440.png) · [1920×1080](after-demo-workspace-1920.png) |
| Evidence | [1440×1080](before-demo-evidence-1440.png) | [full page, 1440px wide](after-demo-evidence-1440.png) |
| Coverage | [1440×1080](before-demo-coverage-1440.png) | [full page, 1440px wide](after-demo-coverage-1440.png) |
| Workspace · mobile | [390×844](before-demo-workspace-390.png) | [390×844](after-demo-workspace-390.png) |

The standalone demo’s owner, priority and age labels are illustrative workflow metadata for the two fictional findings only. They do not change the calculation. The historical October 13 AWS captures remain in local ignored artifacts; the published current images above replace those older images.
