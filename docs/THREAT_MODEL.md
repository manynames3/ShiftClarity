# Phase 4 threat model

Scope: one synthetic workspace, distinct identity accounts, AWS web/worker functions and local development, private PostgreSQL/storage and the supplied supported billing components. No ePHI, real customer data, connectors or source-system edits.

| Threat | Implemented control | Evidence / remaining limit |
|---|---|---|
| Forged identity, role or organization | Verified OIDC identity; operator-created memberships; extra request fields rejected; every object/action checked | API negative cases and real-provider sign-in; live Cognito sign-in/enrollment and signed-sub matching are tested |
| Guessed cross-workspace IDs | Server membership boundary plus forced PostgreSQL RLS and private storage keys | Direct runtime SQL and outsider account tests; no multi-customer product claim |
| Stolen or replayed login/session | Code+PKCE, state/nonce, trusted RS256 keys, fresh authentication, short hashed sessions, HttpOnly/SameSite, cloud __Host-/Secure | Claim, expiry, replay, revocation tests; operator/host compromise requires incident response |
| CSRF | Exact Origin plus session-bound CSRF header on writes | Forged Origin/token cases |
| Self-approved terms | Separate actor and approver permission; immutable version/source records | API denial and distinct browser accounts |
| Uploaded data interpreted as authority/code | Exact JSON allowlist, controls, registered approvals, quarantine, bounded isolated parser, no executable document formats | Invalid/unknown fields, altered rules, conflicting revisions, type/size/timeout cases |
| Sensitive content in free text/logs | Synthetic-only attestation, minimized fields, fixed parser diagnostics, no record/request-body logging, escaped text and private downloads | Canary rejection tests; no DLP classifier or authorization for real notes |
| Duplicate amounts or conflicting reviews | Content/revision identity, receipts, head lock, run/fingerprint/version checks | Duplicate, concurrent and changed-evidence tests |
| Half-published or repeated jobs | Transactional publication, lease fencing, bounded retries | Killed worker, job-targeted SQS retries/replay, old lease fencing, terminal failures and new-failure-versus-exact-retry import receipts |
| Unauthorized file/export access | Membership/role checks, expiry checks, no public URLs, attachment/nosniff/no-store, formula-safe CSV | Download denials and malicious-cell export test; private S3 encryption/TLS/public-access controls and anonymous source denial are verified |
| Irrecoverable changes / expired data resurrected | Isolated restore rehearsal; owner-only retention actions; revocation and deletion ledger required before restore | Local and Neon-to-local database/source matches plus purge tests; approved backup expiry/hold/contact policy remains a real-data gate |
| Credit exhaustion or runaway workload | No provisioned compute, bounded upload/parser limits, cached public build assets, endpoint throttling, budget and dead-letter alarm | Deployed settings and preflight account/credit reading; no hard spending cap, final bill or credit-expiry verification |

The runtime role cannot edit/delete audit, source, rule or completed-run records. The database owner can perform approved retention operations; this is not cryptographic tamper evidence against a compromised administrator. The local development identity server is loopback-only and must never be exposed as the production provider.
