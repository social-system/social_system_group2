# Milestone 04: Extract Endpoint

## Goal

Implement `POST /ocr/receipts/extract` using image validation and the receipt OCR service.

Use fake or injectable providers in tests.
Do not call live Gemini or OpenAI APIs.

## Scope

Implement:

- Route for `POST /ocr/receipts/extract`
- HTTP error mapping
- Endpoint tests with fake providers

## Endpoint

### POST /ocr/receipts/extract

Request:

```text
multipart/form-data
file=<receipt image>
```

Response:

`ReceiptOcrResponse` with `status = needs_confirmation`.

## HTTP error mapping

| Case | Status |
|---|---:|
| Unsupported MIME type | 400 |
| Empty file | 400 |
| Image too large | 413 |
| Provider failure | 502 |
| Structured data validation failure | 422 |
| Unexpected error | 500 |

## Dependency injection

Endpoint tests must inject fake service or fake providers.

Do not require real API keys.
Do not require file-based environment configuration.

## Forbidden work

Do not implement:

- Live Gemini API call
- Live OpenAI API call
- DB registration
- Image persistence
- Environment-file creation or templates

## Required tests

- Valid image returns 200 and `needs_confirmation`
- Unsupported MIME type returns 400
- Empty file returns 400
- Oversized file returns 413
- Provider failure returns 502
- Invalid structured response returns 422 or controlled error according to implementation

## Completion commands

```bash
uv run python -m compileall app
uv run pytest
```
