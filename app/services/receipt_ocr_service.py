from app.providers.base import (
    GeminiProviderProtocol,
    OpenAIStructuredProviderProtocol,
)
from app.providers.errors import (
    GeminiProviderError,
    OpenAIProviderError,
    ProviderConfigurationError,
    ProviderError,
)
from app.schemas.ocr import ReceiptOcrResponse
from app.utils.image_validation import (
    ImageValidationSettings,
    validate_image_upload,
)

TOTAL_MISMATCH_WARNING = "合計金額と明細合計が一致しない可能性があります"


class ReceiptOcrService:
    def __init__(
        self,
        *,
        gemini_provider: GeminiProviderProtocol,
        openai_provider: OpenAIStructuredProviderProtocol,
        image_validation_settings: ImageValidationSettings | None = None,
    ) -> None:
        self._gemini_provider = gemini_provider
        self._openai_provider = openai_provider
        self._image_validation_settings = image_validation_settings

    async def extract_receipt(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        filename: str | None = None,
    ) -> ReceiptOcrResponse:
        validated_image = validate_image_upload(
            image_bytes=image_bytes,
            mime_type=mime_type,
            settings=self._image_validation_settings,
        )
        try:
            gemini_result = await self._gemini_provider.extract_receipt_text(
                image_bytes=image_bytes,
                mime_type=validated_image.mime_type,
                filename=filename,
            )
        except ProviderConfigurationError:
            raise
        except ProviderError as exc:
            raise GeminiProviderError("Gemini provider failed.") from exc

        try:
            structured_result = await self._openai_provider.normalize_receipt(
                gemini_result=gemini_result,
            )
        except ProviderConfigurationError:
            raise
        except ProviderError as exc:
            raise OpenAIProviderError("OpenAI provider failed.") from exc

        response = ReceiptOcrResponse.model_validate(structured_result)

        return self._add_total_mismatch_warning(response)

    def _add_total_mismatch_warning(
        self,
        response: ReceiptOcrResponse,
    ) -> ReceiptOcrResponse:
        if response.total_amount is None:
            return response

        known_line_totals = [
            item.line_total for item in response.items if item.line_total is not None
        ]
        if not known_line_totals:
            return response

        if sum(known_line_totals) == response.total_amount:
            return response

        if TOTAL_MISMATCH_WARNING in response.warnings:
            return response

        return response.model_copy(
            update={"warnings": [*response.warnings, TOTAL_MISMATCH_WARNING]}
        )
