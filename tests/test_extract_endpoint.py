from typing import Any

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.providers.errors import (
    GeminiProviderError,
    OpenAIProviderError,
    ProviderConfigurationError,
    ProviderExecutionError,
)
from app.routes.ocr import get_receipt_ocr_service
from app.schemas.ocr import ReceiptOcrResponse
from app.services.receipt_ocr_service import TOTAL_MISMATCH_WARNING
from app.utils.image_validation import (
    EmptyImageError,
    ImageTooLargeError,
    UnsupportedImageTypeError,
)


class FakeReceiptOcrService:
    def __init__(self, result: ReceiptOcrResponse | None = None) -> None:
        self.result = result or ReceiptOcrResponse(
            status="needs_confirmation",
            store_name="Test Store",
            purchased_at="2026-05-12",
            total_amount=100,
            items=[],
            warnings=[],
        )
        self.received_image_bytes: bytes | None = None
        self.received_mime_type: str | None = None
        self.received_filename: str | None = None

    async def extract_receipt(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        filename: str | None = None,
    ) -> ReceiptOcrResponse:
        self.received_image_bytes = image_bytes
        self.received_mime_type = mime_type
        self.received_filename = filename
        return self.result


class RaisingReceiptOcrService:
    def __init__(self, error: Exception) -> None:
        self.error = error

    async def extract_receipt(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        filename: str | None = None,
    ) -> ReceiptOcrResponse:
        raise self.error


def post_extract_with_service(
    service: Any,
    *,
    content: bytes = b"receipt-image",
    content_type: str = "image/jpeg",
) -> Any:
    app.dependency_overrides[get_receipt_ocr_service] = lambda: service
    try:
        with TestClient(app) as client:
            return client.post(
                "/ocr/receipts/extract",
                files={"file": ("receipt.jpg", content, content_type)},
            )
    finally:
        app.dependency_overrides.clear()


def test_valid_image_upload_returns_needs_confirmation() -> None:
    service = FakeReceiptOcrService()

    response = post_extract_with_service(service)

    assert response.status_code == 200
    assert response.json()["status"] == "needs_confirmation"
    assert service.received_image_bytes == b"receipt-image"
    assert service.received_mime_type == "image/jpeg"
    assert service.received_filename == "receipt.jpg"


def test_unsupported_mime_type_returns_400() -> None:
    response = post_extract_with_service(
        RaisingReceiptOcrService(UnsupportedImageTypeError("unsupported"))
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "unsupported_image_type"


def test_oversized_file_returns_413() -> None:
    response = post_extract_with_service(
        RaisingReceiptOcrService(ImageTooLargeError("too large"))
    )

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "image_too_large"


def test_empty_file_returns_400() -> None:
    response = post_extract_with_service(
        RaisingReceiptOcrService(EmptyImageError("empty"))
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "empty_file"


def test_provider_failure_returns_502() -> None:
    response = post_extract_with_service(
        RaisingReceiptOcrService(ProviderExecutionError("provider failed"))
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "ocr_provider_failed"


def test_gemini_provider_failure_returns_502() -> None:
    response = post_extract_with_service(
        RaisingReceiptOcrService(GeminiProviderError("gemini failed"))
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "gemini_provider_failed"


def test_openai_provider_failure_returns_502() -> None:
    response = post_extract_with_service(
        RaisingReceiptOcrService(OpenAIProviderError("openai failed"))
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "openai_provider_failed"


def test_provider_configuration_error_returns_502() -> None:
    response = post_extract_with_service(
        RaisingReceiptOcrService(ProviderConfigurationError("not configured"))
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "provider_not_configured"


def test_invalid_structured_response_returns_422() -> None:
    validation_error: ValidationError | None = None
    try:
        ReceiptOcrResponse.model_validate(
            {
                "status": "needs_confirmation",
                "store_name": None,
                "purchased_at": "2026/05/12",
                "total_amount": None,
                "items": [],
                "warnings": [],
            }
        )
    except ValidationError as exc:
        validation_error = exc

    assert validation_error is not None
    response = post_extract_with_service(RaisingReceiptOcrService(validation_error))

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "structured_output_invalid"


def test_total_mismatch_returns_200_with_warnings() -> None:
    service = FakeReceiptOcrService(
        ReceiptOcrResponse(
            status="needs_confirmation",
            store_name="Test Store",
            purchased_at="2026-05-12",
            total_amount=150,
            items=[],
            warnings=[TOTAL_MISMATCH_WARNING],
        )
    )

    response = post_extract_with_service(service)

    assert response.status_code == 200
    assert TOTAL_MISMATCH_WARNING in response.json()["warnings"]
