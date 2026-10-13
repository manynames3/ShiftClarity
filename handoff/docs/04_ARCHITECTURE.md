# 04 · Staged architecture

## Stage A: local synthetic demonstration (authorized)
React + TypeScript + Vite; custom design tokens; accessible primitives only where useful; a framework-independent typed domain module; a decimal library; Vitest/component tests and Playwright browser tests. Use supported stable versions resolved when building, not an unverified template or prerelease. Commit exact lockfiles only when commits are later authorized; generating lockfiles locally is expected.

Read bundled synthetic assets. Store demo decisions in memory or namespaced localStorage with a clear reset and synthetic-only warning. Do not put real records in browser storage. An explicit adapter maps input files into domain types; no loose `any` data or direct CSV-to-table wiring. Derive UI summaries from the domain results, not a duplicated UI metrics object.

Suggested new repo layout:
```text
handoff/                 # this kit, retained as reference
apps/web/src/
  app/                   # routes, shell, demo role switch, error boundary
  features/workspace/
  features/evidence/
  features/inputs/
  features/rules/
  features/coverage/
  components/            # shared semantic UI primitives
  adapters/              # fixture input and future API adapter boundary
packages/domain/src/     # pure types, validation, matching, rules, calculations
packages/domain/tests/
tests/e2e/
docs/DECISIONS.md
docs/IMPLEMENTATION_STATUS.md
```
Avoid over-engineered monorepo tooling; ordinary workspaces are sufficient. A simpler single package with separated domain folders is acceptable if recorded and tested. The Python backend is NOT needed just to render the demo.

## Stage B: single-customer secured pilot (separate approval)
Keep the UI. Introduce one FastAPI application, PostgreSQL, private object storage, a durable worker from the same backend codebase, and a trusted identity provider with MFA. An approved deploy environment and budget are prerequisites. An AWS-oriented implementation is compatible, but do not provision it now or assume a cloud provider's eligibility alone makes the application compliant.

Core calculation authority moves server-side. The frontend displays server results and never authorizes or publishes financial decisions independently. Keep one authoritative engine; any frontend preview must be a separately labeled preview and parity-tested. Do not maintain two disagreeing business-rule implementations.

The API YAML describes the stable boundary. Authentication is intentionally not implemented in the static reference or synthetic stage. In pilot mode, remove the demo role switch entirely; derive organization/permissions from verified identity. A client-supplied tenant ID never grants access.

## Data records (logical model, not migrations)
- Organization, User, Membership: customer boundary and roles; owner read-only, operator/importer, rule author, rule approver, billing reviewer. Permissions may combine but author != approver for the same rule.
- SourceConnection: export type, declared semantics, allowed columns and access authorization (not necessarily a live connector).
- ImportBatch: content hash, source, snapshot range, source_as_of, received_at, expected/control totals, status and quarantine report.
- SourceRecordRevision: stable external key, source revision, normalized content hash, effective snapshot scope, batch lineage.
- Document / Excerpt: private object reference, page or line anchoring, content digest, permitted viewers and retention class.
- RuleVersion: scope, component, exact rate, effective bounds, recorded/approved times, source excerpt, supersedes ID, immutable approval.
- WorkRecord: worker pseudonym, assignment/facility/role, service interval/timezone, integer minutes, approval state and source revision.
- InvoiceLine: invoice/document IDs, type, state, signed decimal amount, component, reference IDs and correction-chain links.
- Allocation: many-to-many signed amount/quantity relationships with source-line reconciliation constraints.
- ReconciliationRun: immutable source/rule/calendar/engine manifest, status, coverage summary, publication time.
- Finding / CoverageTask: logical identity, evidence fingerprint, reason code, inputs, signed impact or null, run reference.
- ReviewEvent: actor, permission, action, reason, optimistic version, prior fingerprint and event timestamp.
- AuditEvent: controlled append-only trail for import/rule/review/download/export actions. "Append-only" is an enforced control, not a frontend label.

## Run lifecycle and concurrency
`queued → validating → reconciling → completed` or `failed`. A completed run may have limited coverage; job completion and data completeness are separate fields. Compute into a draft run, validate invariants, then publish atomically. Readers see either a prior completed run or the new completed run, never half of both.

A small PostgreSQL-backed job table with row locking and retry visibility is sufficient initially. Idempotency keys cover import requests, jobs and decision submissions. Reject stale review writes with an explicit conflict (409); refresh evidence and require reconfirmation. Reference the specific run/fingerprint being approved. Never allow two reviewers to silently overwrite each other's decision.

## Input/storage controls before pilot
Minimize before transfer. Restrict upload types and file sizes, validate content not only extensions, separate quarantine from accepted storage, never execute uploaded content, use least-privileged parsers, limit resource use, and track retention. Short-lived authorized downloads are derived from access checks; public object links are prohibited.

Keep original accepted sources only for the approved retention period. "Immutable" means unaltered while retained, not kept forever. Deletion, legal hold, backup expiry and audit metadata policy must reconcile explicitly. Raw PHI/PII, contracts and unfiltered parser errors must not enter logs, analytics or model prompts.

## Simplicity constraints
No Kubernetes, Kafka, vector database, multi-agent pipeline, OCR/LLM extraction pipeline, bespoke authentication, event-sourcing framework, fintech ledger service or multi-region design for the demo. Do not add a Redis/Celery stack until measured needs justify it. No shipping a local demo role switch as security.

## Operations before real data
Define access revocation, support owner, alerts, incident contact, dependency patching, secrets management, backup/restore validation, source expiry/deletion and failed-import recovery. Set actual service/recovery targets with the client and budget; do not invent an SLA in UI. Recovery tests must restore consistent source references and decisions, not just a database that starts.
