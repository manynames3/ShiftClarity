# ADR 0005: Accept bounded private imports and preserve evidence versions

- **Status:** Accepted
- **Date:** October 13, 2026
- **Scope:** Fictional normalized JSON and controlled source/rule authoring

## Context

A useful finding must explain which work, invoice and approved terms produced it. Input files are untrusted and cannot establish their own approvals. Retrying an upload must not duplicate amounts, while a new failed attempt must not leave an earlier result looking current.

## Decision

Accept one complete normalized JSON snapshot, at most 1 MiB and 2,000 rows per collection. Require the synthetic declaration and exact field allowlist. Validate schema, supported values and source control totals. Reject names, patient/clinical fields and unsupported formats; arbitrary vendor CSV mapping, PDF/OCR extraction and live connectors are outside this build.

Store original bytes privately under opaque organization-scoped S3 keys. Quarantine first, match the exact registered source excerpts and immutable rule versions, and preserve source revision identities and import lineage. Identical content reuses its import; conflicting content for an existing work revision is rejected. Authors register bounded fictional sources and propose explicit rule versions through authenticated operations; a different permitted actor approves them.

Delete rejected bytes and expose fixed diagnostics. Request receipts distinguish an exact retry from a new failed attempt. A new failure or terminal run error retains the prior result but blocks review as stale until valid publication. Completed runs, source revisions, rule versions, documents and audit events are protected from runtime mutation in PostgreSQL.

Private downloads require authorization and expiry checks. S3 blocks public access, enforces TLS, encrypts objects and restricts runtime access to the configured organization prefix. No public source URLs are issued.

## Alternatives considered

- **Treat imported approval flags as authority:** would allow an untrusted file to approve its own contract terms.
- **Overwrite source rows and prior results:** loses the evidence needed to explain a review and detect changed inputs.
- **General document extraction or vendor connectors:** expands data and interpretation boundaries before customer semantics and real-data approval exist.

## Consequences

The supported format is narrow and requires normalized input preparation. Coverage gaps remain unknown monetary values; incomplete evidence is not silently converted into confirmed savings or loss. A synthetic attestation and field validation cannot classify arbitrary sensitive text or authorize real records.

Quarantine originals expire after one day and accepted originals after 30 days. Normalized snapshots, rules and audit history need an approved retention and backup policy before real data. PostgreSQL immutability protects against the application role, not an administrator; S3 has no Object Lock guarantee. Storage and database writes are not a distributed transaction, so interrupted imports need retry and lifecycle handling.

## Implementation and verification

[Import validation and receipts](../../backend/imports.py), [JSON adapter](../../src/adapters/custom.ts), [private storage](../../backend/storage.py), [immutability migration](../../backend/migrations/003_import_immutability.sql), and [S3 controls](../../infra/main.tf). The [publication sequence](../architecture/import-publication.md), [threat model](../THREAT_MODEL.md), and [implementation evidence](../../IMPLEMENTATION_STATUS.md) document replay, rejection, concurrency, private-download and recovery behavior.
