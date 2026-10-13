# ADR 0004: Use Neon PostgreSQL with a restricted runtime role

- **Status:** Accepted for synthetic use
- **Date:** October 13, 2026
- **Scope:** Isolated Free-plan branches; no paid upgrade or customer records

## Context

Reviews, immutable evidence, durable jobs and idempotency need transactions and persistent history. The user preferred low idle cost and allowed Neon when justified. PostgreSQL also supports a local development and recovery path without a second data model.

## Decision

Use managed PostgreSQL on an isolated Neon Free branch for the cloud pilot, separate from the local identity/storage environment. Connect from Python through Psycopg with verified TLS. Neon hosts PostgreSQL; Psycopg is the client driver, so the two are complementary.

Keep sessions, memberships, imports, source revisions, lineage, rules, jobs, completed runs, receipts and audit history in PostgreSQL. The application login owns no tables and has neither superuser nor `BYPASSRLS` privilege. Organization-scoped evidence and workflow tables have forced row-level security; each transaction supplies its organization scope. Identity and session tables rely on explicit server checks.

Use row locks, optimistic versions, fingerprints and receipts for concurrent writes. Database triggers and grants prevent the runtime role from rewriting immutable evidence. Owner credentials are reserved for migration, retention and isolated recovery operations.

## Alternatives considered

- **Always-running managed database capacity:** a possible later operating choice, but unnecessary for this intermittent synthetic workload.
- **Embedded local database:** useful for a small demo, but does not exercise the managed persistent pilot and PostgreSQL controls.
- **A second queue database:** unnecessary because PostgreSQL already owns transactional jobs and publication.

## Consequences

The current Free branch is constrained and capped at 0.25 CU; database wake-up adds latency after inactivity. No idle polling keeps it awake. Automatic idle behavior was observed rather than inferred from advertised settings. Neon charges are separate from AWS credits, and a Free plan is not a permanent production cost commitment.

The short restore-history window does not replace an approved backup policy. An isolated database-and-source restore rehearsal is evidence of a tested procedure, not a production RPO/RTO. RLS and runtime checks add boundaries, but the current synthetic single-workspace build does not establish multi-customer capacity, security or operations.

## Implementation and verification

[Transaction scope](../../backend/db.py), [core schema and forced RLS](../../backend/migrations/001_initial.sql), [document policy](../../backend/migrations/002_documents.sql), and [runtime checks](../../backend/app.py). [Implementation status](../../IMPLEMENTATION_STATUS.md) records runtime-role, isolation, idle and restore checks; [pilot gates](../PILOT_GATES.md) retain the real-data requirements.
