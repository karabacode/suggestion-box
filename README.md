# Suggestions Box processor

A small FastAPI service that authenticates to Gmail with OAuth 2.0 and processes Gmail push notifications. It requests only the `gmail.readonly` scope.

## Repository Structure

```text
python/
├── app/
│   ├── infrastructure/
│   │   ├── auth/             Google OAuth and token-store adapters
│   │   ├── configuration/    Environment-backed application settings
│   │   └── gmail/            Gmail API and Pub/Sub adapter
│   ├── ports/                 FastAPI HTTP routers
│   │   ├── auth_http.py       Protected OAuth maintenance routes
│   │   └── http.py            Health and Gmail webhook routes
│   ├── resources/             Local-only OAuth and maintenance secrets
│   ├── services/              Provider-neutral contracts and results
│   └── main.py                Application composition root and startup watch
├── dev/                       Development utilities, including proto compilation
├── schemas/                   Buf-managed Protocol Buffer schemas
├── tests/                     Unit and architecture tests
├── Dockerfile                 Cloud Run container image definition
├── requirements.txt           Runtime dependencies
├── setup.py                   Editable-install package configuration
└── run_local.sh               Local startup script
```

The `python/schemas/buf.yaml` file declares `python/schemas` as the Buf module root. Therefore `python/schemas/email/notifications/v1/new_email.proto` correctly maps to the package `email.notifications.v1`. Run Buf commands from `python/schemas`.

## Architecture

The backend uses provider-neutral service contracts implemented by infrastructure adapters:

```text
python/app/
   services/        OAuth, token-store, and Pub/Sub contracts
   infrastructure/ Google OAuth, Gmail, and configuration adapters
   ports/           FastAPI HTTP routes and response mapping
   resources/       Local-only secret files, ignored by Git
   main.py          Composition root and startup Gmail watch registration
```

The service contracts describe capabilities without importing Google or FastAPI. `GoogleOAuthAdapter`, `GoogleGmailAdapter`, and `InMemoryTokenStore` implement those contracts. The application is currently focused on Gmail authentication, startup watch registration, Pub/Sub delivery, and Gmail history lookup.

The dependency direction is enforced by `tests/test_architecture.py`. Run it with:

```bash
python -m unittest discover -s tests -v
```

That test fails if a developer introduces forbidden framework or adapter imports into protected application boundaries, or if an infrastructure adapter stops implementing its application contract. It is suitable for CI and keeps the rule visible in the repository.

## Gmail Push Notifications

Gmail push notifications use Google Cloud Pub/Sub. They contain an `emailAddress` and `historyId`, not email contents. The backend receives the event at `POST /webhooks/gmail` and uses Gmail History API to identify changed message IDs.

Configure `GOOGLE_PUBSUB_TOPIC=projects/suggestion-box-508020/topics/new-email`, grant Gmail permission to publish to that topic, and create a push subscription targeting `https://YOUR_SERVICE/webhooks/gmail`. On every application startup, the service authenticates with `GMAIL_TOKEN_JSON` and registers the Gmail watch automatically before serving requests.

The Gmail watch expires and must be renewed periodically. The startup flow uses the configured single mailbox token.

## Local setup

The local setup expects these files under `python/app/resources/`:

- `google-client-secret.json`: the OAuth client configuration downloaded from Google Cloud.
- `gmail-lewis-secret.json`: the authorized-user token JSON for the Gmail account the service should use.
- `maintenance-password.txt`: the maintenance password used to protect the OAuth endpoints.

The entire `python/app/resources/` directory is ignored by Git. Keep both files local and never commit their contents. The token file contains a refresh token and provides background access after OAuth authorization.

Set `MAINTENANCE_PASSWORD` in `.env` to protect the OAuth maintenance endpoints. The optional `MAINTENANCE_USERNAME` defaults to `maintenance`. Both `/auth/start` and `/auth/callback` require HTTP Basic authentication; use the same credentials for the Google redirect callback.

1. In Google Cloud Console, create a project, enable the Gmail API, configure the OAuth consent screen, and create a **Web application** OAuth client.
2. Add `http://localhost:8000/auth/callback` as an authorized redirect URI.
3. Create a virtual environment and install dependencies:

   ```bash
   cd python
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
6. Verify the service health at `http://localhost:8000/health`.

The OAuth maintenance endpoints are:

- `GET /auth/start`: starts the Google authorization flow.
- `GET /auth/callback`: completes the flow and stores the token for the current process.

Both endpoints require HTTP Basic authentication using `MAINTENANCE_USERNAME` and `MAINTENANCE_PASSWORD`. The normal Gmail and webhook endpoints do not use these maintenance credentials.

From the repository root, start the local application with:

```bash
./python/run_local.sh
```

Run tests with:

```bash
python -m unittest discover -s tests -p 'test*.py' -v
```

## Deploy on Google Cloud Run

Cloud Run has a generous always-free allowance for small services. It is stateless, so provide both JSON values as Secret Manager secrets or environment variables; do not rely on a token file inside the container.

```bash
gcloud secrets create google-client-secret \
   --replication-policy=automatic \
   --data-file=python/app/resources/google-client-secret.json

gcloud secrets create gmail-lewis-secret \
   --replication-policy=automatic \
   --data-file=python/app/resources/gmail-lewis-secret.json

# Create a strong password locally, then store it in Secret Manager:
openssl rand -base64 32 > /tmp/maintenance-password.txt
gcloud secrets create maintenance-password \
   --replication-policy=automatic \
   --data-file=/tmp/maintenance-password.txt

# Deploy with all three secrets:

gcloud run deploy suggestion-box \
   --source python \
   --region northamerica-northeast1 \
   --set-env-vars GOOGLE_REDIRECT_URI=https://suggestion-box-318780185428.northamerica-northeast1.run.app/auth/callback,GOOGLE_PUBSUB_TOPIC=projects/suggestion-box-508020/topics/new-email \
   --set-secrets GOOGLE_CLIENT_SECRET_JSON=google-client-secret:latest,GMAIL_TOKEN_JSON=gmail-lewis-secret:latest,MAINTENANCE_PASSWORD=maintenance-password:latest
```

The Cloud Run service account must have the Secret Manager Secret Accessor role for all three secrets. `GOOGLE_CLIENT_SECRET_JSON` identifies the OAuth application, `GMAIL_TOKEN_JSON` authorizes the specific Gmail account, and `MAINTENANCE_PASSWORD` protects the OAuth maintenance endpoints. Do not set `OAUTHLIB_INSECURE_TRANSPORT` on Cloud Run.

The OAuth callback URL must be registered in Google Cloud Console before authorization. The Cloud Run service authenticates and registers its Gmail watch during startup, so the `gmail-lewis-secret` Secret Manager value must be present before deployment. Keep the Cloud Run service authenticated instead of public if this API is private.