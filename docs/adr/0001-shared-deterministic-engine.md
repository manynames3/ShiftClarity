# ADR 0001: Share one deterministic calculation engine

- **Status:** Accepted
- **Date:** October 13, 2026
- **Scope:** Standalone demo and synthetic persistent pilot

## Context

The demonstration and server must reach the same conclusions from the same supported inputs. Rates, effective dates, approved minutes and invoice amounts determine financial findings; unsupported or incomplete evidence must remain distinct from a calculated discrepancy. A second accounting implementation would create a second interpretation to reconcile and test.

## Decision

Keep the pure TypeScript domain engine authoritative. Use `decimal.js` for exact-decimal money and rate arithmetic. The React demo calls the domain directly. The server bundles the same domain through a Node adapter; Python coordinates identity, storage and transactions.

The engine receives explicit inputs and action context. UI state, networking, persistence and the clock stay outside the domain. A server invocation runs in a subprocess with a 96 MiB JavaScript heap limit, a 12-second timeout and at most two concurrent parser processes. The adapter returns structured results or allowlisted diagnostics rather than arbitrary exception text.

## Alternatives considered

- **Rewrite calculations in Python:** fits the API language, but duplicates financial and review behavior.
- **Calculate only in the browser:** simplifies a demo, but cannot establish authoritative persistent decisions or controlled publication.
- **Deploy a separate calculation service:** adds a network boundary and operating burden without a current requirement.

## Consequences

The demo and pilot share accounting behavior and regression tests. Python and Node must both be present in the image, and subprocess overhead is accepted for bounded synthetic workloads. The limits protect execution; they do not establish production throughput or capacity. More billing components or larger inputs require explicit scope and validation rather than a second engine.

## Implementation and verification

[Domain engine](../../src/domain/engine.ts), [state transitions](../../src/domain/demo.ts), [Node adapter](../../src/adapters/server-cli.ts), [bundle build](../../scripts/build-engine.mjs), and [Python adapter](../../backend/engine.py). Domain, backend and container evidence is recorded in [implementation status](../../IMPLEMENTATION_STATUS.md).
