# Milestone 02: Provider Interfaces

## Goal

Create provider interfaces and fake-testable provider boundaries.

Do not implement real Gemini or OpenAI network calls in this milestone.

## Scope

Implement:

- Provider protocol or base classes
- Provider-specific exceptions
- Fake provider support for tests
- Basic service dependency wiring if useful

Suggested files:

- `app/providers/base.py`
- `app/providers/errors.py`
- `app/providers/gemini_provider.py`
- `app/providers/openai_structured_provider.py`

## Provider interfaces

Gemini provider suggested method:

```python
async def extract_receipt_text(*, image_bytes: bytes, mime_type: str) -> str:
    ...
```

OpenAI provider suggested method:

```python
async def normalize_receipt(*, gemini_result: str) -> dict:
    ...
```

## Required behavior

Providers must be replaceable in tests.
Actual provider classes may raise `NotImplementedError` until later milestones.

Define clear exception types such as:

- `ProviderConfigurationError`
- `ProviderExecutionError`
- `ProviderInvalidResponseError`

## Secret rules

Do not read, print, or inspect actual environment variable values in tests.
Do not require API keys for app startup or tests.

## Forbidden work

Do not implement:

- Live Gemini API call
- Live OpenAI API call
- `.env` files
- Database calls

## Required tests

- Fake Gemini provider can return fake OCR text
- Fake OpenAI provider can return fake structured dict
- Provider exceptions can be imported and handled
- No test requires API keys

## Completion commands

```bash
uv run python -m compileall app
uv run pytest
```
