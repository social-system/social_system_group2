import asyncio

import pytest

from app.providers.errors import ProviderConfigurationError, ProviderExecutionError
from app.providers.gemini_provider import GEMINI_RECEIPT_PROMPT, GeminiProvider


class FakeGeminiSettings:
    def __init__(
        self,
        *,
        gemini_api_key: str | None = "test-key",
        gemini_model: str = "gemini-test-model",
    ) -> None:
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model


class MockGeminiClient:
    def __init__(self, *, result: str = "intermediate receipt text") -> None:
        self.result = result
        self.received_model: str | None = None
        self.received_prompt: str | None = None
        self.received_image_bytes: bytes | None = None
        self.received_mime_type: str | None = None

    async def generate_receipt_text(
        self,
        *,
        model: str,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        self.received_model = model
        self.received_prompt = prompt
        self.received_image_bytes = image_bytes
        self.received_mime_type = mime_type
        return self.result


class FailingGeminiClient:
    async def generate_receipt_text(
        self,
        *,
        model: str,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        raise RuntimeError("sdk failure")


def test_provider_builds_request_using_image_bytes_and_mime_type() -> None:
    client = MockGeminiClient()
    provider = GeminiProvider(
        settings=FakeGeminiSettings(),
        client=client,
    )

    result = asyncio.run(
        provider.extract_receipt_text(
            image_bytes=b"receipt-image",
            mime_type=" IMAGE/JPEG ",
            filename="receipt.jpg",
        )
    )

    assert result == "intermediate receipt text"
    assert client.received_model == "gemini-test-model"
    assert client.received_image_bytes == b"receipt-image"
    assert client.received_mime_type == "image/jpeg"
    assert client.received_prompt == GEMINI_RECEIPT_PROMPT
    assert "store name" in client.received_prompt
    assert "total amount" in client.received_prompt
    assert "line totals" in client.received_prompt


def test_provider_returns_text_from_mocked_gemini_response() -> None:
    provider = GeminiProvider(
        settings=FakeGeminiSettings(),
        client=MockGeminiClient(result='{"store_name": "Test Store"}'),
    )

    result = asyncio.run(
        provider.extract_receipt_text(
            image_bytes=b"receipt-image",
            mime_type="image/png",
        )
    )

    assert result == '{"store_name": "Test Store"}'


@pytest.mark.parametrize("api_key", [None, ""])
def test_missing_api_key_raises_configuration_error(api_key: str | None) -> None:
    provider = GeminiProvider(
        settings=FakeGeminiSettings(gemini_api_key=api_key),
        client=MockGeminiClient(),
    )

    with pytest.raises(ProviderConfigurationError):
        asyncio.run(
            provider.extract_receipt_text(
                image_bytes=b"receipt-image",
                mime_type="image/jpeg",
            )
        )


def test_client_failure_raises_provider_execution_error() -> None:
    provider = GeminiProvider(
        settings=FakeGeminiSettings(),
        client=FailingGeminiClient(),
    )

    with pytest.raises(ProviderExecutionError):
        asyncio.run(
            provider.extract_receipt_text(
                image_bytes=b"receipt-image",
                mime_type="image/webp",
            )
        )


def test_provider_can_be_imported_without_api_key() -> None:
    provider = GeminiProvider(settings=FakeGeminiSettings(gemini_api_key=None))

    assert provider is not None
