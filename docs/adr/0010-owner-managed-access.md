# ADR 0010: Owner-managed, invite-only agency access

Status: accepted, October 24, 2026. The user chose invite-only access and the existing private reviewer as the synthetic owner.

## Decision

Keep Cognito, mandatory authenticator MFA, OIDC code/PKCE sign-in and existing private sessions. Add owner-only workspace defaults and membership management inside the same application. There is no public signup. Permissions are explicit: upload, review, author, approve and owner. Ownership does not bypass independent approval.

An owner creates a stable username and grants permissions. Cognito `AdminCreateUser` uses `MessageAction=SUPPRESS`: ShiftClarity sends no invitation. The owner shares the sign-in URL and temporary password through their approved private channel. Cognito requires a new password and authenticator enrollment before application access. Temporary credentials expire after three days; the password is returned once and never saved in receipts, audit notes or the database. An existing identity retains its current password; an owner may issue a temporary reset after verifying the person.

Changing access invalidates that member's sessions; revocation also fails the active-membership check on every API call. The last active owner cannot be removed. Resets preserve mandatory MFA and cannot reset the acting owner's own account. The pilot supports 50 memberships; an operator recovery path remains necessary if the sole owner loses access.

Cognito subjects and sign-in usernames are stored as distinct identifiers. Migration 009 retains the verified, immutable username binding; password resets recheck its subject before changing the password. This pool does not accept a subject UUID as an administrative username. Existing bindings are backfilled only after matching Cognito’s verified subject, and sign-in records the verified mapping.

Runtime IAM gains only account creation and temporary password reset on the existing Cognito pool. Membership writes are organization-scoped by RLS, and the identity-to-organization mapping is immutable through granted runtime columns. Verified issuer/subject lookup necessarily precedes organization selection; its SELECT policy allows that authentication lookup. HTTP routes still require exact active membership and owner permission for administration.

Local tests mock only the Cognito service boundary; local Keycloak provisioning remains an operator/test concern. Live first-login/MFA evidence must be recorded separately. Real customer data, customer retention terms and independent billing validation remain gated.

[Cognito administrator-created accounts](https://docs.aws.amazon.com/cognito/latest/developerguide/how-to-create-user-accounts.html) documents temporary passwords, required password changes and suppressed invitations.
