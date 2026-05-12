# OCR Project Specification

## Purpose

This project provides a Receipt OCR API for a household accounting and refrigerator inventory application.

The API receives a receipt image and returns structured candidate data for frontend confirmation.

The API does not write to a database.
The API does not decide final accounting records.
The API does not directly update inventory.

## Core flow

```text
Receipt image
  -> image validation
  -> Gemini image reading
  -> OpenAI Structured Outputs normalization
  -> Pydantic validation
  -> frontend confirmation response
```

The OCR result is not trusted as final data. It is temporary candidate data.

## Responsibility split

| Layer | Responsibility |
|---|---|
| OCR API | Read image and return candidate receipt data |
| Frontend | Show candidate data and let the user confirm or correct it |
| Database API | Save confirmed receipt and receipt items |
| Inventory API | Reflect confirmed inventory target items |
| Recipe API | Suggest recipes from confirmed inventory data |

## Non-goals

This project must not implement:

- Database registration
- Database API calls
- Inventory table updates
- Recipe recommendation
- User authentication
- Image persistence
- Background queue processing

## Provider roles

### Gemini

Gemini is used for image reading.
It receives the receipt image and extracts as much visible information as possible.
Gemini output is treated as untrusted intermediate text or JSON-like data.

### OpenAI Structured Outputs

OpenAI Structured Outputs is used to convert Gemini's intermediate extraction into a strict JSON shape.
It must follow the schema in `docs/STRUCTURED_OUTPUT_SCHEMA.md`.

### Pydantic

Pydantic validates the final structured response before returning it to the frontend.

## Secret policy

This project does not use `.env` files.
Configuration must be read from OS environment variables.

Real API keys must not be placed in project files.
Codex must not read or print environment variables.
External provider tests must use mocks.

## Required environment variables for live manual testing

These variables may be set by a human developer only when manually testing live providers:

```text
GEMINI_API_KEY
GEMINI_MODEL
OPENAI_API_KEY
OPENAI_MODEL
MAX_IMAGE_BYTES
ALLOWED_IMAGE_MIME_TYPES
```

The application must start without API keys.
Actual provider execution should fail clearly if required keys are missing.

## Default configuration

| Name | Default | Meaning |
|---|---|---|
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `OPENAI_MODEL` | `gpt-5.1-mini` | OpenAI model name |
| `MAX_IMAGE_BYTES` | `10485760` | 10MB upload limit |
| `ALLOWED_IMAGE_MIME_TYPES` | `image/jpeg,image/png,image/webp` | Allowed image MIME types |

If the actual codebase uses different current model names, keep model names configurable through environment variables.

## Quality requirements

The API should be conservative.
If a field cannot be read safely, return `null` instead of inventing a value.
If a total does not match item totals, do not fail the request. Return a warning.
If the image cannot be read as a receipt, return a stable error response.

## Privacy requirements

Do not log full receipt contents by default.
Do not log uploaded image bytes.
Do not persist uploaded image files.
Do not persist OCR provider responses.
Do not expose API keys or environment variables in logs or error responses.
