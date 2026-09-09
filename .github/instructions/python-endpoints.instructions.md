---
applyTo: "python/**/*.py"
---

# Python Endpoint Instructions

When adding or changing an endpoint:

1. Read the existing route factory in `python/app/ports/http.py`, the relevant contract in `python/app/services/`, and the concrete adapter in `python/app/infrastructure/` before editing.
2. Keep the route handler thin. It should validate input, invoke a provider-neutral contract, map domain/application data to a response, and translate expected exceptions.
3. Put new capabilities in a provider-neutral `Protocol` under `python/app/services/` when the capability is external or likely to have another implementation. Implement that protocol in `python/app/infrastructure/` and wire it in `python/app/main.py`.
4. Do not import Google, FastAPI, Pub/Sub, database, or other infrastructure libraries into domain models or provider-neutral contracts.
5. Use typed dataclasses or Pydantic models for non-trivial request and response payloads. Do not expose SDK response objects directly.
6. Treat tokens and credentials as secrets: accept them only where required, never return them from GET endpoints, and never log them.
7. For Gmail push endpoints, expect a Pub/Sub envelope, decode and validate the notification, use `historyId` to fetch changes through an adapter, and make duplicate deliveries harmless.
8. For user-specific configuration, use authenticated identity and a keyed persistence port. An arbitrary path `user_id` is acceptable only for local development.
9. Add focused tests under `python/tests/` for valid input, invalid input, expected failures, and boundary behavior. Update the architecture test for new ports/adapters.
10. Validate from `python/` with:

```bash
python -m unittest discover -s tests -p 'test*.py' -v
python -m compileall -q app tests
```
