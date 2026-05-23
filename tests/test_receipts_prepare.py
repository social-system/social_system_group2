from app.receipts.models import AccountingCategory, Product, ProductAlias, Receipt
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
