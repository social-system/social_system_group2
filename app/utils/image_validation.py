from dataclasses import dataclass
from typing import Protocol

from app.config import get_settings


class ImageValidationSettings(Protocol):
    max_image_bytes: int
    allowed_image_mime_types: list[str]


class ImageValidationError(ValueError):
    code = "invalid_image"


class EmptyImageError(ImageValidationError):
    code = "empty_file"


class UnsupportedImageTypeError(ImageValidationError):
    code = "unsupported_image_type"


class ImageTooLargeError(ImageValidationError):
    code = "image_too_large"


@dataclass(frozen=True)
class ImageValidationResult:
    size_bytes: int
    mime_type: str


def validate_image_upload(
    *,
    image_bytes: bytes,
    mime_type: str,
    settings: ImageValidationSettings | None = None,
) -> ImageValidationResult:
    current_settings = settings or get_settings()
    normalized_mime_type = mime_type.strip().lower()
    image_size = len(image_bytes)

    if image_size == 0:
        raise EmptyImageError("Uploaded image is empty.")

    if normalized_mime_type not in current_settings.allowed_image_mime_types:
        raise UnsupportedImageTypeError("Unsupported image type.")

    if image_size > current_settings.max_image_bytes:
        raise ImageTooLargeError("Uploaded image exceeds maximum size.")

    return ImageValidationResult(
        size_bytes=image_size,
        mime_type=normalized_mime_type,
    )
