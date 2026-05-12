# Environment Variables

## Policy

This project does not use `.env` files.
Do not create `.env`, `.env.local`, or `.env.example`.

Configuration is read from OS environment variables through `pydantic-settings`.

Codex must not read, print, or inspect environment variables.
Live API keys are used only by the human developer during manual verification.

## Variables

| Name | Required for app startup | Required for live provider call | Default | Description |
|---|---:|---:|---|---|
| `GEMINI_API_KEY` | no | yes | none | Gemini API key |
| `GEMINI_MODEL` | no | no | `gemini-2.5-flash` | Gemini model |
| `OPENAI_API_KEY` | no | yes | none | OpenAI API key |
| `OPENAI_MODEL` | no | no | `gpt-5.1-mini` | OpenAI model |
| `MAX_IMAGE_BYTES` | no | no | `10485760` | Maximum image upload size |
| `ALLOWED_IMAGE_MIME_TYPES` | no | no | `image/jpeg,image/png,image/webp` | Allowed upload MIME types |

## Recommended config implementation

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.1-mini"
    max_image_bytes: int = 10_485_760
    allowed_image_mime_types: str = "image/jpeg,image/png,image/webp"

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
    )
```

Do not set `env_file`.

## Human-only live startup example

A human developer may run:

```bash
OPENAI_API_KEY="..." GEMINI_API_KEY="..." uv run uvicorn app.main:app --reload
```

This command must not be executed by Codex.

## Safe Codex testing

Codex should run only:

```bash
uv run python -m compileall app
uv run pytest
```

These tests must use fake providers and must not require real API keys.
