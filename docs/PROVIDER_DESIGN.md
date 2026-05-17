# Provider Design

## Purpose

External model calls must be isolated behind provider classes.
This makes unit tests safe and allows the project to run without real API keys.

## Required provider boundary

```text
Route
  -> ReceiptOcrService
      -> GeminiProvider
      -> OpenAIStructuredProvider
      -> Pydantic validation
```

Routes must not directly call Gemini or OpenAI SDKs.

## Gemini provider

### Responsibility

- Receive validated image bytes and MIME type
- Send image and instruction prompt to Gemini
- Return intermediate OCR text or JSON-like extraction result

### It must not

- Return final API response directly
- Write to a database
- Persist images
- Log image bytes
- Print API keys

### Suggested interface

```python
class GeminiProvider:
    async def extract_receipt_text(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        ...
```

The actual return type may be a string or a small internal model, but the provider output must be treated as untrusted intermediate data.

## OpenAI Structured provider

### Responsibility

- Receive Gemini intermediate result
- Apply the strict structured output schema
- Return a dict or Pydantic model matching `ReceiptOcrResponse`

### It must not

- Call Gemini
- Read image files
- Register data in a database
- Persist output
- Print API keys

### Suggested interface

```python
class OpenAIStructuredProvider:
    async def normalize_receipt(
        self,
        *,
        gemini_result: str,
    ) -> dict:
        ...
```

## API key behavior

The app must start without API keys.

Provider constructors may accept keys as optional values.
Actual provider methods must check whether required keys exist before live API execution.

If a key is missing during a real provider call, raise a clear internal configuration exception such as:

```text
ProviderConfigurationError
```

Do not include secret values in the exception.

## Mocking requirement

Tests must replace provider implementations with fake providers.

Example fake provider behavior:

```python
class FakeGeminiProvider:
    async def extract_receipt_text(self, *, image_bytes: bytes, mime_type: str) -> str:
        return "receipt text"

class FakeOpenAIStructuredProvider:
    async def normalize_receipt(self, *, gemini_result: str) -> dict:
        return {
            "status": "needs_confirmation",
            "store_name": "Test Store",
            "purchased_at": "2026-05-12",
            "total_amount": 100,
            "items": [],
            "warnings": [],
        }
```

## Configuration source

Configuration must be read from OS environment variables only.
Do not use `.env` files.

Suggested `Settings` behavior:

```python
class Settings(BaseSettings):
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4-mini"
    max_image_bytes: int = 10_485_760
    allowed_image_mime_types: str = "image/jpeg,image/png,image/webp"

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
    )
```

Do not configure `env_file`.

## Live manual verification

Codex must not run live provider calls.

A human developer may manually run:

```bash
OPENAI_API_KEY="..." GEMINI_API_KEY="..." uv run uvicorn app.main:app --reload
```

This command is documentation only. Do not ask Codex to execute it.
