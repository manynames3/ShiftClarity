# Architecture

ShiftClarity compares approved work and posted invoices against independently approved, effective contract terms. It publishes an explainable result, preserves the evidence used, and records the human review. Missing support becomes a coverage task with an unknown monetary value.

The public root serves a static landing page from Cloudflare Pages; its dedicated `/landing/` assets do not invoke AWS.

These C4 views describe the **deployed synthetic pilot**, not a proposed production platform. All records are fictional. The standalone `/demo/` experience remains memory-only. Its separate `?view=files` evaluator accepts authorized minimized CSV/XLSX exports entirely in the browser; those records never enter the cloud containers below.

The CSV/XLSX onboarding and Excel/PDF reports extend these same containers in the **deployed synthetic MVP**, released October 23, 2026. See the [spreadsheet component view](#c4-level-3-spreadsheet-mvp) and [walkthrough](../SPREADSHEET_WALKTHROUGH.md). No new cloud service is introduced.

## C4 level 1: system context

```mermaid
flowchart LR
    reviewer["Reviewer<br/>Person<br/>Examines findings and records decisions"]
    author["Rule author<br/>Person<br/>Registers source evidence and proposes terms"]
    approver["Independent approver<br/>Person<br/>Approves or rejects another person's draft"]
    operator["Workspace owner / uploader<br/>Person<br/>Prepares exports and manages private access"]
    sources["Contract, timekeeping and invoice records<br/>External source systems<br/>Represented by fictional normalized exports"]
    sc["ShiftClarity<br/>Software system<br/>Verifies alignment and preserves review evidence"]
    identity["AWS Cognito<br/>External identity system<br/>Private accounts and authenticator MFA"]

    reviewer -->|"Reviews evidence and exports decisions"| sc
    author -->|"Registers sources and drafts rules"| sc
    approver -->|"Independently reviews rule versions"| sc
    sources -.->|"Manual export preparation; no live connector"| operator
    operator -->|"Imports synthetic CSV/XLSX; manages access"| sc
    sc -->|"Authorization-code sign-in and identity verification"| identity

    classDef person fill:#e6f3f4,stroke:#006C78,color:#142333;
    classDef system fill:#142333,stroke:#142333,color:#ffffff;
    classDef external fill:#f2f4f6,stroke:#667788,color:#142333;
    class reviewer,author,approver,operator person;
    class sc system;
    class sources,identity external;
```

The operator-supplied snapshots are the boundary with source systems. ShiftClarity does not edit invoices, connect to customer systems, or send evidence requests. A verified identity still needs an active workspace membership. The author cannot approve their own draft.

## C4 level 2: containers

In C4, a container is an application or data store. The web function and worker are separate runtime containers built from the **same Docker image**. AWS services are labeled as infrastructure so the diagram does not imply a collection of custom microservices.

```mermaid
flowchart TB
    user["Workspace participant<br/>Person"]
    cognito["AWS Cognito<br/>External identity system<br/>Authorization code and mandatory TOTP"]

    subgraph sc["ShiftClarity — software system"]
        ui["Browser application<br/>Container: React and TypeScript<br/>Imports, evidence, period history, follow-up and team setup"]

        edge["Cloudflare Pages<br/>Container: static landing and JavaScript Worker<br/>Public assets; fixed AWS proxy with secure cookies and no private caching"]

        subgraph aws["AWS hosting boundary — us-east-1"]
            gateway["API Gateway HTTP API<br/>Infrastructure: HTTPS entry point"]
            web["Web function<br/>Container: FastAPI, Mangum and Node<br/>Sessions, authorization, imports and review API"]
            queue["SQS FIFO<br/>Infrastructure: job notifications<br/>One group per configured workspace"]
            worker["Worker function<br/>Container: Python and Node<br/>Claims durable jobs and publishes results"]
            objects[("Private S3<br/>Data store: original JSON/CSV/XLSX bytes<br/>Quarantine and accepted objects")]
            secrets["Secrets Manager<br/>Infrastructure: restricted database credential"]
        end

        subgraph neon["Neon hosting boundary — isolated synthetic branch"]
            db[("PostgreSQL<br/>Data store: memberships, sessions, source revisions,<br/>rules, jobs, period reviews, cases, receipts and audit history")]
        end
    end

    user -->|"Uses HTTPS interface"| ui
    ui -->|"Sign-in redirect"| cognito
    ui -->|"Same-origin requests; session and CSRF on writes"| edge
    edge -->|"HTTPS; private edge credential; manual redirects"| gateway
    gateway -->|"Invokes"| web
    web -->|"Code exchange, token and MFA checks"| cognito
    web -->|"Serves application and assets through proxy"| edge
    web -->|"Transactions; verified TLS"| db
    web -->|"Private write, read and expiry-gated download"| objects
    web -->|"Sends job ID before database commit"| queue
    queue -->|"Invokes with retry and partial failure handling"| worker
    worker -->|"Claims, fences and atomically publishes"| db
    secrets -->|"Retrieved at cold initialization"| web
    secrets -->|"Retrieved at cold initialization"| worker

    classDef app fill:#e6f3f4,stroke:#006C78,color:#142333;
    classDef store fill:#f2f4f6,stroke:#667788,color:#142333;
    classDef infra fill:#ffffff,stroke:#667788,color:#142333;
    class ui,edge,web,worker app;
    class db,objects store;
    class gateway,queue,secrets,cognito infra;
```

The worker reads validated normalized data from PostgreSQL; it does not download the original S3 object to calculate a run. SQS wakes work, while PostgreSQL remains the authority for job status and publication. See the [import and publication sequence](import-publication.md) for failure and retry behavior.

The diagram omits supporting operations resources: a FIFO dead-letter queue and alarm, seven-day CloudWatch logs, ECR for the verified image, a private encrypted and versioned Terraform state bucket, and an account budget. Deployment uses a dedicated role; the application uses a separate restricted runtime role. A budget and endpoint throttling provide visibility and traffic control, not a hard spending cap.

## C4 level 3: web function components

The components below run within one web function. They are code boundaries, not independently deployed services.

```mermaid
flowchart LR
    browser["Browser application<br/>External container"]
    provider["Cognito<br/>External identity system"]
    db[("PostgreSQL<br/>External data store")]
    s3[("Private S3<br/>External data store")]
    sqs["SQS FIFO<br/>External infrastructure"]

    subgraph web["Web function — container"]
        routes["Routes and request controls<br/>Component: backend/app.py<br/>Strict bodies, permissions, limits and conflict checks"]
        auth["Identity and sessions<br/>Component: backend/auth.py<br/>OIDC, MFA, membership, session and CSRF"]
        imports["Import validation<br/>Component: backend/imports.py<br/>Quarantine, trusted sources, revisions and receipts"]
        engine["Shared engine adapter<br/>Component: backend/engine.py<br/>Bounded Node process running the TypeScript engine"]
        persistence["Transactions and audit<br/>Component: backend/db.py<br/>Organization scope, head locks and history"]
        storage["Private object adapter<br/>Component: backend/storage.py<br/>Opaque organization-scoped references"]
        jobs["Job notification<br/>Component: backend/jobs.py<br/>Durable job and FIFO wake-up"]
    end

    browser -->|"Calls API through Pages"| routes
    routes -->|"Verifies actor and request"| auth
    auth -->|"Validates identity and MFA"| provider
    auth -->|"Reads sessions and memberships"| persistence
    routes -->|"Accepts bounded synthetic upload"| imports
    routes -->|"Applies review and rule transitions"| engine
    routes -->|"Locks and commits state"| persistence
    routes -->|"Enqueues exact import run"| jobs
    imports -->|"Validates and normalizes input"| engine
    imports -->|"Records revisions and receipts"| persistence
    imports -->|"Quarantines and accepts bytes"| storage
    routes -->|"Streams authorized source"| storage
    persistence -->|"Uses scoped SQL transactions"| db
    storage -->|"Uses private object operations"| s3
    jobs -->|"Sends FIFO notification"| sqs
```

## Boundaries that matter

| Boundary | Implemented behavior | Practical limit |
| --- | --- | --- |
| Identity to workspace | Cognito identity verification plus active server-side membership and role checks | Sign-in does not establish permission to use a workspace. |
| Browser to API | Short server sessions; exact Origin and session-bound CSRF checks on writes | The local provider is loopback-only development infrastructure. |
| Pages to AWS | Fixed upstream, exact gateway host and private edge credential; redirects are not followed by the proxy | Edge identity grants no user permission. Preview hosts are denied; the record-free health endpoint remains public. |
| API to data | Restricted nonowner PostgreSQL role; forced RLS on organization-scoped evidence/workflow tables | Identity/session tables use server checks. This synthetic single-workspace build is not evidence of a multi-customer operating model. |
| Upload to trusted evidence | Bounded exact-schema JSON, registered rule/source matching, revision conflicts and private quarantine | A synthetic declaration cannot classify or authorize real personal information. |
| Calculation to publication | Shared exact-decimal engine; immutable completed run, head update and audit event committed together | Missing or unsupported evidence can require abstention rather than a financial finding. |
| Runtime to historical records | Database permissions and triggers prevent application edits to immutable records | Administrators retain maintenance authority; there is no cryptographic tamper-evidence or S3 Object Lock claim. |

## Code and decision map

| Area | Source | Decision |
| --- | --- | --- |
| Shared calculations | [TypeScript engine](../../src/domain/engine.ts), [server adapter](../../src/adapters/server-cli.ts), [Python boundary](../../backend/engine.py) | [ADR 0001](../adr/0001-shared-deterministic-engine.md) |
| Event-driven deployment | [Lambda handlers](../../backend/lambda_handler.py), [jobs](../../backend/jobs.py), [Terraform](../../infra/main.tf), [Dockerfile](../../Dockerfile) | [ADR 0002](../adr/0002-event-driven-aws-pilot.md) |
| Authentication and approval | [Authentication](../../backend/auth.py), [API](../../backend/app.py) | [ADR 0003](../adr/0003-cognito-and-server-authorization.md) |
| Persistence and isolation | [Transactions](../../backend/db.py), [schema](../../backend/migrations/001_initial.sql) | [ADR 0004](../adr/0004-neon-postgres-and-rls.md) |
| Imports and evidence | [Import boundary](../../backend/imports.py), [storage](../../backend/storage.py), [import immutability](../../backend/migrations/003_import_immutability.sql) | [ADR 0005](../adr/0005-private-versioned-evidence.md) |

The [ADR index](../adr/README.md) records why these choices were made. [Phase 4 controls](../PHASE_4.md), the [threat model](../THREAT_MODEL.md), and [implementation evidence](../../IMPLEMENTATION_STATUS.md) provide the detailed verification and remaining gates. Real customer data, approved retention and incident operations, independent evaluation, and production approval remain separate requirements.

## C4 level 3: spreadsheet MVP

These components run inside the existing React browser and FastAPI container. PostgreSQL/S3 are the existing storage boundaries; local checks use isolated PostgreSQL and private local files.

```mermaid
flowchart LR
  finance["Finance reviewer"] --> ui["Guided import and mapping<br/>React: ImportWorkbench"]
  approver["Independent approver"] --> ui
  ui --> scope["Session, scope and permissions<br/>workbench.py + auth.py"]
  scope --> parser["Bounded parser subprocess<br/>tabular.py + table_cli.py"]
  parser --> mapping["Confirmed mappings<br/>table_mapping.py"]
  mapping --> bundle["Canonical source selection<br/>table_bundle.py"]
  bundle --> approval["Serialized rate approval<br/>shared rate-approval.ts"]
  approval --> imports["Existing immutable import pipeline<br/>imports.py"]
  imports --> jobs["Existing durable job/publication<br/>jobs.py + shared engine"]
  jobs --> review["Existing evidence and review API"]
  review --> reports["Selected-period evidence reports<br/>reports.py"]
  reports --> downloads["Literal Excel / branded PDF"]
  scope --> db[("PostgreSQL<br/>Forced workspace RLS<br/>sessions/files/profiles + existing evidence")]
  imports --> db
  jobs --> db
  reports --> db
  scope --> private[("Private originals<br/>Quarantine / accepted storage")]
```

A spreadsheet mapping never grants approval or changes the engine's financial rules. Original files and unmapped previews are not report content. Accepted previews are removed; current reports draw on normalized evidence and hashed references. See [ADR 0007](../adr/0007-confirmed-spreadsheet-adapters.md), [ADR 0008](../adr/0008-current-review-evidence-reports.md) and the [billing matrix](../BILLING_CAPABILITIES.md).

## C4 level 3: recurring review and team access

These components extend the same React, FastAPI and PostgreSQL containers. They add no cloud service. See [ADR 0009](../adr/0009-periods-and-follow-up.md) and [ADR 0010](../adr/0010-owner-managed-access.md).

```mermaid
flowchart LR
  owner["Workspace owner<br/>Person"] --> setup["Workspace and team UI<br/>React: AgencySetup"]
  staff["Billing reviewer / assigned colleague<br/>Person"] --> history["Period history and follow-up UI<br/>React: Workflow + ServerApp"]
  setup --> access["Owner authorization and membership management<br/>onboarding.py + auth.py"]
  access --> cognito["Existing Cognito pool<br/>Suppressed invitation; password change; TOTP"]
  access --> members[("PostgreSQL<br/>agency_settings + memberships + sessions")]
  history --> api["Period and follow-up API<br/>workflow_api.py + app.py"]
  api --> reviews[("PostgreSQL<br/>review_workspaces + billing_cases + case_events")]
  publish["Existing durable publication<br/>jobs.py + shared engine"] --> sync["Evidence-based case verification<br/>workflow.py"]
  publish --> snapshots[("PostgreSQL<br/>immutable completed_runs")]
  sync --> reviews
  api --> reports["Selected-period reports<br/>reports.py"]
  reviews --> reports
  snapshots --> reports
```

```mermaid
sequenceDiagram
  actor Reviewer
  participant UI as Selected-period browser
  participant API as FastAPI
  participant DB as Existing PostgreSQL
  participant Worker as Existing SQS worker
  Reviewer->>UI: Record correction reference
  UI->>API: CSRF-protected, versioned case action
  API->>DB: Save case and append event atomically
  Reviewer->>UI: Import corrected source exports
  UI->>API: Validate, accept and request run
  Worker->>DB: Publish immutable result and period workspace
  Worker->>DB: Check every affected work reference
  alt All affected financial records evaluate aligned
    Worker->>DB: Resolve case with verification run reference
  else Evidence incomplete, missing or still discrepant
    Worker->>DB: Retain unresolved follow-up
  end
  Reviewer->>UI: Open an earlier period and download report
  UI->>API: Selected run ID
  API->>DB: Read period decisions and latest scoped follow-up
  API-->>UI: Private PDF/XLSX; original financial evidence retained
```

## C4 level 3: browser-local prospect evaluation

```mermaid
flowchart LR
  user["Agency billing specialist · Person"]
  sources["Existing ATS / VMS / billing / approved terms · External systems"]
  subgraph browser["Prospect browser · Container"]
    mapping["Local CSV reader / bounded XLSX worker and confirmed mappings · Component"]
    engine["Existing exact TypeScript reconciliation engine · Component"]
    review["Findings, evidence and local decisions · Component"]
    reports["XLSX / CSV / print-save PDF and opt-in mapping metadata · Component"]
    mapping --> engine --> review --> reports
  end
  sources -.->|"User exports authorized minimized files"| user
  user -->|"Selects local files; confirms meanings and scope"| mapping
  reports -->|"Explicit download; refresh clears memory"| user
  edge["Cloudflare / AWS · Existing containers · Static application and fictional examples only"]
  edge -->|"GET application assets; no source rows returned"| browser
```

```mermaid
sequenceDiagram
  actor Agency as Agency billing specialist
  participant Browser as Browser-local evaluator
  participant Engine as Shared exact engine
  participant Cloud as Existing cloud host
  Browser->>Cloud: GET application assets / optional fictional examples
  Agency->>Browser: Select authorized CSV/XLSX files and explicit mappings
  Browser->>Browser: Bounded parse, source SHA-256, row corrections, totals
  Browser->>Engine: Validated canonical records and supplied declarations
  Engine-->>Browser: Both billing directions, allocations and unknown-value gaps
  Agency->>Browser: Review and explicitly download report
  Note over Browser,Cloud: No source records, results or local reviews are uploaded
```

[ADR 0011](../adr/0011-browser-local-agency-evaluation.md) records why this path does not imply customer-cloud approval or a vendor connector. [Agency adoption research](../AGENCY_ADOPTION.md) maps the source evidence and testable assumptions.


The browser-local evaluation component now includes file-first preparation (`LocalFiles`), deterministic header/period/source guidance (`local-guidance`) and direct approved-term entry (`RateEntry`). All feed the existing confirmed LocalSource adapter and shared engine; no new container, network boundary or persistent store is introduced. See [ADR 0012](../adr/0012-guided-local-preparation.md).
