# ShiftClarity workspace instructions

## GitHub publication authorization · October 13, 2026
The user explicitly approved creating public `manynames3/ShiftClarity` and publishing a product-led README, GitHub About fields, actual synthetic product screenshots, ADRs and C4 documentation. Publish the reviewed application source and reproducible build/test inputs with that documentation. This supersedes earlier no-commit/no-push restrictions for this repository publication. Keep credentials, authenticator setup keys, private configurations, Terraform state, backups, raw runtime artifacts and customer data out of Git. Preserve the original handoff unchanged. Existing synthetic/real-data operating gates continue to apply.

## Synthetic AWS deployment authorization · October 13, 2026
The user explicitly requested container verification and deployment to AWS account 636305658578 with Cognito, private S3 and Neon, using an AWS-generated hostname and private test accounts. They approved Mangum and Lambda/SQS to minimize idle cost and requested a separate deployment role. Existing credentials may establish that dedicated role; all pilot deployment operations must use it. This supersedes earlier AWS provisioning/spend/deployment prohibitions for the isolated synthetic pilot only. Keep costs minimal, use no paid Neon upgrade, send no invitations/messages, and do not touch DealFinder resources. No real customer data or production claims are authorized.

This file is intended to become `AGENTS.md` at the root of a NEW ShiftClarity application workspace. Do not overwrite unrelated existing instructions.

The canonical build handoff lives in `./handoff/`. Before implementation, read and apply `handoff/AGENTS.md`, `handoff/contracts/scope-lock.json`, the numbered requirements/domain/design docs, and `handoff/docs/06_BUILD_PLAN.md`. Resolve paths inside handoff instructions relative to `handoff/` unless explicitly stated otherwise.

Current authorization: stages 0–4 with fictional records, local development, isolated Neon Free branches and the explicitly approved minimal AWS synthetic deployment through the dedicated role. No customer records, paid-plan upgrades, source-system edits, outgoing messages, commits or pushes.

Do not restyle or broaden the product. Match the supplied ShiftClarity SVGs, design tokens and canonical interface references. Calculate results from synthetic inputs; expected results are a test oracle, never an implementation shortcut. Keep coverage, unknown values, effective dates and independent rule approval intact.

At every checkpoint, update IMPLEMENTATION_STATUS.md, map work to acceptance IDs, run the relevant tests, inspect screenshots and record deviations. Do not claim completed application tests or security properties without evidence. Complete the authorized synthetic phase 4 build; report the separate AWS/real-data/measurement gates.

## Subsequent explicit user scope update
The user has additionally authorized research into common complaints, an AWS infrastructure direction with conditional Neon cost evaluation, and an option to enter/import their own records. Implemented as a separate minimized JSON/manual local preview; the canonical fixture-only flow remains intact. Do not reinterpret this as proof of customer discovery, permission to upload ePHI, cloud deployment approval or production security. Follow docs/PILOT_GATES.md and the actual evidence in IMPLEMENTATION_STATUS.md. Preserve all original handoff files unchanged.

## Phase 4 authorization · October 12, 2026
The user explicitly authorized phase 4 backend, identity integration, persistence, secure imports and AWS preparation with realistic synthetic data, and approved FastAPI/Uvicorn, Psycopg, Authlib and Boto3. This supersedes the stages 0–3 stop instruction for local development. Implement and test all possible phase 4 controls; retain the original demo separately. No real customer data, AWS provisioning/spend/deployment, paid-plan upgrades, outgoing messages, commits or pushes are authorized; the conditional isolated Neon Free choice is resolved below. Cognito is the cloud identity service; Neon is an optional PostgreSQL host, not a replacement for its Python driver. Record unexercised cloud and real-data gates honestly.

## Conditional Neon choice resolved
The user's instruction to use Neon if justified supports the isolated synthetic Free-plan project created after verifying the connected organization plan. Project lively-field-50384173 (AWS us-east-1), base branch br-spring-hall-b7cu8pa3, application branch br-holy-block-b75wbmjb. Both endpoints are fixed at 0.25 CU. Only fictional source data is loaded; restricted runtime credentials remain in ignored owner-only .local files. This supersedes the earlier blanket prohibition on Neon provisioning for this specific synthetic project. It does not authorize paid-plan upgrades, AWS provisioning/deployment or customer data. Suspend unused compute; record actual suspension behavior rather than inferring it from pricing pages.
