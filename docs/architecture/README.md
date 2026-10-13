# Architecture

ShiftClarity compares approved work and posted invoices against independently approved, effective contract terms. It publishes an explainable result, preserves the evidence used, and records the human review. Missing support becomes a coverage task with an unknown monetary value.

These C4 views describe the **deployed synthetic pilot**, not a proposed production platform. All records are fictional. The standalone `/demo/` experience remains a separate, memory-only demonstration.

## C4 level 1: system context

```mermaid
flowchart LR
    reviewer["Reviewer<br/>Person<br/>Examines findings and records decisions"]
    author["Rule author<br/>Person<br/>Registers source evidence and proposes terms"]
    approver["Independent approver<br/>Person<br/>Approves or rejects another person's draft"]
    operator["Workspace operator<br/>Person<br/>Prepares fictional records and provisions memberships"]
    sources["Contract, timekeeping and invoice records<br/>External source systems<br/>Represented by fictional normalized exports"]
    sc["ShiftClarity<br/>Software system<br/>Verifies alignment and preserves review evidence"]
    identity["AWS Cognito<br/>External identity system<br/>Private accounts and authenticator MFA"]

    reviewer -->|"Reviews evidence and exports decisions"| sc
    author -->|"Registers sources and drafts rules"| sc
    approver -->|"Independently reviews rule versions"| sc
    sources -.->|"Manual export preparation; no live connector"| operator
    operator -->|"Imports normalized synthetic JSON; manages access"| sc
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
        ui["Browser application<br/>Container: React and TypeScript<br/>Workspace, evidence, inputs, rules and coverage"]

        edge["Cloudflare Pages proxy<br/>Container: JavaScript Worker<br/>Fixed AWS origin, secure cookies and no private caching"]

        subgraph aws["AWS hosting boundary — us-east-1"]
            gateway["API Gateway HTTP API<br/>Infrastructure: HTTPS entry point"]
            web["Web function<br/>Container: FastAPI, Mangum and Node<br/>Sessions, authorization, imports and review API"]
            queue["SQS FIFO<br/>Infrastructure: job notifications<br/>One group per configured workspace"]
            worker["Worker function<br/>Container: Python and Node<br/>Claims durable jobs and publishes results"]
            objects[("Private S3<br/>Data store: original JSON bytes<br/>Quarantine and accepted objects")]
            secrets["Secrets Manager<br/>Infrastructure: restricted database credential"]
        end

        subgraph neon["Neon hosting boundary — isolated synthetic branch"]
            db[("PostgreSQL<br/>Data store: memberships, sessions, source revisions,<br/>rules, jobs, runs, receipts and audit history")]
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
