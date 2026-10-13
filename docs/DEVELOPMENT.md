# Development and verification

The standalone demo and persistent pilot share the interface and calculation engine. Their state and identity boundaries differ. Use fictional, minimized records in both.

## Standalone demo

Node 22.23.1 was used for this release. Install the locked packages and start the loopback server:

```sh
npm ci
npm run dev -- --port 5178
```

Open http://127.0.0.1:5178/. Reset restores the canonical run, decisions, role, and rule proposal. Refresh also restores the fixture and discards custom previews. The standalone role selector is explicitly a simulation.

```sh
npm run test:fixtures
npm test
npm run build
npm run test:e2e
```

The browser suite uses installed Google Chrome with isolated test profiles and starts or reuses port 5178. If Chrome is unavailable, configure a supported installed browser or explicitly install the project test browser. `npm run screenshots` expects the demo server to be running and writes local captures under `artifacts/`.

`npm run preview -- --port 4178` serves the built `dist/` directory.

## Persistent local pilot

Prerequisites: Node, uv, Python 3.13, PostgreSQL 17 tools on PATH, and a Java runtime supported by Keycloak 26.8.0. This release used Python 3.13.9, PostgreSQL 17.10, and Java 26 locally.

```sh
npm ci
uv venv --python 3.13 backend/.venv
uv pip sync --python backend/.venv/bin/python backend/requirements-dev.lock
npm run pilot
```

The launcher verifies the pinned Keycloak archive, creates a dedicated PostgreSQL cluster under `.local/postgres` on loopback port 55478, builds the engine/UI, and starts missing local services. Existing system PostgreSQL data is untouched. The app opens at http://127.0.0.1:5180/pilot/; local identity runs on port 5181. Reruns preserve saved pilot data and accounts.

If a prepared `.local/neon-app-config.json` exists, the launcher uses that isolated Neon environment. Set `SHIFTCLARITY_CONFIG` to choose another prepared configuration. Database/bootstrap scripts are operator tools; inspect their target guards before using a different environment.

Local sign-in instructions and generated credentials live only in ignored, owner-only `.local/SIGN_IN.md` and `.local/accounts.json`. A fresh account enrolls a personal authenticator. First OTP enrollment may require a second sign-in before verified OTP execution is accepted. Test-enrolled accounts and their test authenticator keys must remain private.

| Account | Workspace permission |
|---|---|
| reviewer | Import and review findings |
| author | Register fictional source text and propose terms |
| approver | Independently approve or reject a rule proposal |
| observer | Read-only access |
| outsider | Negative membership test; no workspace access |

Pilot mode has no role switch or reset that grants permission. Reload retains server decisions, versions, sources, and runs. Sign-out revokes the app session and completes the provider sign-out flow.

Use **Inputs & rules → Import synthetic snapshot** and its downloadable JSON template. The pilot accepts normalized fictional JSON up to 1 MiB and 2,000 rows per collection. Authors must register source text and propose a rule; a separate permitted account must approve it before an import can use it. Imported approval metadata alone grants no authority.

## Backend checks

Prepare the local environment first, then:

```sh
npm run build:engine
npm run test:backend
terraform -chdir=infra init -backend=false
terraform -chdir=infra validate
```

Backend tests use dedicated `shiftclarity_test` and `shiftclarity_restore_check` databases. They include worker replay and database/private-source recovery. They never truncate the saved pilot database. Tests depend on the local configuration prepared by the setup script; they are not a cloud deployment check.

## Persistent-pilot browser checks

These checks write synthetic records and approval state to a dedicated browser-test database. Prepare it:

```sh
backend/.venv/bin/python scripts/setup-browser-db.py
```

Stop the normal local API instance using port 5180. In one terminal, start the isolated test API:

```sh
SHIFTCLARITY_CONFIG=.local/browser-config.json backend/.venv/bin/python -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 5180 --no-access-log
```

In a second terminal:

```sh
npm run test:pilot
```

Stop the test API afterward and restart the normal pilot. Browser tests require the real local identity provider, synthetic accounts, and their private test authenticator setup. Screenshots and traces stay in ignored output directories.

Live AWS browser checks also change synthetic state. They require operator-provided private accounts and a reviewed starting state. Do not point them at customer environments or run them as a read-only smoke test.

## Containers and AWS

The default Docker target runs the local server. The explicit `lambda` target packages the same UI, Python API, and bounded Node engine for web/worker Lambda functions. Cloud verification requires a prepared private configuration and the AWS runtime emulator; see [AWS operations](AWS_AND_DATABASE.md).

Keep `.local/`, environment files, credentials, authenticator keys, source backups, Terraform state, and local test artifacts out of Git and Docker build contexts. No cloud credentials are required for the standalone demo.

See [verification evidence](VERIFICATION.md), [phase 4 boundaries](PHASE_4.md), and [pilot gates](PILOT_GATES.md) for what these checks establish.
