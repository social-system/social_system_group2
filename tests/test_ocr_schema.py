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


def test_receipt_ocr_response_keeps_normalized_name_as_candidate() -> None:
    response = ReceiptOcrResponse(
        status="needs_confirmation",
        store_name="Sample Store",
        purchased_at="2026-05-12",
        total_amount=238,
        items=[
            ReceiptOcrItem(
                raw_name="タマゴM 10コ",
                normalized_name="たまご",
                category_name="食費",
                purchased_quantity=1,
                purchased_unit="パック",
                base_quantity=10,
                base_unit="個",
                unit_price=238,
                line_total=238,
                is_inventory_target=True,
                confidence=0.82,
                warnings=[],
            )
        ],
        warnings=[],
    )

    dumped = response.model_dump()
    assert dumped["items"][0]["normalized_name"] == "たまご"
    assert "product_id" not in dumped["items"][0]
    assert "category_id" not in dumped["items"][0]


def test_receipt_ocr_item_accepts_auto_registration_metadata() -> None:
    item = ReceiptOcrItem(
        raw_name="タマゴM 10コ",
        normalized_name="卵",
        confidence=0.9,
        ocr_metadata={
            "field_confidence": {
                "raw_name": 0.95,
                "normalized_name": 0.88,
            },
            "auto_register_candidate": False,
            "needs_review_reasons": ["base quantity requires review"],
        },
    )

    assert item.ocr_metadata.field_confidence.raw_name == 0.95
    assert item.ocr_metadata.auto_register_candidate is False
    assert item.ocr_metadata.needs_review_reasons == [
        "base quantity requires review"
    ]


def test_invalid_field_confidence_fails() -> None:
    with pytest.raises(ValidationError):
        ReceiptOcrItem(
            ocr_metadata={
                "field_confidence": {"raw_name": 1.1},
                "auto_register_candidate": None,
                "needs_review_reasons": [],
            }
        )


@pytest.mark.parametrize("forbidden_field", ["product_id", "category_id"])
def test_database_ids_are_rejected_from_item_schema(forbidden_field: str) -> None:
    data = {
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
        forbidden_field: 1,
    }

    with pytest.raises(ValidationError):
        ReceiptOcrItem.model_validate(data)


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
