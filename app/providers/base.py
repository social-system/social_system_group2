from typing import Any, Protocol


class GeminiProviderProtocol(Protocol):
    async def extract_receipt_text(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        filename: str | None = None,
    ) -> str:
        ...


class OpenAIStructuredProviderProtocol(Protocol):
    async def normalize_receipt(
        self,
        *,
        gemini_result: str,
    ) -> dict[str, Any]:
        ...
