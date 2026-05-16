# Error Handling

## Goals

Errors must be stable and safe.

Do not expose:

- API keys
- Environment variable values
- Uploaded image bytes
- Full provider raw responses
- Internal stack traces

## Error response shape

Use a consistent error shape where practical.

```json
{
  "detail": {
    "code": "unsupported_image_type",
    "message": "Unsupported image type."
  }
}
```

FastAPI validation errors may use FastAPI's standard 422 response unless a route-specific error is clearer.

## HTTP status mapping

| Status | Code | Meaning |
|---:|---|---|
| 400 | `unsupported_image_type` | MIME type is not allowed |
| 400 | `empty_file` | File is empty |
| 413 | `image_too_large` | Uploaded image exceeds size limit |
| 422 | `receipt_not_readable` | Image could not be interpreted as a receipt |
| 422 | `structured_output_invalid` | Final structured data failed validation |
| 502 | `provider_not_configured` | A live OCR provider was called without required configuration |
| 502 | `ocr_provider_failed` | OCR provider failed |
| 502 | `gemini_provider_failed` | Gemini provider failed |
| 502 | `openai_provider_failed` | OpenAI provider failed |
| 500 | `internal_server_error` | Unexpected server error |

## Missing API key behavior

The app must start without API keys.

If a real provider method is called without a required key, return a controlled provider failure.
Recommended external response:

```json
{
  "detail": {
    "code": "provider_not_configured",
    "message": "OCR provider is not configured."
  }
}
```

Do not state which key is missing in public API responses.
Internal logs may mention provider name only, not secret values.

## Logging rules

Do not log:

- Request image bytes
- Base64 image strings
- Full OCR text by default
- API keys
- Environment variable dumps

Allowed logs:

- Request started
- Request completed
- Provider name
- Error code
- File size
- MIME type

## Non-fatal inconsistencies

The following should not cause request failure:

- Total amount and item sum differ
- Some item units are unknown
- Some normalized names are unknown
- Some inventory target flags are unknown

Return the response with `warnings` instead.
