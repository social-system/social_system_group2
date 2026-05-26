from decimal import Decimal

import pytest

from app.receipts.models import (
    AccountingCategory,
    Product,
    ProductAlias,
    ProductUnitConversion,
    Receipt,
)
from app.services.product_normalization import normalize_product_key


def make_product(
    db_session,
    *,
    name: str,
    unit: str = "個",
    category_id: int | None = None,
) -> Product:
    product = Product(
        name=name,
        name_key=normalize_product_key(name),
        default_base_unit=unit,
        default_category_id=category_id,
        is_inventory_target=True,
    )
    db_session.add(product)
    db_session.commit()
    return product


def make_alias(db_session, *, product: Product, alias_name: str) -> ProductAlias:
    alias = ProductAlias(
        product_id=product.id,
        alias_name=alias_name,
        alias_key=normalize_product_key(alias_name),
        source="seed",
    )
    db_session.add(alias)
    db_session.commit()
    return alias


def make_conversion(
    db_session,
    *,
    product: Product,
    from_unit: str,
    to_unit: str,
    multiplier: str,
) -> ProductUnitConversion:
    conversion = ProductUnitConversion(
        product_id=product.id,
        from_unit=from_unit,
        to_unit=to_unit,
        multiplier=Decimal(multiplier),
    )
    db_session.add(conversion)
    db_session.commit()
    return conversion


def test_prepare_receipt_converts_ocr_json_and_resolves_by_alias(client, db_session):
    category = AccountingCategory(name="食費", sort_order=1)
    db_session.add(category)
    db_session.commit()
    product = make_product(db_session, name="卵", unit="個", category_id=category.id)
    make_alias(db_session, product=product, alias_name="タマゴM 10コ")

    response = client.post(
        "/receipts/prepare",
        json={
            "status": "needs_confirmation",
            "store_name": "サンプルスーパー",
            "purchased_at": "2026-05-12",
            "total_amount": 238,
            "items": [
                {
                    "raw_name": "タマゴM 10コ",
                    "normalized_name": "たまご",
                    "category_name": "食費",
                    "purchased_quantity": 1,
                    "purchased_unit": "パック",
                    "base_quantity": 10,
                    "base_unit": "個",
                    "unit_price": 238,
                    "line_total": 238,
                    "is_inventory_target": True,
                    "confidence": 0.82,
                    "warnings": ["OCR item warning"],
                }
            ],
            "warnings": ["OCR warning"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["receipt"] == {
        "store_name": "サンプルスーパー",
        "purchased_at": 20260512,
        "total_amount": 238,
        "items": [
            {
                "raw_name": "タマゴM 10コ",
                "normalized_name": "卵",
                "product_id": product.id,
                "category_id": category.id,
                "purchased_quantity": "1.00",
                "purchased_unit": "パック",
                "base_quantity": "10.00",
                "base_unit": "個",
                "unit_price": 238,
                "line_total": 238,
                "is_inventory_target": True,
            }
        ],
    }
    assert body["item_resolutions"] == [
        {
            "index": 0,
            "resolution_status": "resolved",
            "resolution_source": "raw_name_alias",
            "product_id": product.id,
            "product_name": "卵",
            "product_candidates": [],
            "issues": [],
        }
    ]
    assert body["unresolved_items"] == []
    assert body["warnings"] == ["OCR warning"]
    assert body["validation_issues"] == []
    assert "status" not in body["receipt"]
    assert "confidence" not in body["receipt"]["items"][0]
    assert "warnings" not in body["receipt"]["items"][0]


def test_prepare_receipt_resolves_by_product_name_key(client, db_session):
    product = make_product(db_session, name="卵", unit="個")

    response = client.post(
        "/receipts/prepare",
        json={
            "store_name": "sample store",
            "purchased_at": 20260512,
            "total_amount": 100,
            "items": [
                {
                    "raw_name": "unknown",
                    "normalized_name": " 卵 ",
                    "purchased_quantity": 1,
                    "line_total": 100,
                    "is_inventory_target": True,
                    "base_quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 200
    item = response.json()["receipt"]["items"][0]
    assert item["product_id"] == product.id
    assert item["normalized_name"] == "卵"
    assert item["base_unit"] == "個"
    resolution = response.json()["item_resolutions"][0]
    assert resolution["resolution_status"] == "resolved"
    assert resolution["resolution_source"] == "normalized_name_product"


def test_prepare_receipt_returns_candidates_for_unresolved_item(client, db_session):
    product = make_product(db_session, name="味噌", unit="g")

    response = client.post(
        "/receipts/prepare",
        json={
            "store_name": "sample store",
            "purchased_at": 20260512,
            "total_amount": 198,
            "items": [
                {
                    "raw_name": "味噌10個",
                    "normalized_name": "ミソ",
                    "purchased_quantity": 1,
                    "purchased_unit": "個",
                    "base_quantity": None,
                    "base_unit": None,
                    "unit_price": 198,
                    "line_total": 198,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    item = body["receipt"]["items"][0]
    assert item["product_id"] is None
    assert item["normalized_name"] == "ミソ"
    resolution = body["item_resolutions"][0]
    assert resolution["resolution_status"] == "unresolved"
    assert resolution["resolution_source"] == "candidate_only"
    assert resolution["product_candidates"][0]["product_id"] == product.id
    assert resolution["product_candidates"][0]["name"] == "味噌"
    assert body["unresolved_items"] == [resolution]
    assert "product_not_resolved" in resolution["issues"]
    assert "inventory_target_without_base_quantity" in resolution["issues"]
    assert "inventory_target_without_base_unit" in resolution["issues"]


def test_prepare_receipt_does_not_register_normalized_name_as_alias(client, db_session):
    product = make_product(db_session, name="たまご", unit="個")

    response = client.post(
        "/receipts/prepare",
        json={
            "store_name": "sample store",
            "purchased_at": 20260512,
            "total_amount": 238,
            "items": [
                {
                    "raw_name": "不明なOCR名",
                    "normalized_name": "タマゴM 10コ",
                    "purchased_quantity": 1,
                    "purchased_unit": "パック",
                    "base_quantity": None,
                    "base_unit": None,
                    "unit_price": 238,
                    "line_total": 238,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert response.status_code == 200
    assert db_session.query(ProductAlias).count() == 0
    body = response.json()
    resolution = body["item_resolutions"][0]
    assert resolution["resolution_status"] == "unresolved"
    assert resolution["product_candidates"][0]["product_id"] == product.id


def test_prepare_receipt_fills_default_base_unit_after_product_resolution(client, db_session):
    product = make_product(db_session, name="牛乳", unit="ml")

    response = client.post(
        "/receipts/prepare",
        json={
            "purchased_at": 20260512,
            "total_amount": 198,
            "items": [
                {
                    "raw_name": "牛乳",
                    "normalized_name": "牛乳",
                    "purchased_quantity": 1,
                    "purchased_unit": "本",
                    "line_total": 198,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert response.status_code == 200
    item = response.json()["receipt"]["items"][0]
    assert item["product_id"] == product.id
    assert item["base_unit"] == "ml"
    assert item["base_quantity"] is None


def test_prepare_receipt_fills_base_quantity_when_units_match(client, db_session):
    make_product(db_session, name="水", unit="ml")

    response = client.post(
        "/receipts/prepare",
        json={
            "purchased_at": 20260512,
            "total_amount": 100,
            "items": [
                {
                    "raw_name": "水",
                    "normalized_name": "水",
                    "purchased_quantity": 1000,
                    "purchased_unit": " ｍｌ ",
                    "line_total": 100,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert response.status_code == 200
    item = response.json()["receipt"]["items"][0]
    assert item["base_unit"] == "ml"
    assert item["base_quantity"] == "1000.00"


@pytest.mark.parametrize(
    (
        "product_name",
        "default_base_unit",
        "raw_name",
        "purchased_quantity",
        "purchased_unit",
        "conversion_from_unit",
        "conversion_to_unit",
        "multiplier",
        "expected_base_quantity",
    ),
    [
        ("卵", "個", "卵 1パック", 1, "パック", "パック", "個", "10", "10.00"),
        ("牛乳", "ml", "牛乳 1本", 1, "本", "本", "ml", "1000", "1000.00"),
        ("米", "g", "米 1kg", 1, "kg", "kg", "g", "1000", "1000.00"),
    ],
)
def test_prepare_receipt_fills_base_quantity_from_product_unit_conversion(
    client,
    db_session,
    product_name,
    default_base_unit,
    raw_name,
    purchased_quantity,
    purchased_unit,
    conversion_from_unit,
    conversion_to_unit,
    multiplier,
    expected_base_quantity,
):
    product = make_product(db_session, name=product_name, unit=default_base_unit)
    make_alias(db_session, product=product, alias_name=raw_name)
    make_conversion(
        db_session,
        product=product,
        from_unit=conversion_from_unit,
        to_unit=conversion_to_unit,
        multiplier=multiplier,
    )

    response = client.post(
        "/receipts/prepare",
        json={
            "purchased_at": 20260512,
            "total_amount": 100,
            "items": [
                {
                    "raw_name": raw_name,
                    "normalized_name": product_name,
                    "purchased_quantity": purchased_quantity,
                    "purchased_unit": purchased_unit,
                    "line_total": 100,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert response.status_code == 200
    item = response.json()["receipt"]["items"][0]
    assert item["product_id"] == product.id
    assert item["base_unit"] == default_base_unit
    assert item["base_quantity"] == expected_base_quantity


@pytest.mark.parametrize(
    ("product_name", "raw_name", "purchased_quantity", "purchased_unit"),
    [
        ("トマト", "トマト 2個", 2, "個"),
        ("肉", "肉 1パック", 1, "パック"),
    ],
)
def test_prepare_receipt_does_not_guess_base_quantity_without_conversion(
    client,
    db_session,
    product_name,
    raw_name,
    purchased_quantity,
    purchased_unit,
):
    product = make_product(db_session, name=product_name, unit="g")
    make_alias(db_session, product=product, alias_name=raw_name)

    response = client.post(
        "/receipts/prepare",
        json={
            "purchased_at": 20260512,
            "total_amount": 100,
            "items": [
                {
                    "raw_name": raw_name,
                    "normalized_name": product_name,
                    "purchased_quantity": purchased_quantity,
                    "purchased_unit": purchased_unit,
                    "line_total": 100,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert response.status_code == 200
    item = response.json()["receipt"]["items"][0]
    assert item["product_id"] == product.id
    assert item["base_unit"] == "g"
    assert item["base_quantity"] is None


def test_prepare_receipt_reports_unit_conversion_missing(client, db_session):
    product = make_product(db_session, name="米", unit="g")
    make_alias(db_session, product=product, alias_name="米 1kg")

    response = client.post(
        "/receipts/prepare",
        json={
            "purchased_at": 20260512,
            "total_amount": 100,
            "items": [
                {
                    "raw_name": "米 1kg",
                    "normalized_name": "米",
                    "purchased_quantity": 1,
                    "purchased_unit": "kg",
                    "line_total": 100,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    resolution = body["item_resolutions"][0]
    assert "unit_conversion_missing" in resolution["issues"]
    assert "base_quantity_missing" in resolution["issues"]
    assert "inventory_target_without_base_quantity" in resolution["issues"]
    assert "inventory_items_require_quantity_confirmation" in body["validation_issues"]
    assert body["unresolved_items"] == [resolution]


def test_prepare_receipt_reports_ambiguous_quantity_for_item_unit_without_conversion(
    client,
    db_session,
):
    product = make_product(db_session, name="トマト", unit="g")
    make_alias(db_session, product=product, alias_name="トマト 2個")

    response = client.post(
        "/receipts/prepare",
        json={
            "purchased_at": 20260512,
            "total_amount": 100,
            "items": [
                {
                    "raw_name": "トマト 2個",
                    "normalized_name": "トマト",
                    "purchased_quantity": 2,
                    "purchased_unit": "個",
                    "line_total": 100,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert response.status_code == 200
    resolution = response.json()["item_resolutions"][0]
    assert "ambiguous_quantity" in resolution["issues"]
    assert "unit_conversion_missing" in resolution["issues"]


def test_prepare_receipt_reports_base_unit_missing(client):
    response = client.post(
        "/receipts/prepare",
        json={
            "purchased_at": 20260512,
            "total_amount": 100,
            "items": [
                {
                    "raw_name": "unknown",
                    "normalized_name": None,
                    "purchased_quantity": 1,
                    "purchased_unit": "個",
                    "line_total": 100,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert response.status_code == 200
    resolution = response.json()["item_resolutions"][0]
    assert "base_unit_missing" in resolution["issues"]
    assert "inventory_target_without_base_unit" in resolution["issues"]


def test_prepare_receipt_reports_ambiguous_quantity_when_purchase_unit_missing(
    client,
    db_session,
):
    make_product(db_session, name="卵", unit="個")

    response = client.post(
        "/receipts/prepare",
        json={
            "purchased_at": 20260512,
            "total_amount": 100,
            "items": [
                {
                    "raw_name": "卵",
                    "normalized_name": "卵",
                    "purchased_quantity": 1,
                    "purchased_unit": None,
                    "line_total": 100,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert response.status_code == 200
    resolution = response.json()["item_resolutions"][0]
    assert "ambiguous_quantity" in resolution["issues"]
    assert "base_quantity_missing" in resolution["issues"]


def test_prepare_receipt_does_not_add_quantity_issues_for_non_inventory_item(client):
    response = client.post(
        "/receipts/prepare",
        json={
            "purchased_at": 20260512,
            "total_amount": 100,
            "items": [
                {
                    "raw_name": "割引",
                    "normalized_name": None,
                    "purchased_quantity": None,
                    "purchased_unit": None,
                    "line_total": 100,
                    "is_inventory_target": False,
                }
            ],
        },
    )

    assert response.status_code == 200
    issues = response.json()["item_resolutions"][0]["issues"]
    assert "unit_conversion_missing" not in issues
    assert "ambiguous_quantity" not in issues
    assert "base_quantity_missing" not in issues
    assert "base_unit_missing" not in issues


def test_prepare_receipt_does_not_overwrite_existing_base_quantity(client, db_session):
    product = make_product(db_session, name="卵", unit="個")
    make_alias(db_session, product=product, alias_name="卵 1パック")
    make_conversion(
        db_session,
        product=product,
        from_unit="パック",
        to_unit="個",
        multiplier="10",
    )

    response = client.post(
        "/receipts/prepare",
        json={
            "purchased_at": 20260512,
            "total_amount": 100,
            "items": [
                {
                    "raw_name": "卵 1パック",
                    "normalized_name": "卵",
                    "purchased_quantity": 1,
                    "purchased_unit": "パック",
                    "base_quantity": 6,
                    "line_total": 100,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert response.status_code == 200
    item = response.json()["receipt"]["items"][0]
    assert item["base_unit"] == "個"
    assert item["base_quantity"] == "6.00"


def test_prepare_receipt_does_not_convert_when_product_unresolved(client, db_session):
    product = make_product(db_session, name="卵", unit="個")
    make_conversion(
        db_session,
        product=product,
        from_unit="パック",
        to_unit="個",
        multiplier="10",
    )

    response = client.post(
        "/receipts/prepare",
        json={
            "purchased_at": 20260512,
            "total_amount": 100,
            "items": [
                {
                    "raw_name": "unknown",
                    "normalized_name": None,
                    "purchased_quantity": 1,
                    "purchased_unit": "パック",
                    "line_total": 100,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert response.status_code == 200
    item = response.json()["receipt"]["items"][0]
    assert item["product_id"] is None
    assert item["base_unit"] is None
    assert item["base_quantity"] is None


def test_user_confirmed_base_quantity_and_unit_can_be_saved(client, db_session):
    product = make_product(db_session, name="トマト", unit="g")

    create_response = client.post(
        "/receipts",
        json={
            "purchased_at": 20260512,
            "store_name": "sample store",
            "total_amount": 198,
            "items": [
                {
                    "raw_name": "トマト 2個",
                    "normalized_name": "トマト",
                    "product_id": product.id,
                    "category_id": None,
                    "purchased_quantity": 2,
                    "purchased_unit": "個",
                    "base_quantity": 300,
                    "base_unit": "g",
                    "unit_price": 198,
                    "line_total": 198,
                    "is_inventory_target": True,
                }
            ],
        },
    )

    assert create_response.status_code == 201
    receipt_id = create_response.json()["id"]
    get_response = client.get(f"/receipts/{receipt_id}")

    assert get_response.status_code == 200
    item = get_response.json()["items"][0]
    assert item["product_id"] == product.id
    assert item["base_quantity"] == "300.00"
    assert item["base_unit"] == "g"


def test_prepare_receipt_reports_invalid_date_as_validation_issue(client):
    response = client.post(
        "/receipts/prepare",
        json={
            "store_name": "sample store",
            "purchased_at": "2026-02-30",
            "total_amount": 100,
            "items": [],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["receipt"]["purchased_at"] is None
    assert "purchased_at_invalid" in body["validation_issues"]
    assert "items_empty" in body["validation_issues"]


def test_prepare_receipt_does_not_save_receipt(client, db_session):
    assert db_session.query(Receipt).count() == 0

    response = client.post(
        "/receipts/prepare",
        json={
            "store_name": "sample store",
            "purchased_at": 20260512,
            "total_amount": 100,
            "items": [
                {
                    "raw_name": "unknown",
                    "normalized_name": "unknown",
                    "purchased_quantity": 1,
                    "line_total": 100,
                    "is_inventory_target": False,
                }
            ],
        },
    )

    assert response.status_code == 200
    assert db_session.query(Receipt).count() == 0
