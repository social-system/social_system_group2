from typing import NoReturn

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import ValidationError

from app.providers.errors import ProviderError
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_structured_provider import OpenAIStructuredProvider
from app.schemas.ocr import ReceiptOcrResponse
from app.services.receipt_ocr_service import ReceiptOcrService
from app.utils.image_validation import (
    EmptyImageError,
    ImageTooLargeError,
    UnsupportedImageTypeError,
)

router = APIRouter(prefix="/ocr/receipts", tags=["ocr"])


def get_receipt_ocr_service() -> ReceiptOcrService:
    return ReceiptOcrService(
        gemini_provider=GeminiProvider(),
        openai_provider=OpenAIStructuredProvider(),
    )


def raise_http_error(
    *,
    status_code: int,
    code: str,
    message: str,
) -> NoReturn:
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
        },
    )


@router.post("/extract", response_model=ReceiptOcrResponse)
async def extract_receipt(
    file: UploadFile = File(...),
    service: ReceiptOcrService = Depends(get_receipt_ocr_service),
) -> ReceiptOcrResponse:
    try:
        image_bytes = await file.read()
        return await service.extract_receipt(
            image_bytes=image_bytes,
            mime_type=file.content_type or "",
            filename=file.filename,
        )
    except UnsupportedImageTypeError:
        raise_http_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="unsupported_image_type",
            message="Unsupported image type.",
        )
    except EmptyImageError:
        raise_http_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="empty_file",
            message="File is empty.",
        )
    except ImageTooLargeError:
        raise_http_error(
            status_code=413,
            code="image_too_large",
            message="Uploaded image is too large.",
        )
    except ProviderError:
        raise_http_error(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="ocr_provider_failed",
            message="OCR provider failed.",
        )
    except ValidationError:
        raise_http_error(
            status_code=422,
            code="structured_output_invalid",
            message="Structured OCR output is invalid.",
        )
    except Exception:
        raise_http_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_server_error",
            message="Internal server error.",
        )
