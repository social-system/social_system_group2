import pytest

from app.utils.image_validation import (
    EmptyImageError,
    ImageTooLargeError,
    UnsupportedImageTypeError,
    validate_image_upload,
)


class FakeSettings:
    def __init__(
        self,
        *,
        max_image_bytes: int,
        allowed_image_mime_types: list[str] | None = None,
    ) -> None:
        self.max_image_bytes = max_image_bytes
        self.allowed_image_mime_types = allowed_image_mime_types or [
            "image/jpeg",
            "image/png",
            "image/webp",
        ]


def test_jpeg_mime_type_passes() -> None:
    result = validate_image_upload(
        image_bytes=b"jpeg",
        mime_type="image/jpeg",
        settings=FakeSettings(max_image_bytes=10),
    )

    assert result.size_bytes == 4
    assert result.mime_type == "image/jpeg"


@pytest.mark.parametrize("mime_type", ["image/png", "image/webp"])
def test_supported_mime_types_pass(mime_type: str) -> None:
    result = validate_image_upload(
        image_bytes=b"image-bytes",
        mime_type=mime_type,
        settings=FakeSettings(max_image_bytes=20),
    )

    assert result.mime_type == mime_type


def test_unsupported_mime_type_fails() -> None:
    with pytest.raises(UnsupportedImageTypeError) as exc_info:
        validate_image_upload(
            image_bytes=b"image-bytes",
            mime_type="application/pdf",
            settings=FakeSettings(max_image_bytes=20),
        )

    assert exc_info.value.code == "unsupported_image_type"


def test_empty_file_fails() -> None:
    with pytest.raises(EmptyImageError) as exc_info:
        validate_image_upload(
            image_bytes=b"",
            mime_type="image/jpeg",
            settings=FakeSettings(max_image_bytes=20),
        )

    assert exc_info.value.code == "empty_file"


def test_oversized_file_fails() -> None:
    with pytest.raises(ImageTooLargeError) as exc_info:
        validate_image_upload(
            image_bytes=b"too-large",
            mime_type="image/jpeg",
            settings=FakeSettings(max_image_bytes=8),
        )

    assert exc_info.value.code == "image_too_large"
