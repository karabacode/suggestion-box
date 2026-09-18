# Suggestion Box Infrastructure

This Terraform stack provisions the full Google Cloud runtime for the Suggestion Box application in project `suggestion-box-508020`.

```text
Gmail -> new-email -> suggestion-ingester -> analysis-request -> suggestion-agent
                                     -> suggestion-core -> Cloudflare D1
                                     -> suggestion-response-dispatcher (on demand)
```

## What this stack creates

The deployment provisions the application infrastructure, not just the wiring for pre-existing resources.

It creates or manages:

- a runtime service account
- Secret Manager secrets and secret versions
- the Pub/Sub topics and push subscriptions
- Cloud Run services for ingester, agent, dispatcher, and core
- Cloud Run IAM bindings and Secret Manager access
- the Artifact Registry repository and run source storage bucket

## File layout

The Terraform config is split by concern so it stays readable:

- `locals.tf` — project, region, and topic locals
- `secrets.tf` — runtime service account and Secret Manager resources
- `platform.tf` — required APIs, Artifact Registry, and storage bucket
- `pubsub.tf` — Pub/Sub topics and subscriptions
- `cloudrun.tf` — Cloud Run service definitions and runtime env vars
- `iam.tf` — IAM bindings and access grants
- `variables.tf` — input variables for project settings and secrets
- `versions.tf` — Terraform and provider configuration
- `terraform.tfvars.example` — sample values for local deployment configuration

## Prerequisites

- Terraform >= 1.6
- Google Cloud CLI access to the target project
- permissions to create Cloud Run, Pub/Sub, Secret Manager, IAM, and Artifact Registry resources
- a valid Cloudflare API token with D1 access
- a Cloudflare account ID where Terraform can create the D1 database
- a valid Gmail OAuth client and callback URLs
- Docker images you want Cloud Run to deploy, or a build/push workflow before `terraform apply`

## Local bootstrap

Create the environment-specific config file from the example:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Then fill in the real values in `terraform.tfvars`:

- project ID and region
- image URLs for the four Cloud Run services
- the secret names and secret payloads for Gmail/OAuth/maintenance/model/Cloudflare
- the Gmail account email
- the Cloudflare account ID, D1 database name, and API token
- OAuth callback URLs

Important: keep `terraform.tfvars` out of version control. It contains sensitive values.

## Apply the stack

```bash
terraform init
terraform fmt -recursive
terraform plan
terraform apply
```

## Secret handling

This repo intentionally uses Terraform to create the D1 database, secret resources, and secret versions from values supplied through a local `terraform.tfvars` file.

The secret content is not stored in Git. Do not commit:

- `terraform.tfvars`
- raw OAuth client JSON
- Gmail token JSON
- API keys
- Cloudflare tokens

## Application prerequisites

Terraform wires service URLs into the containers, but the application code still must implement the expected calls:

- `suggestion-ingester` publishes or posts new inbound suggestions to `SUGGESTION_CORE_URL`
- `suggestion-core` calls `SUGGESTION_AGENT_URL` for analysis
- `suggestion-core` calls `SUGGESTION_RESPONSE_DISPATCHER_URL` only when a response is requested
- `suggestion-core` exposes `/webhooks/suggestion-analysis` if the result subscription is retained

The D1 adapter must read `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_D1_DATABASE_ID`, and `CLOUDFLARE_API_TOKEN` from env/configuration.

## Notes

- The deployment is designed to create the application platform from scratch in GCP.
- It does not manage unrelated exported project-level resources from the Config Connector snapshot unless they are explicitly added here.
- OAuth callback URLs must be registered in the Google OAuth client before Gmail authorization completes successfully.
