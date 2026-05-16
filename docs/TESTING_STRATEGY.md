# Testing Strategy

## Main rule

Tests must not require real API keys.
Tests must not call real Gemini or OpenAI APIs.
Tests must not require `.env` files.

All external providers must be mocked or faked.

## Required test categories

### Health check

- `GET /health` returns 200
- Response is `{"status": "ok"}`

### Image validation

- JPEG is accepted
- PNG is accepted
- WebP is accepted
- Unsupported MIME type returns 400
- Empty file returns 400
- Oversized file returns 413

### OCR extraction endpoint

- Valid image returns `status = needs_confirmation`
- Provider calls are invoked through service/provider boundaries
- Response contains top-level `warnings`
- Response accepts `null` fields where allowed

### Provider failure

- Gemini failure returns 502
- OpenAI failure returns 502
- Structured output validation failure returns 422 or 502 according to implementation choice
- Missing provider key during real provider path returns controlled error

### Business rules

- Mismatched total and item sum returns warning, not failure
- `confidence` must be between 0 and 1
- Negative amount fails validation
- Invalid date format fails validation

## Fake providers

Use fake providers in tests.
Do not monkeypatch environment variables with real secrets.

Example:

```python
class FakeGeminiProvider:
    async def extract_receipt_text(self, *, image_bytes: bytes, mime_type: str) -> str:
        return "fake receipt"

class FakeOpenAIProvider:
    async def normalize_receipt(self, *, gemini_result: str) -> dict:
        return {
            "status": "needs_confirmation",
            "store_name": "Test Store",
            "purchased_at": "2026-05-12",
            "total_amount": 100,
            "items": [
                {
                    "raw_name": "卵",
                    "normalized_name": "卵",
                    "category_name": "食費",
                    "purchased_quantity": 1,
                    "purchased_unit": "パック",
                    "base_quantity": 10,
                    "base_unit": "個",
                    "unit_price": 100,
                    "line_total": 100,
                    "is_inventory_target": True,
                    "confidence": 0.9,
                    "warnings": [],
                }
            ],
            "warnings": [],
        }
```

## Commands to run

Every milestone must end with:

```bash
uv run python -m compileall app
uv run pytest
```

If a milestone adds linting, also run:

```bash
uv run ruff check .
```

## What not to test in Codex tasks

Do not test actual Gemini image recognition.
Do not test actual OpenAI Structured Outputs network calls.
Do not test real receipt images containing personal information.
Do not use file-based environment configuration.
