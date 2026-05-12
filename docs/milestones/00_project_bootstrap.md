# Milestone 00: Project Bootstrap

## Goal

Create the minimum FastAPI project foundation.

This milestone must not implement OCR, image upload, Gemini, OpenAI, database calls, or `.env` files.

## Scope

Implement:

- `app/main.py`
- `app/config.py`
- package `__init__.py` files
- empty module directories for schemas, services, providers, utils
- `tests/test_health.py`
- README update using `docs/README_TEMPLATE.md`

## Required API

### GET /health

Response:

```json
{
  "status": "ok"
}
```

## Configuration rule

Use `pydantic-settings` for configuration.
Do not use `.env` files.
Do not configure `env_file`.

The app must start without API keys.

## Dependencies

If missing, add runtime dependencies:

- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `pydantic-settings`
- `python-multipart`

If missing, add dev dependencies:

- `pytest`
- `httpx`

## Forbidden work

Do not implement:

- `POST /ocr/receipts/extract`
- Image validation
- Gemini provider
- OpenAI provider
- OCR service logic
- Database registration
- `.env`
- `.env.example`

## Required tests

- `GET /health` returns 200
- Response body is `{"status": "ok"}`

## Completion commands

```bash
uv run python -m compileall app
uv run pytest
```

## Completion report

Report:

- Changed files
- Added API
- Commands executed
- Test results
- Remaining TODOs
