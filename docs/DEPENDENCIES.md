# Resolved dependencies

Node 22.23.1, npm 10.9.8, Python 3.14.6. Exact versions are locked in package-lock.json. Production dependencies implement the requested React UI, exact decimal arithmetic and self-hosted Inter. Test dependencies implement TypeScript/Vite, unit/component, browser and accessibility checks.

- `@fontsource-variable/inter`: `5.3.0`
- `decimal.js`: `10.6.0`
- `react`: `19.3.0`
- `react-dom`: `19.3.0`
- `@axe-core/playwright`: `4.13.0`
- `@playwright/test`: `1.64.0`
- `@testing-library/jest-dom`: `7.0.1`
- `@testing-library/react`: `16.3.3`
- `@testing-library/user-event`: `14.6.7`
- `@types/node`: `26.6.5`
- `@types/react`: `19.3.0`
- `@types/react-dom`: `19.3.0`
- `@vitejs/plugin-react`: `6.1.2`
- `jsdom`: `30.1.2`
- `typescript`: `7.0.2`
- `vite`: `8.3.4`
- `vitest`: `5.0.4`

Inter Variable is self-hosted from Fontsource under OFL-1.1. No network font request is needed in the application. [React stable versioning](https://react.dev/community/versioning-policy), [Vite requirements](https://vite.dev/guide/), [Fontsource Inter license](https://fontsource.org/fonts/inter/about).

## Phase 4 dependencies

Explicitly approved libraries: FastAPI 0.143.0, Uvicorn 0.54.0, Psycopg 3.3.6, Authlib 1.8.0 and Boto3 1.43.112. HTTPX 0.28.1 transports Authlib/metadata requests; joserfc 1.7.5 verifies RS256 tokens through Authlib's dependency. Exact production and development transitive versions are in backend/requirements.lock and backend/requirements-dev.lock. Pytest 9.1.1 is development-only. No Neon-specific client or second accounting library is required.

Local identity uses Keycloak 26.8.0, downloaded from its official release with verified SHA256 9e41da899f838a58cd510fc98ed4f7cadc715aed5683e42aca20a0c9a2a3980a. The cloud uses Cognito. Local backend Python is 3.13.9; PostgreSQL is 17.10; the Terraform AWS provider is 6.68.0, locked in infra/.terraform.lock.hcl.

Installed Authlib/Starlette issue HTTPX transport deprecation warnings; tests pass with the pinned transport. No comprehensive dependency security audit is claimed. The subsequent container verification is summarized in [release verification](VERIFICATION.md).

Verified database TLS uses the pinned Certifi public CA bundle, including on this macOS runtime where system-root lookup failed. PostgreSQL URI query values use percent encoding; spaces must not be encoded as plus signs. No certificate-verification bypass is used.


October 13 deployment update: the user approved Mangum 0.22.0 for Lambda/SQS after requesting near-zero idle cost. Production and development lockfiles include it. The Lambda image uses the official Python 3.13 AWS image pinned to sha256:40dcef2531da40c0fae6d11ee28e12313af9723fc1f0f31c1728c22e5112ec3c and AL2023 security packages from release 2023.12.20260928. Node remains 22.23.1 and the accounting engine remains unchanged. The supplied wordmark SVG was rendered into infra/shiftclarity-login.png for Cognito branding; it was not redesigned. ECR's basic OS scan and actual image digest are recorded in artifacts/aws-image-scan.json; this is not an independent application or dependency audit.
