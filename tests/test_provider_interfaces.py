import asyncio
from typing import Any

import pytest

from app.providers import (
    GeminiProviderError,
    OpenAIProviderError,
    GeminiProviderProtocol,
    OpenAIStructuredProviderProtocol,
    ProviderConfigurationError,
    ProviderExecutionError,
    ProviderInvalidResponseError,
)
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_structured_provider import OpenAIStructuredProvider


class FakeGeminiSettings:
    gemini_api_key = None
    gemini_model = "test-gemini-model"


class FakeOpenAISettings:
    openai_api_key = None
    openai_model = "test-openai-model"


class FakeGeminiProvider:
    async def extract_receipt_text(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        filename: str | None = None,
    ) -> str:
        assert image_bytes == b"receipt"
        assert mime_type == "image/jpeg"
        assert filename == "receipt.jpg"
        return "fake receipt text"


class FakeOpenAIStructuredProvider:
    async def normalize_receipt(
        self,
        *,
        gemini_result: str,
    ) -> dict[str, Any]:
        assert gemini_result == "fake receipt text"
        return {
            "status": "needs_confirmation",
            "store_name": "Test Store",
            "purchased_at": "2026-05-12",
            "total_amount": 100,
            "items": [],
            "warnings": [],
        }


async def _read_with_gemini(provider: GeminiProviderProtocol) -> str:
    return await provider.extract_receipt_text(
        image_bytes=b"receipt",
        mime_type="image/jpeg",
        filename="receipt.jpg",
    )


async def _normalize_with_openai(
    provider: OpenAIStructuredProviderProtocol,
) -> dict[str, Any]:
    return await provider.normalize_receipt(gemini_result="fake receipt text")


def test_fake_gemini_provider_can_return_fake_ocr_text() -> None:
    result = asyncio.run(_read_with_gemini(FakeGeminiProvider()))

    assert result == "fake receipt text"


def test_fake_openai_provider_can_return_fake_structured_dict() -> None:
    result = asyncio.run(_normalize_with_openai(FakeOpenAIStructuredProvider()))

    assert result["status"] == "needs_confirmation"
    assert result["items"] == []


@pytest.mark.parametrize(
    "error_type",
    [
        GeminiProviderError,
        OpenAIProviderError,
        ProviderConfigurationError,
        ProviderExecutionError,
        ProviderInvalidResponseError,
    ],
)
def test_provider_exceptions_can_be_imported_and_handled(
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type):
        raise error_type("provider error")


def test_real_provider_stubs_do_not_call_external_apis() -> None:
    with pytest.raises(ProviderConfigurationError):
        asyncio.run(
            GeminiProvider(settings=FakeGeminiSettings()).extract_receipt_text(
                image_bytes=b"receipt",
                mime_type="image/jpeg",
            )
        )

    with pytest.raises(ProviderConfigurationError):
        asyncio.run(
            OpenAIStructuredProvider(settings=FakeOpenAISettings()).normalize_receipt(
                gemini_result="fake receipt text"
            )
        )
