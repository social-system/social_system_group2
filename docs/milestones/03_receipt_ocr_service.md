# Milestone 03: Receipt OCR Service

## Goal

Implement service-level orchestration using provider interfaces and Pydantic validation.

Do not implement route-level upload handling yet unless needed by tests.
Do not implement live provider network calls.

## Scope

Implement:

- `app/services/receipt_ocr_service.py`
- Service tests using fake providers

## Service flow

```text
image bytes + mime type
  -> Gemini provider
  -> OpenAI structured provider
  -> Pydantic ReceiptOcrResponse validation
  -> add non-fatal warnings if needed
  -> return ReceiptOcrResponse
```

## Required behavior

The service must:

- Accept image bytes and MIME type
- Call Gemini provider
- Pass Gemini result to OpenAI provider
- Validate OpenAI result with Pydantic
- Return `ReceiptOcrResponse`
- Add a warning if `total_amount` and known `line_total` sum differ

## Total mismatch rule

If `total_amount` is present and all present item `line_total` values sum to a different value, do not fail.
Append a warning to top-level `warnings`.

## Provider error behavior

Provider exceptions must be allowed to propagate as typed service/provider exceptions.
HTTP mapping will be handled by route layer.

## Forbidden work

Do not implement:

- Real Gemini API call
- Real OpenAI API call
- DB registration
- `.env` files

## Required tests

- Service returns valid `ReceiptOcrResponse` with fake providers
- Null fields pass through correctly
- Total mismatch adds warning
- Invalid structured response raises validation-related error
- Gemini provider failure propagates as provider error
- OpenAI provider failure propagates as provider error

## Completion commands

```bash
uv run python -m compileall app
uv run pytest
```
