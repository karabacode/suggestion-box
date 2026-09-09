# Bill Poller Repository Rules

## Repository Shape

- `python/` is the Python backend component.
- `python/app/domain/` contains provider-neutral business models and must not import FastAPI, Google SDKs, or infrastructure.
- `python/app/services/` contains provider-neutral application ports/contracts such as `EmailReader`, `OAuthClient`, `TokenStore`, `InformationExtractor`, and `CrawlerConfigStore`.
- `python/app/infrastructure/` contains concrete adapters such as Google Gmail, Google OAuth, Pub/Sub, storage, and AI implementations.
- `python/app/ports/http.py` contains the FastAPI presentation adapter and HTTP response mapping.
- `python/app/main.py` is the composition root and wires ports to infrastructure implementations.
- `chrome-extension/` contains the Manifest V3 client. It communicates with the backend over HTTP and must not contain Gmail client secrets.

## Endpoint Rules

- Before adding an endpoint, identify its inbound request/response shape and the application port or domain object it uses.
- Keep provider-specific concepts out of `python/app/domain/` and `python/app/services/`. Use names such as `EmailReader`, not `GmailReader`, in application contracts.
- Implement external behavior in `python/app/infrastructure/`, then wire it in `python/app/main.py`.
- Keep HTTP handlers thin: validate input, call a port, map the result, and translate expected failures to HTTP status codes.
- Use typed request and response models when a payload has more than one field; do not expose raw Google SDK objects.
- Do not return Gmail access tokens or refresh tokens from normal read/configuration responses. Never log secrets.
- New webhook endpoints must validate their envelope, be idempotent, and acknowledge duplicate/replayed deliveries safely.
- Gmail Pub/Sub notifications contain `emailAddress` and `historyId`, not email contents. Use Gmail History API through an infrastructure adapter.
- Do not add polling when a Gmail push/watch flow is appropriate. Watches expire and need renewal handling.
- Per-user data must be keyed by an authenticated user identity. Do not trust an arbitrary user ID from a public URL in production.

## Validation

From the repository root:

```bash
cd python
python -m unittest discover -s tests -p 'test*.py' -v
python -m compileall -q app tests
```

- Add or update focused tests for every endpoint behavior and validation rule.
- Update architecture tests when introducing a new port or adapter.
- Keep `python/` installable with `python -m pip install -e .`.
- Use `./python/run_local.sh` for local startup. Do not run `python app/main.py` directly.
- Local OAuth may use `OAUTHLIB_INSECURE_TRANSPORT=1` only with localhost. Never use it in production.
