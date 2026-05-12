# AGENTS.md

## Project role

This repository implements a Receipt OCR API.

The API receives a receipt image, extracts candidate receipt data, normalizes it into a strict JSON response, and returns that response for frontend confirmation.

This repository must not register data into any database.
This repository must not call the accounting/database API.
This repository must not manage inventory or recipe recommendation.

## Required reading before any task

Before changing code, read these documents:

1. `docs/OCR_PROJECT_SPEC.md`
2. `docs/API_SPEC.md`
3. `docs/STRUCTURED_OUTPUT_SCHEMA.md`
4. `docs/PROVIDER_DESIGN.md`
5. `docs/ERROR_HANDLING.md`
6. `docs/TESTING_STRATEGY.md`
7. The milestone file explicitly named in the task prompt

Do not implement later milestones unless the prompt explicitly asks for them.

## Secret handling

Real API keys and other secrets must never be read, printed, logged, copied, modified, requested, or committed.

Do not create, read, open, or modify these files:

- `.env`
- `.env.local`
- `.env.*`
- Any file that appears to contain real secrets

This project intentionally does not use `.env` files.
Configuration must be read from OS environment variables through `pydantic-settings`.

Do not run commands that dump environment variables, including:

- `env`
- `printenv`
- `set`
- `export`
- `echo $OPENAI_API_KEY`
- `echo $GEMINI_API_KEY`
- `echo $GOOGLE_API_KEY`

The following environment variables must never be printed or logged:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `GOOGLE_API_KEY`
- Any variable ending with `_API_KEY`, `_TOKEN`, `_SECRET`, or `_PASSWORD`

If a live API key is required to verify behavior, stop and provide manual verification steps for the human developer. Do not attempt live provider calls during Codex tasks.

## External API policy

Unit tests must not call real Gemini or OpenAI APIs.

Gemini and OpenAI integrations must be written behind provider interfaces so they can be mocked in tests.

The application must start without `OPENAI_API_KEY` and `GEMINI_API_KEY`.
Only the real provider execution path may require these keys.

When an API key is missing during a real provider call, raise a clear configuration error. Do not expose the missing key value or environment contents.

## Implementation boundaries

Do not implement:

- Database registration
- Database API calls
- Inventory reflection
- Recipe suggestion
- User authentication
- User management
- Receipt image storage
- Background jobs
- Payment or billing features

The OCR API returns temporary candidate data only.
The frontend or another service is responsible for user confirmation and final database registration.

## Coding rules

Use Python 3.12 or later if the project allows it.
Use FastAPI for API endpoints.
Use Pydantic and `pydantic-settings` for schemas and configuration.
Use typed functions where practical.
Keep provider calls separate from route handlers.
Keep business logic in services.
Keep request/response models in schemas.

Do not put large logic directly in `app/main.py`.

## Error handling rules

Return stable HTTP errors according to `docs/ERROR_HANDLING.md`.
Do not return raw exception messages from external providers to clients.
Do not log image contents, API keys, or provider raw responses if they may contain private receipt data.

## Testing rules

Before finishing a task, run:

```bash
uv run python -m compileall app
uv run pytest
```

If tests fail, fix the cause unless the prompt explicitly says not to.

Tests must mock external provider calls.
Tests must not require real API keys.
Tests must not require `.env` files.

## Completion report

At the end of each task, report:

- Changed files
- Added or changed APIs
- Commands executed
- Test results
- Remaining TODOs
