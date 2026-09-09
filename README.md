# Suggestions Box processor

A small FastAPI service that authenticates to Gmail with OAuth 2.0 and processes Gmail push notifications. It requests only the `gmail.readonly` scope.

## Repository Structure

```text
├── suggestions-ingester/       FastAPI Gmail ingestion service
│   ├── app/
│   │   ├── infrastructure/     Google OAuth, Gmail, and configuration adapters
│   │   ├── ports/               FastAPI HTTP routers
│   │   ├── resources/           Local-only OAuth and maintenance secrets
│   │   ├── services/            Provider-neutral contracts and results
│   │   └── main.py              Composition root and startup watch
│   ├── dev/                     Development utilities
│   ├── tests/                   Unit and architecture tests
│   ├── Dockerfile               Cloud Run container image definition
│   ├── requirements.txt         Runtime dependencies
│   └── run_local.sh             Local startup script
├── suggestion-agent/            LangChain suggestion analysis service
│   ├── agent/                   Configuration, prompts, and execution logic
│   ├── main.py                  Local agent runner
│   ├── requirements.txt         Agent runtime dependencies
│   ├── Dockerfile               Cloud Run image definition
│   └── start_local.sh           Local agent launcher
└── schemas/                     Shared protobuf and Pydantic contracts
   ├── suggestion.proto         Source protobuf contract
   ├── suggestion_pb2.py        Generated protobuf classes
   └── pydantic_schemas.py      Shared Pydantic validation models
```

The root `schemas/buf.yaml` file declares `schemas` as the Buf module root. `schemas/suggestion.proto` is shared by both services. Run schema commands from the repository root.

The `suggestion-agent` service receives email content from the ingester, analyzes feature suggestions and qualitative tone with LangChain/OpenAI, and returns the shared `SuggestionAnalysis` protobuf shape.

## Architecture

The backend uses provider-neutral service contracts implemented by infrastructure adapters:

```text
suggestions-ingester/app/
   services/        OAuth, token-store, and Pub/Sub contracts
   infrastructure/ Google OAuth, Gmail, and configuration adapters
   ports/           FastAPI HTTP routes and response mapping
   resources/       Local-only secret files, ignored by Git
   main.py          Composition root and startup Gmail watch registration
```

The service contracts describe capabilities without importing Google or FastAPI. `GoogleOAuthAdapter`, `GoogleGmailAdapter`, and `InMemoryTokenStore` implement those contracts. The application is currently focused on Gmail authentication, startup watch registration, Pub/Sub delivery, and Gmail history lookup.

## Suggestion Agent

Install the agent dependencies and run the agent service from the repository root:

```bash
pip install -r suggestion-agent/requirements.txt
cp suggestion-agent/.env.example suggestion-agent/.env
# Edit suggestion-agent/.env, then run:
./suggestion-agent/start_local.sh
```

Start the agent before the ingester. The agent publishes each resulting `SuggestionAnalysis` protobuf to the configured output topic.

The agent reads `MODEL_PROVIDER`, `MODEL_API_KEY`, `MODEL_NAME`, `TEMPERATURE`, and `OUTPUT_TOPIC`. Gemini is the default provider and uses `gemini-3.6-flash`; OpenAI is also supported by setting `MODEL_PROVIDER=openai` and changing the model name. It exposes `POST /webhooks/pubsub`, which accepts a Pub/Sub envelope containing a serialized `schemas/suggestion.proto` `EmailMessage`, then publishes `SuggestionAnalysis` protobufs to `OUTPUT_TOPIC`. The ingester receives those messages at `POST /webhooks/suggestion-analysis`. The agent imports shared contracts from `schemas/`, so keep that directory at the repository root.

For local development, `start_local.sh` reads `MODEL_API_KEY` from the environment first, then from the ignored `suggestion-agent/resources/model-api-key.txt` file.

The dependency direction is enforced by `tests/test_architecture.py`. Run it with:

```bash
python -m unittest discover -s tests -v
```

That test fails if a developer introduces forbidden framework or adapter imports into protected application boundaries, or if an infrastructure adapter stops implementing its application contract. It is suitable for CI and keeps the rule visible in the repository.

## Gmail Push Notifications

Gmail push notifications use Google Cloud Pub/Sub. They contain an `emailAddress` and `historyId`, not email contents. The backend receives the event at `POST /webhooks/gmail` and uses Gmail History API to identify changed message IDs.

Configure `GOOGLE_PUBSUB_TOPIC=projects/suggestion-box-508020/topics/new-email`, grant Gmail permission to publish to that topic, and create a push subscription targeting `https://YOUR_SERVICE/webhooks/gmail`. Configure `SUGGESTION_AGENT_TOPIC=projects/suggestion-box-508020/topics/analysis-request`; the ingester publishes serialized `EmailMessage` protobufs there after fetching Gmail message content. Create a second push subscription targeting the agent's `POST /webhooks/pubsub`. On every application startup, the service authenticates with `GMAIL_TOKEN_JSON` and registers the Gmail watch automatically before serving requests.

The Gmail watch expires and must be renewed periodically. The startup flow uses the configured single mailbox token.

## Local setup

The local setup expects these files under `suggestions-ingester/app/resources/`:

- `google-client-secret.json`: the OAuth client configuration downloaded from Google Cloud.
- `gmail-lewis-secret.json`: the authorized-user token JSON for the Gmail account the service should use.
- `maintenance-password.txt`: the maintenance password used to protect the OAuth endpoints.

The entire `suggestions-ingester/app/resources/` directory is ignored by Git. Keep both files local and never commit their contents. The token file contains a refresh token and provides background access after OAuth authorization.

Set `MAINTENANCE_PASSWORD` in `.env` to protect the OAuth maintenance endpoints. The optional `MAINTENANCE_USERNAME` defaults to `maintenance`. Both `/auth/start` and `/auth/callback` require HTTP Basic authentication; use the same credentials for the Google redirect callback.

1. In Google Cloud Console, create a project, enable the Gmail API, configure the OAuth consent screen, and create a **Web application** OAuth client.
2. Add `http://localhost:8000/auth/callback` as an authorized redirect URI.
3. Create a virtual environment and install dependencies:

   ```bash
   cd suggestions-ingester
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and set the Google variables. The example enables the OAuth library's HTTP exception for localhost only. Load it in your shell, then run:

   ```bash
   set -a; source .env; set +a
   python -m pip install -e .
   ./run_local.sh
   ```
   ```

   For a direct launch without `.env`, use `OAUTHLIB_INSECURE_TRANSPORT=1`. Never set this in production.

5. Ensure `gmail-lewis-secret.json` contains an authorized-user token before starting the local service. The file must contain the token JSON itself, not the outer callback response. If you need to authorize or reauthorize the account, use `/auth/start` with HTTP Basic credentials, approve access in Google, and provision the resulting token JSON into this file before restarting. Startup fails if the token is missing or the Gmail watch cannot be registered.
6. Set `SUGGESTION_AGENT_URL=http://localhost:8090` in the ingester environment and start it with `./suggestions-ingester/run_local.sh`.
7. Verify the ingester health at `http://localhost:8000/health`.

The OAuth maintenance endpoints are:

- `GET /auth/start`: starts the Google authorization flow.
- `GET /auth/callback`: completes the flow and stores the token for the current process.

Both endpoints require HTTP Basic authentication using `MAINTENANCE_USERNAME` and `MAINTENANCE_PASSWORD`. The normal Gmail and webhook endpoints do not use these maintenance credentials.

From the repository root, start the local application with:

```bash
./suggestions-ingester/run_local.sh
```

Run tests with:

```bash
python -m unittest discover -s tests -p 'test*.py' -v
```

## Deploy on Google Cloud Run

Cloud Run has a generous always-free allowance for small services. Deploy the agent first, then the ingester. The services communicate through two Pub/Sub topics:

- `analysis-request`: the ingester publishes serialized `EmailMessage` protobufs.
- `suggestion-analysis`: the agent publishes serialized `SuggestionAnalysis` protobufs back to the ingester.
- `suggestion-analysis`: the response dispatcher also subscribes to this topic to send the draft reply.

The response dispatcher requires a separate Gmail OAuth token authorized with `https://www.googleapis.com/auth/gmail.send`. The ingester's read-only token cannot send replies.
The dispatcher uses an in-memory TTL cache keyed by source `email_id` to prevent duplicate replies during Pub/Sub redelivery. Configure `RESPONSE_CACHE_TTL_SECONDS` as needed; use Firestore or Memorystore for durable multi-instance idempotency.

Enable the required APIs and authenticate `gcloud` before starting:

```bash
gcloud config set project suggestion-box-508020
gcloud services enable run.googleapis.com pubsub.googleapis.com \
   secretmanager.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

Cloud Run is stateless. Keep OAuth, model, and maintenance credentials in Secret Manager; do not bake them into either image.

```bash
gcloud secrets create google-client-secret \
   --replication-policy=automatic \
   --data-file=suggestions-ingester/app/resources/google-client-secret.json

gcloud secrets create gmail-lewis-secret \
   --replication-policy=automatic \
   --data-file=suggestions-ingester/app/resources/gmail-lewis-secret.json

# Create a strong password locally, then store it in Secret Manager:
openssl rand -base64 32 > /tmp/maintenance-password.txt
gcloud secrets create maintenance-password \
   --replication-policy=automatic \
   --data-file=/tmp/maintenance-password.txt

gcloud secrets create model-api-key \
   --replication-policy=automatic \
   --data-file=agent/resources/model-api-key.txt

gcloud pubsub topics create analysis-request \
   --project=suggestion-box-508020

gcloud pubsub topics create suggestion-analysis \
   --project=suggestion-box-508020

# Run the agent service separately, then create a push subscription to its URL:
gcloud run deploy suggestion-agent \
  --source suggestion-agent \
  --region northamerica-northeast1 \
  --allow-unauthenticated \
  --min 1 \
  --set-env-vars "^@^MODEL_NAME=gemini-3.6-flash@OUTPUT_TOPIC=projects/suggestion-box-508020/topics/suggestion-analysis" \
  --set-secrets MODEL_API_KEY=model-api-key:latest

# Replace YOUR_AGENT_SERVICE_URL with the URL returned by:
gcloud run services describe suggestion-agent \
   --region northamerica-northeast1 \
   --format='value(status.url)'

# Use the deployed agent URL in the push endpoint:
gcloud pubsub subscriptions create analysis-request-push \
   --topic=projects/suggestion-box-508020/topics/analysis-request \
   --push-endpoint=https://suggestion-agent-ruk22oq2sa-nn.a.run.app/webhooks/pubsub \
   --project=suggestion-box-508020

gcloud pubsub subscriptions create suggestion-analysis-push \
   --topic=projects/suggestion-box-508020/topics/suggestion-analysis \
   --push-endpoint=https://suggestion-agent-ruk22oq2sa-nn.a.run.app/webhooks/suggestion-analysis \
   --project=suggestion-box-508020

gcloud secrets create gmail-send-secret \
   --replication-policy=automatic \
   --data-file=suggestion-response-dispatcher/resources/gmail-send-secret.json

gcloud run deploy suggestion-response-dispatcher \
   --source suggestion-response-dispatcher \
   --region northamerica-northeast1 \
   --allow-unauthenticated \
   --set-env-vars "^@^GOOGLE_REDIRECT_URI=https://suggestion-response-dispatcher-318780185428.northamerica-northeast1.run.app/auth/callback@MAINTENANCE_USERNAME=maintenance@GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.send" \
   --set-secrets GOOGLE_CLIENT_SECRET_JSON=google-client-secret:latest,GMAIL_TOKEN_JSON=gmail-send-secret:latest,MAINTENANCE_PASSWORD=maintenance-password:latest




# Open /auth/start with HTTP Basic credentials once. Approve the Gmail send scope,
# copy the token returned by /auth/callback, then store it and redeploy:
gcloud secrets versions add gmail-send-secret \
   --data-file=suggestions-ingester/app/resources/gmail-send-secret.json

gcloud run deploy suggestion-response-dispatcher \
   --source suggestion-response-dispatcher \
   --region northamerica-northeast1 \
   --allow-unauthenticated \
   --set-env-vars "^@^GOOGLE_REDIRECT_URI=https://suggestion-response-dispatcher-318780185428.northamerica-northeast1.run.app/auth/callback@MAINTENANCE_USERNAME=maintenance@GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.send@GMAIL_ACCOUNT_EMAIL=lewis@example.com" \
   --set-secrets GOOGLE_CLIENT_SECRET_JSON=google-client-secret:latest,GMAIL_TOKEN_JSON=gmail-send-secret:latest,MAINTENANCE_PASSWORD=maintenance-password:latest

gcloud pubsub subscriptions create suggestion-response-dispatcher-push \
   --topic=projects/suggestion-box-508020/topics/suggestion-analysis \
   --push-endpoint=https://suggestion-response-dispatcher-318780185428.northamerica-northeast1.run.app/webhooks/pubsub \
   --project=suggestion-box-508020

# Deploy with all three secrets:

gcloud run deploy suggestion-box \
   --source suggestions-ingester \
   --region northamerica-northeast1 \
   --allow-unauthenticated \
   --set-env-vars "^@^GOOGLE_REDIRECT_URI=https://suggestion-box-318780185428.northamerica-northeast1.run.app/auth/callback@GOOGLE_PUBSUB_TOPIC=projects/suggestion-box-508020/topics/new-email@SUGGESTION_AGENT_TOPIC=projects/suggestion-box-508020/topics/analysis-request@IGNORED_GMAIL_LABELS=SPAM,TRASH,SENT,CATEGORY_PROMOTIONS,CATEGORY_SOCIAL,CATEGORY_UPDATES,CATEGORY_FORUMS=" \
   --set-secrets GOOGLE_CLIENT_SECRET_JSON=google-client-secret:latest,GMAIL_TOKEN_JSON=gmail-lewis-secret:latest,MAINTENANCE_PASSWORD=maintenance-password:latest
```

The agent Cloud Run service account must have Secret Manager Secret Accessor access to `model-api-key` and Pub/Sub Publisher access to `suggestion-analysis`. The ingester service account must have Secret Manager Secret Accessor access to its three secrets and Pub/Sub Publisher access to `analysis-request`. The example uses unauthenticated Cloud Run ingress so Pub/Sub can push directly; for production, use an authenticated push subscription with an OIDC service account and grant it Cloud Run Invoker. `--min 1` keeps one agent instance running; Pub/Sub push provides durable delivery and retries failed requests. Do not set `OAUTHLIB_INSECURE_TRANSPORT` on Cloud Run.

The OAuth callback URL must be registered in Google Cloud Console before authorization. The Cloud Run service authenticates and registers its Gmail watch during startup, so the `gmail-lewis-secret` Secret Manager value must be present before deployment. Keep the Cloud Run service authenticated instead of public if this API is private.