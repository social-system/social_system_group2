import asyncio
import base64
import json
from typing import Any, Protocol
from urllib import parse, request

from app.config import Settings, get_settings
from app.providers.errors import (
    ProviderConfigurationError,
    ProviderExecutionError,
    ProviderInvalidResponseError,
)

GEMINI_RECEIPT_PROMPT = """
You are reading a receipt image for an OCR preprocessing step.

Extract only information that is visible on the receipt. Do not guess.
If a value is unclear or missing, mark it as unknown/null in the intermediate result.
Return intermediate text or JSON-like text for a later normalization step; this output
is not trusted final JSON.

Capture these candidates when visible:
- store name
- purchase date
- total amount paid
- item rows
- quantities and units
- unit prices
- line totals
- warnings for unclear, ignored, or ambiguous lines

Do not include product IDs, category IDs, database IDs, inventory updates, or recipe
recommendations.
""".strip()


class GeminiProviderSettings(Protocol):
    gemini_api_key: str | None
    gemini_model: str


class GeminiClientProtocol(Protocol):
    async def generate_receipt_text(
        self,
        *,
        model: str,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        ...


class GeminiRestClient:
    def __init__(self, *, api_key: str, timeout_seconds: float = 30.0) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    async def generate_receipt_text(
        self,
        *,
        model: str,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        return await asyncio.to_thread(
            self._generate_receipt_text_sync,
            model=model,
            prompt=prompt,
            image_bytes=image_bytes,
            mime_type=mime_type,
        )

    def _generate_receipt_text_sync(
        self,
        *,
        model: str,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{parse.quote(model, safe='')}:generateContent?"
            f"{parse.urlencode({'key': self._api_key})}"
        )
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            }
                        },
                    ],
                }
            ]
        }
        http_request = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(  # noqa: S310
                http_request,
                timeout=self._timeout_seconds,
            ) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise ProviderExecutionError("Gemini provider request failed.") from exc

        return self._extract_text(response_payload)

    @staticmethod
    def _extract_text(response_payload: dict[str, Any]) -> str:
        candidates = response_payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise ProviderInvalidResponseError("Gemini response did not contain text.")

        content = candidates[0].get("content")
        if not isinstance(content, dict):
            raise ProviderInvalidResponseError("Gemini response did not contain text.")

        parts = content.get("parts")
        if not isinstance(parts, list):
            raise ProviderInvalidResponseError("Gemini response did not contain text.")

        text_parts = [
            part.get("text")
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        text = "\n".join(part.strip() for part in text_parts if part.strip())
        if not text:
            raise ProviderInvalidResponseError("Gemini response did not contain text.")

        return text


class GeminiProvider:
    def __init__(
        self,
        *,
        settings: GeminiProviderSettings | None = None,
        client: GeminiClientProtocol | None = None,
    ) -> None:
        self._settings = settings
        self._client = client

    async def extract_receipt_text(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        filename: str | None = None,
    ) -> str:
        settings = self._settings or get_settings()
        api_key = settings.gemini_api_key
        if not api_key:
            raise ProviderConfigurationError("Gemini provider is not configured.")

        client = self._client or GeminiRestClient(api_key=api_key)
        try:
            return await client.generate_receipt_text(
                model=settings.gemini_model,
                prompt=GEMINI_RECEIPT_PROMPT,
                image_bytes=image_bytes,
                mime_type=mime_type.strip().lower(),
            )
        except ProviderConfigurationError:
            raise
        except ProviderInvalidResponseError:
            raise
        except ProviderExecutionError:
            raise
        except Exception as exc:
            raise ProviderExecutionError("Gemini provider failed.") from exc
