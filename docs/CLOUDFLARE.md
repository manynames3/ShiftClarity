# Cloudflare Pages pilot address

The full synthetic pilot uses **https://shiftclarity.pages.dev/**. Root serves the approved public landing page directly from Pages static assets. `/pilot/` opens the assigned-account workspace; `/demo/` is the memory-only standalone demonstration. AWS Lambda/API Gateway, Cognito, private S3 and Neon remain the backend.

The [advanced-mode Worker](../infra/cloudflare/_worker.js) serves `/` and `/landing/` from its `ASSETS` binding, and forwards the remaining paths to one fixed AWS origin. It preserves secure cookies and browser Origin/CSRF checks. It never follows a redirect with the private edge credential. Preview hosts fail closed. The backend requires the configured gateway host and edge credential before normal user authorization. `/health` exposes availability only.

## Deploy

The dedicated Pages project is `shiftclarity`, production branch `main`, using direct upload. No automatic Git integration is configured. A deployment does not change the database or provision user accounts.

The private `.local/aws.tfvars.json` includes `public_origin` and sensitive `edge_proxy_secret`. The matching value is the Pages secret `ORIGIN_TOKEN`; provide it through stdin, never a command argument. Lambda environment values are encrypted by AWS; the credential also resides in private Terraform state. Keep it out of Git, deployment artifacts intended for sharing, and browser bundles.

```sh
node --test tests/edge.test.mjs
backend/.venv/bin/python -m pytest backend/tests/test_edge.py -q
npm run build:pages
npm run test:landing
wrangler pages deploy dist/cloudflare --project-name shiftclarity --branch main
```

Build and verify the AWS image using the [AWS operations guide](AWS_AND_DATABASE.md). The image-push script preserves existing private Terraform inputs. Inspect the saved plan before applying: the address transition changes the two function images/environments and the Cognito callback/logout URLs. It does not replace S3, queues, identities or Neon data.

## Cost

Pages Functions share the account's Workers Free allowance of 100,000 requests/day; other applications use the same allowance. The Worker handles routing, while landing HTML, styles, scripts, fonts and screenshots come from Pages static storage without invoking AWS. Demo, pilot, authentication and API requests retain their fixed AWS proxy path. There is no additional monthly Cloudflare baseline within that allowance. If the account reaches its free quota, availability can be affected; it is not an unlimited-traffic service.

The current AWS idle estimate is roughly **$0.60–$1/month before credits and shared free allowances**, dominated by one Secrets Manager secret, ECR image storage and one standard alarm. Stored S3 originals/state are under 1 MiB at this checkpoint. Lambda/API execution has no reserved idle capacity. Managed SQS polling may use request allowance even with no jobs. Neon remains on the isolated Free plan. This is a resource-based estimate, not a measured monthly invoice.

Sources: [Pages Functions pricing](https://developers.cloudflare.com/pages/functions/pricing/), [Secrets Manager](https://aws.amazon.com/secrets-manager/pricing/), [ECR](https://aws.amazon.com/ecr/pricing/), [CloudWatch](https://aws.amazon.com/cloudwatch/pricing/), and [SQS polling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html).

## Recorded verification · October 13, 2026

Two proxy tests and two focused backend gateway tests passed. The final image passed the Lambda runtime emulator checks for nonroot/read-only execution, restricted Neon access, UI, anonymous denial and the shared engine. Terraform applied only three in-place updates and its final plan found no drift.

The live browser completed Cognito authenticator sign-in, retained the Pages origin, validated a synthetic import, downloaded its private original, queued a durable SQS run and verified completion after reload. It reproduced 12 checked records and $1,760.00 potential underbilling. Missing CSRF was denied. HTTP checks verified anonymous API denial, direct AWS denial and preview-host denial. The actual signed-in product capture was inspected.

Ten stored ECR images total at most 2.86 GB by summed image sizes; shared layers may reduce billed storage. One $0.40 secret, image storage at $0.10/GB and one $0.10 alarm give an approximately $0.79 monthly baseline before free allowances/credits. Small storage and request charges remain variable. No monthly invoice or credit eligibility was measured.

The original full backend suite did not complete in this session because the local test cluster rejected peer authentication. Gateway tests were isolated from that unrelated cluster and passed; the actual cloud persistence/import/job path and container-to-Neon runtime were exercised. The previous release's broader results remain historical evidence, not a full rerun for this address change.

## Landing page release · October 17, 2026

The user approved the rendered bright editorial concept before implementation. Source lives in `landing/`; `scripts/build-pages.mjs` assembles only that public content and the Worker into ignored `dist/cloudflare/`. The app build and its `/assets/` remain separate, so no Lambda image rebuild or backend change is required. Deploy the assembled directory, not the Worker-only source folder.

Landing responses carry a self-only content policy, framing denial, nosniff, restricted device permissions and explicit revalidation. Static requests need no private origin credential; preview hosts still fail closed. Private paths retain the existing credential, cookie, CSRF, redirect and cache behavior. No signup, analytics service, connector, new account or paid resource is introduced.
