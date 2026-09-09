# Bill Poller Repository Rules

## Repository Shape

- `suggestions-ingester/` is the FastAPI backend component.
- `suggestions-ingester/app/services/` contains provider-neutral application contracts.
- `suggestions-ingester/app/infrastructure/` contains Google OAuth, Gmail, Pub/Sub, and configuration adapters.
- `suggestions-ingester/app/ports/` contains the FastAPI HTTP routers.
- `suggestions-ingester/app/main.py` is the composition root and registers the startup Gmail watch.

## Endpoint Rules

- Before adding an endpoint, identify its inbound request/response shape and the application port or domain object it uses.
- Keep provider-specific concepts out of `suggestions-ingester/app/services/`. Use provider-neutral names in application contracts.
- Implement external behavior in `suggestions-ingester/app/infrastructure/`, then wire it in `suggestions-ingester/app/main.py`.
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
cd suggestions-ingester
python -m unittest discover -s tests -p 'test*.py' -v
python -m compileall -q app tests
```

- Add or update focused tests for every endpoint behavior and validation rule.
- Update architecture tests when introducing a new port or adapter.
- Keep `suggestions-ingester/` installable with `python -m pip install -e .`.
- Use `./suggestions-ingester/run_local.sh` for local startup. Do not run `python app/main.py` directly.
- Local OAuth may use `OAUTHLIB_INSECURE_TRANSPORT=1` only with localhost. Never use it in production.
