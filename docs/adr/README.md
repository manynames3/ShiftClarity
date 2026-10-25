# Architecture decision records

These records explain the accepted architecture of the synthetic ShiftClarity pilot as of October 24, 2026. They describe implemented choices and their consequences, rather than a list of future capabilities.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-shared-deterministic-engine.md) | One deterministic TypeScript engine for demo and server calculations | Accepted |
| [0002](0002-event-driven-aws-pilot.md) | Lambda and FIFO notifications for an intermittent AWS pilot | Accepted |
| [0003](0003-cognito-and-server-authorization.md) | Cognito identity with server sessions and independent approval | Accepted |
| [0004](0004-neon-postgres-and-rls.md) | Neon PostgreSQL with restricted runtime access and forced RLS | Accepted for synthetic use |
| [0005](0005-private-versioned-evidence.md) | Private bounded imports and immutable evidence history | Accepted |
| [0006](0006-cloudflare-pages-origin.md) | Cloudflare Pages as the full signed-in pilot origin | Accepted |
| [0007](0007-confirmed-spreadsheet-adapters.md) | Confirmed spreadsheet adapters and reusable mappings | Accepted; deployed synthetic MVP |
| [0008](0008-current-review-evidence-reports.md) | Current-review Excel/PDF evidence reports | Accepted; historical-access restriction superseded by ADR 0009 |
| [0009](0009-periods-and-follow-up.md) | Period-scoped review workspaces, historical reports and verified follow-up | Accepted; deployed synthetic release |
| [0011](0011-browser-local-agency-evaluation.md) | Local prospect CSV evaluation alongside the synthetic persistent pilot | Accepted; release evidence in verification |
| [0010](0010-owner-managed-access.md) | Owner-managed, invite-only agency access with Cognito MFA | Accepted; deployed synthetic release |

Start with the [C4 architecture views](../architecture/README.md) to see how these decisions fit together. The [import publication sequence](../architecture/import-publication.md) explains transaction and retry behavior. The earlier [decision log](../../DECISIONS.md) remains available for chronology; these ADRs describe the current decisions after the authorized AWS scope change.

Changes to an accepted decision should record the new context, tradeoffs, and any superseded record. No ADR removes the [real-data and evaluation gates](../PILOT_GATES.md), changes the original handoff, or establishes production readiness.
