import asyncio
from typing import Any

import pytest
from pydantic import ValidationError

from app.providers.errors import (
    GeminiProviderError,
    OpenAIProviderError,
    ProviderConfigurationError,
    ProviderExecutionError,
)
from app.schemas.ocr import ReceiptOcrResponse
from app.services.receipt_ocr_service import (
    TOTAL_MISMATCH_WARNING,
    ReceiptOcrService,
)
from app.utils.image_validation import UnsupportedImageTypeError


class FakeImageSettings:
    max_image_bytes = 100
    allowed_image_mime_types = ["image/jpeg", "image/png", "image/webp"]


class FakeGeminiProvider:
    def __init__(self, result: str = "fake receipt text") -> None:
        self.result = result
        self.received_image_bytes: bytes | None = None
        self.received_mime_type: str | None = None
        self.received_filename: str | None = None

    async def extract_receipt_text(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        filename: str | None = None,
    ) -> str:
        self.received_image_bytes = image_bytes
        self.received_mime_type = mime_type
        self.received_filename = filename
        return self.result


class FailingGeminiProvider:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error or ProviderExecutionError("gemini failed")

    async def extract_receipt_text(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        filename: str | None = None,
    ) -> str:
        raise self.error


class FakeOpenAIProvider:
    def __init__(self, result: dict[str, Any] | None = None) -> None:
        self.result = result or valid_structured_response()
        self.received_gemini_result: str | None = None

    async def normalize_receipt(
        self,
        *,
        gemini_result: str,
    ) -> dict[str, Any]:
        self.received_gemini_result = gemini_result
        return self.result


class FailingOpenAIProvider:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error or ProviderExecutionError("openai failed")

    async def normalize_receipt(
        self,
        *,
        gemini_result: str,
    ) -> dict[str, Any]:
        raise self.error


def valid_structured_response() -> dict[str, Any]:
    return {
        "status": "needs_confirmation",
        "store_name": "Test Store",
        "purchased_at": "2026-05-12",
        "total_amount": 100,
        "items": [
            {
                "raw_name": "egg",
                "normalized_name": "egg",
                "category_name": "food",
                "purchased_quantity": 1,
                "purchased_unit": "pack",
                "base_quantity": 10,
                "base_unit": "piece",
                "unit_price": 100,
                "line_total": 100,
                "is_inventory_target": True,
                "confidence": 0.9,
                "warnings": [],
            }
        ],
        "warnings": [],
    }


def make_service(
    *,
    gemini_provider: Any | None = None,
    openai_provider: Any | None = None,
) -> ReceiptOcrService:
    return ReceiptOcrService(
        gemini_provider=gemini_provider or FakeGeminiProvider(),
        openai_provider=openai_provider or FakeOpenAIProvider(),
        image_validation_settings=FakeImageSettings(),
    )


def test_service_returns_valid_response_with_fake_providers() -> None:
    gemini_provider = FakeGeminiProvider()
    openai_provider = FakeOpenAIProvider()
    service = make_service(
        gemini_provider=gemini_provider,
        openai_provider=openai_provider,
    )

    response = asyncio.run(
        service.extract_receipt(
            image_bytes=b"receipt-image",
            mime_type="image/jpeg",
            filename="receipt.jpg",
        )
    )

    assert isinstance(response, ReceiptOcrResponse)
    assert response.status == "needs_confirmation"
    assert response.store_name == "Test Store"
    assert gemini_provider.received_image_bytes == b"receipt-image"
    assert gemini_provider.received_mime_type == "image/jpeg"
    assert gemini_provider.received_filename == "receipt.jpg"
    assert openai_provider.received_gemini_result == "fake receipt text"


def test_null_fields_pass_through() -> None:
    service = make_service(
        openai_provider=FakeOpenAIProvider(
            {
                "status": "needs_confirmation",
                "store_name": None,
                "purchased_at": None,
                "total_amount": None,
                "items": [
                    {
                        "raw_name": None,
                        "normalized_name": None,
                        "category_name": None,
                        "purchased_quantity": None,
                        "purchased_unit": None,
                        "base_quantity": None,
                        "base_unit": None,
                        "unit_price": None,
                        "line_total": None,
                        "is_inventory_target": None,
                        "confidence": None,
                        "warnings": [],
                    }
                ],
                "warnings": [],
            }
        )
    )

    response = asyncio.run(
        service.extract_receipt(image_bytes=b"receipt-image", mime_type="image/png")
    )

    assert response.store_name is None
    assert response.purchased_at is None
    assert response.total_amount is None
    assert response.items[0].line_total is None
    assert response.warnings == []


def test_total_mismatch_adds_warning_and_ignores_null_line_totals() -> None:
    data = valid_structured_response()
    data["total_amount"] = 150
    data["items"] = [
        {**data["items"][0], "line_total": 100},
        {**data["items"][0], "raw_name": "unknown", "line_total": None},
    ]
    service = make_service(openai_provider=FakeOpenAIProvider(data))

    response = asyncio.run(
        service.extract_receipt(image_bytes=b"receipt-image", mime_type="image/webp")
    )

    assert TOTAL_MISMATCH_WARNING in response.warnings


def test_invalid_structured_response_raises_validation_error() -> None:
    service = make_service(
        openai_provider=FakeOpenAIProvider(
            {
                "status": "needs_confirmation",
                "store_name": None,
                "purchased_at": "2026/05/12",
                "total_amount": None,
                "items": [],
                "warnings": [],
            }
        )
    )

    with pytest.raises(ValidationError):
        asyncio.run(
            service.extract_receipt(image_bytes=b"receipt-image", mime_type="image/jpeg")
        )


def test_image_validation_error_propagates() -> None:
    service = make_service()

    with pytest.raises(UnsupportedImageTypeError):
        asyncio.run(
            service.extract_receipt(
                image_bytes=b"receipt-image",
                mime_type="application/pdf",
            )
        )


def test_gemini_provider_failure_propagates() -> None:
    service = make_service(gemini_provider=FailingGeminiProvider())

    with pytest.raises(GeminiProviderError):
        asyncio.run(
            service.extract_receipt(image_bytes=b"receipt-image", mime_type="image/jpeg")
        )


def test_openai_provider_failure_propagates() -> None:
    service = make_service(openai_provider=FailingOpenAIProvider())

    with pytest.raises(OpenAIProviderError):
        asyncio.run(
            service.extract_receipt(image_bytes=b"receipt-image", mime_type="image/jpeg")
        )


def test_provider_configuration_error_is_not_wrapped() -> None:
    service = make_service(
        gemini_provider=FailingGeminiProvider(
            ProviderConfigurationError("not configured")
        )
    )

    with pytest.raises(ProviderConfigurationError):
        asyncio.run(
            service.extract_receipt(image_bytes=b"receipt-image", mime_type="image/jpeg")
        )
