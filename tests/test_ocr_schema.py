import pytest
from pydantic import ValidationError

from app.schemas.ocr import ReceiptOcrItem, ReceiptOcrResponse


def test_receipt_ocr_response_accepts_null_fields() -> None:
    response = ReceiptOcrResponse(
        status="needs_confirmation",
        store_name=None,
        purchased_at=None,
        total_amount=None,
        items=[
            ReceiptOcrItem(
                raw_name=None,
                normalized_name=None,
                category_name=None,
                purchased_quantity=None,
                purchased_unit=None,
                base_quantity=None,
                base_unit=None,
                unit_price=None,
                line_total=None,
                is_inventory_target=None,
                confidence=None,
                warnings=[],
            )
        ],
        warnings=[],
    )

    assert response.status == "needs_confirmation"
    assert response.store_name is None
    assert response.purchased_at is None
    assert response.total_amount is None
    assert response.items[0].warnings == []
    assert response.warnings == []


def test_receipt_ocr_response_accepts_store_name() -> None:
    response = ReceiptOcrResponse(
        status="needs_confirmation",
        store_name="Sample Store",
        purchased_at="2026-05-12",
        total_amount=636,
        items=[],
        warnings=[],
    )

    assert response.store_name == "Sample Store"


def test_invalid_status_fails() -> None:
    with pytest.raises(ValidationError):
        ReceiptOcrResponse(status="confirmed")


def test_invalid_date_format_fails() -> None:
    with pytest.raises(ValidationError):
        ReceiptOcrResponse(purchased_at="2026/05/12")


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("total_amount", -1),
    ],
)
def test_negative_response_amount_fails(field_name: str, value: int) -> None:
    with pytest.raises(ValidationError):
        ReceiptOcrResponse(**{field_name: value})


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("unit_price", -1),
        ("line_total", -1),
    ],
)
def test_negative_item_amount_fails(field_name: str, value: int) -> None:
    with pytest.raises(ValidationError):
        ReceiptOcrItem(**{field_name: value})


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("purchased_quantity", 0),
        ("base_quantity", 0),
    ],
)
def test_non_positive_quantities_fail(field_name: str, value: int) -> None:
    with pytest.raises(ValidationError):
        ReceiptOcrItem(**{field_name: value})


def test_invalid_confidence_fails() -> None:
    with pytest.raises(ValidationError):
        ReceiptOcrItem(confidence=1.1)


def test_valid_boundaries_pass() -> None:
    item = ReceiptOcrItem(
        purchased_quantity=1,
        base_quantity=1,
        unit_price=0,
        line_total=0,
        confidence=1,
    )
    response = ReceiptOcrResponse(
        purchased_at="2026-05-12",
        total_amount=0,
        items=[item],
    )

    assert response.items[0].confidence == 1
