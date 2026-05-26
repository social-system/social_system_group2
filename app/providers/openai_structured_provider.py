import asyncio
import json
from typing import Any, Protocol
from urllib import request

from pydantic import ValidationError

from app.config import get_settings
from app.providers.errors import (
    ProviderConfigurationError,
    ProviderExecutionError,
    ProviderInvalidResponseError,
)
from app.schemas.ocr import ReceiptOcrResponse

OPENAI_RECEIPT_NORMALIZATION_INSTRUCTIONS = """
Convert Gemini's untrusted receipt OCR intermediate output into the strict
ReceiptOcrResponse JSON shape.

Use status = "needs_confirmation".
Use null for unknown optional values.
Do not invent values that are not supported by the OCR text.
For store_name, use a visible receipt header store, branch, supermarket, or
convenience store name only. Do not use an address, phone number, or company
name alone. If the store name is unclear or low confidence, return null and add
a warning.
Return warnings for uncertainty, ignored lines, unclear dates, unclear totals, or
unit conversion uncertainty.
Do not proactively warn about a mismatch between total_amount and item line totals;
the service layer performs that deterministic check once after validation.
Treat normalized_name as an OCR-estimated product name candidate only. It is not a
database product master name and does not have to match products.name.
For ocr_metadata, include field-level confidence when you can estimate it.
Set auto_register_candidate to false and add needs_review_reasons when the item
has uncertainty that should prevent automatic database registration. If no
specific reason is known, use an empty needs_review_reasons list.
Do not include database IDs, product IDs, category IDs, inventory updates, recipe
recommendations, authentication data, or any fields outside the schema.
""".strip()

RECEIPT_OCR_FIELD_CONFIDENCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "raw_name": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "normalized_name": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "category_name": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "purchased_quantity": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "purchased_unit": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "base_quantity": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "base_unit": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "unit_price": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "line_total": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "is_inventory_target": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
    },
    "required": [
        "raw_name",
        "normalized_name",
        "category_name",
        "purchased_quantity",
        "purchased_unit",
        "base_quantity",
        "base_unit",
        "unit_price",
        "line_total",
        "is_inventory_target",
    ],
}


RECEIPT_OCR_ITEM_METADATA_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "field_confidence": RECEIPT_OCR_FIELD_CONFIDENCE_SCHEMA,
        "auto_register_candidate": {"type": ["boolean", "null"]},
        "needs_review_reasons": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "field_confidence",
        "auto_register_candidate",
        "needs_review_reasons",
    ],
}

RECEIPT_OCR_ITEM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "raw_name": {"type": ["string", "null"]},
        "normalized_name": {"type": ["string", "null"]},
        "category_name": {"type": ["string", "null"]},
        "purchased_quantity": {"type": ["number", "null"], "exclusiveMinimum": 0},
        "purchased_unit": {"type": ["string", "null"]},
        "base_quantity": {"type": ["number", "null"], "exclusiveMinimum": 0},
        "base_unit": {"type": ["string", "null"]},
        "unit_price": {"type": ["integer", "null"], "minimum": 0},
        "line_total": {"type": ["integer", "null"], "minimum": 0},
        "is_inventory_target": {"type": ["boolean", "null"]},
        "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "ocr_metadata": RECEIPT_OCR_ITEM_METADATA_SCHEMA,
    },
    "required": [
        "raw_name",
        "normalized_name",
        "category_name",
        "purchased_quantity",
        "purchased_unit",
        "base_quantity",
        "base_unit",
        "unit_price",
        "line_total",
        "is_inventory_target",
        "confidence",
        "warnings",
        "ocr_metadata",
    ],
}


RECEIPT_OCR_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "status": {"type": "string", "enum": ["needs_confirmation"]},
        "store_name": {"type": ["string", "null"]},
        "purchased_at": {
            "type": ["string", "null"],
            "pattern": r"^\d{4}-\d{2}-\d{2}$",
        },
        "total_amount": {"type": ["integer", "null"], "minimum": 0},
        "items": {"type": "array", "items": RECEIPT_OCR_ITEM_SCHEMA},
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "status",
        "store_name",
        "purchased_at",
        "total_amount",
        "items",
        "warnings",
    ],
}


OPENAI_RECEIPT_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "name": "receipt_ocr_response",
    "strict": True,
    "schema": RECEIPT_OCR_RESPONSE_SCHEMA,
}


class OpenAIProviderSettings(Protocol):
    openai_api_key: str | None
    openai_model: str


class OpenAIClientProtocol(Protocol):
    async def normalize_receipt(
        self,
        *,
        model: str,
        instructions: str,
        response_format: dict[str, Any],
        gemini_result: str,
    ) -> dict[str, Any]:
        ...


class OpenAIRestClient:
    def __init__(self, *, api_key: str, timeout_seconds: float = 30.0) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    async def normalize_receipt(
        self,
        *,
        model: str,
        instructions: str,
        response_format: dict[str, Any],
        gemini_result: str,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(
            self._normalize_receipt_sync,
            model=model,
            instructions=instructions,
            response_format=response_format,
            gemini_result=gemini_result,
        )

    def _normalize_receipt_sync(
        self,
        *,
        model: str,
        instructions: str,
        response_format: dict[str, Any],
        gemini_result: str,
    ) -> dict[str, Any]:
        payload = {
            "model": model,
            "input": [
                {"role": "system", "content": instructions},
                {
                    "role": "user",
                    "content": (
                        "Normalize this untrusted Gemini receipt OCR output:\n\n"
                        f"{gemini_result}"
                    ),
                },
            ],
            "text": {"format": response_format},
        }
        http_request = request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(  # noqa: S310
                http_request,
                timeout=self._timeout_seconds,
            ) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise ProviderExecutionError("OpenAI provider request failed.") from exc

        return self._extract_structured_json(response_payload)

    @staticmethod
    def _extract_structured_json(response_payload: dict[str, Any]) -> dict[str, Any]:
        if isinstance(response_payload.get("output_text"), str):
            return _json_object_from_text(response_payload["output_text"])

        output = response_payload.get("output")
        if not isinstance(output, list):
            raise ProviderInvalidResponseError("OpenAI response did not contain JSON.")

        text_parts: list[str] = []
        for output_item in output:
            if not isinstance(output_item, dict):
                continue
            content = output_item.get("content")
            if not isinstance(content, list):
                continue
            for content_item in content:
                if not isinstance(content_item, dict):
                    continue
                text = content_item.get("text")
                if isinstance(text, str):
                    text_parts.append(text)

        if not text_parts:
            raise ProviderInvalidResponseError("OpenAI response did not contain JSON.")

        return _json_object_from_text("\n".join(text_parts))


def _json_object_from_text(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderInvalidResponseError("OpenAI response was not valid JSON.") from exc

    if not isinstance(parsed, dict):
        raise ProviderInvalidResponseError("OpenAI response JSON was not an object.")

    return parsed


class OpenAIStructuredProvider:
    def __init__(
        self,
        *,
        settings: OpenAIProviderSettings | None = None,
        client: OpenAIClientProtocol | None = None,
    ) -> None:
        self._settings = settings
        self._client = client

    async def normalize_receipt(
        self,
        *,
        gemini_result: str,
    ) -> dict[str, Any]:
        settings = self._settings or get_settings()
        api_key = settings.openai_api_key
        if not api_key:
            raise ProviderConfigurationError("OpenAI provider is not configured.")

        client = self._client or OpenAIRestClient(api_key=api_key)
        try:
            structured_result = await client.normalize_receipt(
                model=settings.openai_model,
                instructions=OPENAI_RECEIPT_NORMALIZATION_INSTRUCTIONS,
                response_format=OPENAI_RECEIPT_RESPONSE_FORMAT,
                gemini_result=gemini_result,
            )
            response = ReceiptOcrResponse.model_validate(structured_result)
        except ProviderConfigurationError:
            raise
        except ProviderInvalidResponseError:
            raise
        except ProviderExecutionError:
            raise
        except ValidationError as exc:
            raise ProviderInvalidResponseError(
                "OpenAI response did not match ReceiptOcrResponse."
            ) from exc
        except Exception as exc:
            raise ProviderExecutionError("OpenAI provider failed.") from exc

        return response.model_dump()
