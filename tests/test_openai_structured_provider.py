import asyncio
from typing import Any

import pytest

from app.providers.errors import ProviderConfigurationError, ProviderExecutionError
from app.providers.errors import ProviderInvalidResponseError
from app.providers.openai_structured_provider import (
    OPENAI_RECEIPT_RESPONSE_FORMAT,
    OpenAIStructuredProvider,
)
from app.schemas.ocr import ReceiptOcrResponse


class FakeOpenAISettings:
    def __init__(
        self,
        *,
        openai_api_key: str | None = "test-key",
        openai_model: str = "openai-test-model",
    ) -> None:
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model


class MockOpenAIClient:
    def __init__(self, *, result: dict[str, Any] | None = None) -> None:
        self.result = result or valid_receipt_response_dict()
        self.received_model: str | None = None
        self.received_instructions: str | None = None
        self.received_response_format: dict[str, Any] | None = None
        self.received_gemini_result: str | None = None

    async def normalize_receipt(
        self,
        *,
        model: str,
        instructions: str,
        response_format: dict[str, Any],
        gemini_result: str,
    ) -> dict[str, Any]:
        self.received_model = model
        self.received_instructions = instructions
        self.received_response_format = response_format
        self.received_gemini_result = gemini_result
        return self.result


class FailingOpenAIClient:
    async def normalize_receipt(
        self,
        *,
        model: str,
        instructions: str,
        response_format: dict[str, Any],
        gemini_result: str,
    ) -> dict[str, Any]:
        raise RuntimeError("sdk failure")


def valid_receipt_response_dict() -> dict[str, Any]:
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


def assert_no_additional_properties(schema: dict[str, Any]) -> None:
    if schema.get("type") == "object":
        assert schema.get("additionalProperties") is False
        for child in schema.get("properties", {}).values():
            assert_no_additional_properties(child)
    if schema.get("type") == "array":
        assert_no_additional_properties(schema["items"])


def test_provider_sends_schema_constrained_request() -> None:
    client = MockOpenAIClient()
    provider = OpenAIStructuredProvider(
        settings=FakeOpenAISettings(),
        client=client,
    )

    result = asyncio.run(
        provider.normalize_receipt(gemini_result="fake gemini receipt text")
    )

    assert result["status"] == "needs_confirmation"
    assert client.received_model == "openai-test-model"
    assert client.received_gemini_result == "fake gemini receipt text"
    assert client.received_response_format == OPENAI_RECEIPT_RESPONSE_FORMAT
    assert client.received_response_format["strict"] is True
    assert_no_additional_properties(client.received_response_format["schema"])

    schema = client.received_response_format["schema"]
    assert set(schema["required"]) == set(schema["properties"])
    item_schema = schema["properties"]["items"]["items"]
    assert set(item_schema["required"]) == set(item_schema["properties"])
    assert "null" in schema["properties"]["store_name"]["type"]
    assert "null" in item_schema["properties"]["raw_name"]["type"]


def test_provider_returns_dict_matching_receipt_ocr_response() -> None:
    provider = OpenAIStructuredProvider(
        settings=FakeOpenAISettings(),
        client=MockOpenAIClient(),
    )

    result = asyncio.run(provider.normalize_receipt(gemini_result="fake receipt"))

    response = ReceiptOcrResponse.model_validate(result)
    assert response.status == "needs_confirmation"
    assert response.items[0].line_total == 100


@pytest.mark.parametrize("api_key", [None, ""])
def test_missing_api_key_raises_configuration_error(api_key: str | None) -> None:
    provider = OpenAIStructuredProvider(
        settings=FakeOpenAISettings(openai_api_key=api_key),
        client=MockOpenAIClient(),
    )

    with pytest.raises(ProviderConfigurationError):
        asyncio.run(provider.normalize_receipt(gemini_result="fake receipt"))


def test_client_failure_raises_provider_execution_error() -> None:
    provider = OpenAIStructuredProvider(
        settings=FakeOpenAISettings(),
        client=FailingOpenAIClient(),
    )

    with pytest.raises(ProviderExecutionError):
        asyncio.run(provider.normalize_receipt(gemini_result="fake receipt"))


def test_invalid_provider_output_raises_invalid_response_error() -> None:
    provider = OpenAIStructuredProvider(
        settings=FakeOpenAISettings(),
        client=MockOpenAIClient(
            result={
                "status": "needs_confirmation",
                "store_name": None,
                "purchased_at": "2026/05/12",
                "total_amount": None,
                "items": [],
                "warnings": [],
            }
        ),
    )

    with pytest.raises(ProviderInvalidResponseError):
        asyncio.run(provider.normalize_receipt(gemini_result="fake receipt"))


def test_schema_outside_key_raises_invalid_response_error() -> None:
    result = valid_receipt_response_dict()
    result["unexpected"] = "not allowed"
    provider = OpenAIStructuredProvider(
        settings=FakeOpenAISettings(),
        client=MockOpenAIClient(result=result),
    )

    with pytest.raises(ProviderInvalidResponseError):
        asyncio.run(provider.normalize_receipt(gemini_result="fake receipt"))


def test_provider_can_be_imported_without_api_key() -> None:
    provider = OpenAIStructuredProvider(
        settings=FakeOpenAISettings(openai_api_key=None)
    )

    assert provider is not None
