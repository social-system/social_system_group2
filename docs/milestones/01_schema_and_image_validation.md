# Milestone 01: Schema and Image Validation

## Goal

Add Pydantic response schemas and local image validation utilities.

Do not call Gemini or OpenAI in this milestone.

## Scope

Implement:

- OCR response schemas in `app/schemas/ocr.py`
- Image validation utility in `app/utils/image_validation.py`
- Unit tests for schemas and image validation

## Required schemas

Create schemas matching `docs/STRUCTURED_OUTPUT_SCHEMA.md`.

Suggested models:

- `ReceiptOcrItem`
- `ReceiptOcrResponse`

## Required schema rules

- `status` must be `needs_confirmation`
- `purchased_at` must be `YYYY-MM-DD` or null
- `total_amount`, `unit_price`, `line_total` must be null or >= 0
- `purchased_quantity`, `base_quantity` must be null or > 0
- `confidence` must be null or between 0 and 1
- `warnings` must always be a list
- item `warnings` must always be a list

## Image validation rules

Allowed MIME types are read from settings:

```text
image/jpeg,image/png,image/webp
```

Default maximum size:

```text
10485760
```

Validation must reject:

- Empty files
- Unsupported MIME types
- Files larger than max size

## Error behavior

Utility functions may raise internal exceptions or return validation results.
Route-level HTTP behavior will be implemented later.

## Forbidden work

Do not implement:

- Real OCR endpoint behavior
- Gemini provider
- OpenAI provider
- Database calls
- `.env` or `.env.example`

## Required tests

- Valid schema with null fields passes
- Invalid `status` fails
- Invalid date format fails
- Negative amount fails
- Invalid confidence fails
- JPEG MIME type passes
- Unsupported MIME type fails
- Empty file fails
- Oversized file fails

## Completion commands

```bash
uv run python -m compileall app
uv run pytest
```
