# ADR 0003: Separate identity, workspace permission and approval

- **Status:** Accepted
- **Date:** October 13, 2026
- **Scope:** Cognito cloud identity; loopback development identity

## Context

Persistent reviews need an authenticated actor and an auditable permission boundary. A browser role selector cannot grant authority. Contract rules also need separation between the person who proposes a change and the person who approves it. The user selected Cognito for the AWS pilot.

## Decision

Use Cognito Lite with private administrator-created accounts and mandatory software-token MFA. Authlib implements the server's OIDC authorization-code client; it is a library used to integrate Cognito. Code/PKCE, browser-bound single-use state, nonce, RS256 issuer/audience checks and fresh authentication protect the sign-in flow.

Cognito classic sign-in clears provider SSO before the fresh authorization flow. The server checks required pool MFA, the verified identity's matching provider subject, and enabled verified authenticator enrollment before creating a workspace session.

Issue a random, hashed server-side session with 15-minute expiry and a Secure, HttpOnly, SameSite `__Host-` cookie in the cloud. Every request rechecks active database membership and required roles. Writes require exact Origin plus a session-bound CSRF token. Sign-out revokes the application session and clears provider SSO.

Rule approval is a server operation. The approver must have permission and differ from the recorded author. Uploaded approval fields do not establish authority. Local development uses a loopback-only Keycloak provider with required OTP and distinct accounts.

## Alternatives considered

- **Browser-managed roles or imported approvals:** convenient for a demo, but would allow users or input files to grant themselves permission.
- **Application password/MFA implementation:** duplicates identity-provider responsibilities.
- **Another hosted identity provider:** unnecessary after the explicit Cognito choice.

## Consequences

Identity and permission can be revoked independently. An authenticated account with no active membership cannot enter the workspace. Sessions require fresh sign-in after expiry, and classic Cognito needs provider-specific enrollment and logout handling. A compromised operator or host remains an incident-response problem; these controls do not imply compliance certification.

## Implementation and verification

[Authentication and sessions](../../backend/auth.py), [API permissions and approval](../../backend/app.py), [identity schema](../../backend/migrations/001_initial.sql), and [Cognito configuration](../../infra/main.tf). Provider sign-in, missing enrollment, outsider membership and self-approval evidence is recorded in [implementation status](../../IMPLEMENTATION_STATUS.md) and the [threat model](../THREAT_MODEL.md).
