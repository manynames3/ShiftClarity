# ADR 0002: Run the intermittent pilot on Lambda and SQS

- **Status:** Accepted; supersedes the prepared App Runner deployment and cloud integrated-worker plan
- **Date:** October 13, 2026
- **Scope:** Authorized synthetic AWS deployment

## Context

The pilot is used for occasional demonstrations. The user explicitly requested a near-zero idle-cost direction and approved Lambda, SQS and Mangum. An always-running web/worker process would reserve capacity between sessions and could keep the database awake through background polling.

## Decision

Use API Gateway HTTP API to invoke a FastAPI/Mangum web function. A separate Lambda worker receives FIFO job notifications. Both functions use the same verified, immutable x86 container image containing the React build, Python API and shared Node engine. Neither runs an idle polling thread or provisioned Lambda capacity.

PostgreSQL owns durable job state. Send the SQS notification inside the job transaction **before commit**: a failed send rolls the transaction back; delivery before commit retries. The worker claims the exact job ID, uses fenced leases, and commits the run, head, completion and audit together. Replayed terminal notifications cannot publish another result.

Keep the event-driven integrated worker for loopback local development. It wakes for pending work and does not poll an idle workspace.

## Alternatives considered

- **App Runner or an always-on VM:** easier persistent process lifetime, but idle capacity is unnecessary for the current presentation workload.
- **Database polling worker:** avoids another service, but adds idle database traffic and an always-running process.
- **Additional orchestration or Redis:** introduces state and operating cost without a supported need.

## Consequences

Idle application compute is not reserved; cold starts and database wake-up affect the first operation. The interface shows pending writes and blocks duplicate clicks. SQS and PostgreSQL are not a distributed transaction, so retry semantics remain essential. There is no recurring recovery sweep; exhausted notifications reach a dead-letter queue and visible alarm.

Storage, secrets, logs, alarms and traffic can still incur charges. Endpoint throttling and the account budget are not hard cost caps. Incident ownership, external alarm routing, representative capacity and billed-cost measurement remain real-data operating gates.

## Implementation and verification

[Lambda handlers](../../backend/lambda_handler.py), [job leases and publication](../../backend/jobs.py), [run creation](../../backend/app.py), [Dockerfile](../../Dockerfile), and [Terraform](../../infra/main.tf). See [C4 containers](../architecture/README.md#c4-level-2-containers), the [publication sequence](../architecture/import-publication.md), and [recorded deployment evidence](../../IMPLEMENTATION_STATUS.md).
