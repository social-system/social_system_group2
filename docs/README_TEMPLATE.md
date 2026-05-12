# Receipt OCR API

## Overview

This project provides a Receipt OCR API.

It receives a receipt image and returns structured candidate data for frontend confirmation.

It does not write to a database.
It does not call the database API.
It does not update inventory.
It does not suggest recipes.

## Setup

```bash
uv sync
```

## Run development server

Without live providers:

```bash
uv run uvicorn app.main:app --reload
```

With live providers, a human developer may pass environment variables for the current command only:

```bash
OPENAI_API_KEY="..." GEMINI_API_KEY="..." uv run uvicorn app.main:app --reload
```

Do not store API keys in project files.
This project does not use `.env` files.

## Health check

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## Extract receipt

```bash
curl -X POST "http://127.0.0.1:8000/ocr/receipts/extract" \
  -F "file=@sample_receipt.jpg;type=image/jpeg"
```

## Test

```bash
uv run python -m compileall app
uv run pytest
```

Tests do not call real Gemini or OpenAI APIs.
Tests do not require API keys.
