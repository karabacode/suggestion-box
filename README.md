# Suggestion Box Monorepo

This repository contains the Python backend and infrastructure for the suggestion box system.

## Layout

- `suggestion-box-processor/`: Python services, shared schemas, and backend tests.
- `infra/terraform/`: importable Google Cloud and Cloudflare infrastructure.
- `infra/gcp-terraform-export/`: read-only inventory exported from the existing GCP project.
- `ui/`: reserved for the frontend application.

The runtime architecture is:

```text
Gmail -> suggestion-ingester -> suggestion-core -> Cloudflare D1
                            -> suggestion-agent
                            -> suggestion-response-dispatcher on demand
```

Run backend commands from `suggestion-box-processor/`. Run Terraform commands from `infra/terraform/`.