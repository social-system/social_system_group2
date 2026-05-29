from datetime import date

from app.common.date import format_yyyymmdd
from app.receipts.models import AccountingCategory, Product, Receipt
from app.services.product_normalization import normalize_product_key


def make_category(db_session, *, name: str = "食費") -> AccountingCategory:
    category = AccountingCategory(name=name, sort_order=1)
    db_session.add(category)
    db_session.commit()
    return category


def make_product(
    db_session,
    *,
    name: str,
    unit: str,
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


def make_ocr_payload(
    *,
    store_name: str,
    raw_name: str = "タマゴM 10コ",
    normalized_name: str = "たまご",
    purchased_at: str | None = None,
    total_amount: int = 238,
    line_total: int = 238,
    base_quantity: int = 10,
    base_unit: str = "個",
) -> dict:
    return {
        "status": "needs_confirmation",
        "store_name": store_name,
        "purchased_at": purchased_at or date.today().isoformat(),
        "total_amount": total_amount,
        "items": [
            {
                "raw_name": raw_name,
                "normalized_name": normalized_name,
                "category_name": "食費",
                "purchased_quantity": 1,
                "purchased_unit": "パック",
                "base_quantity": base_quantity,
                "base_unit": base_unit,
                "unit_price": line_total,
                "line_total": line_total,
                "is_inventory_target": True,
                "confidence": 0.82,
                "warnings": ["OCR item warning"],
            }
        ],
        "warnings": ["OCR warning"],
    }


def make_auto_create_payload(**overrides) -> dict:
    payload = make_ocr_payload(
        store_name=overrides.pop("store_name", "自動登録スーパー"),
        **overrides,
    )
    payload["auto_register_enabled"] = True
    payload["warnings"] = []
    payload["items"][0]["warnings"] = []
    payload["items"][0]["confidence"] = 0.95
    payload["items"][0]["ocr_metadata"] = {
        "field_confidence": {
            "raw_name": 0.98,
            "line_total": 0.97,
            "purchased_quantity": 0.95,
        },
        "auto_register_candidate": True,
        "needs_review_reasons": [],
    }
    return payload


def prepare_and_create_receipt(client, payload: dict) -> tuple[dict, dict]:
    prepare_response = client.post("/receipts/prepare", json=payload)
    assert prepare_response.status_code == 200
    prepared = prepare_response.json()

    create_response = client.post("/receipts", json=prepared["receipt"])
    assert create_response.status_code == 201

    return prepared, create_response.json()


def test_ocr_json_prepare_create_and_cheapest_flow(client, db_session):
    category = make_category(db_session)
    product = make_product(
        db_session,
        name="卵",
        unit="個",
        category_id=category.id,
    )
    alias_response = client.post(
        "/product-aliases",
        json={
            "alias_name": "タマゴM 10コ",
            "product_id": product.id,
            "source": "user_confirmed",
        },
    )
    assert alias_response.status_code == 200

    _prepared_expensive, expensive_receipt = prepare_and_create_receipt(
        client,
        make_ocr_payload(
            store_name="少量店",
            total_amount=180,
            line_total=180,
            base_quantity=6,
        ),
    )
    prepared_cheaper, cheaper_receipt = prepare_and_create_receipt(
        client,
        make_ocr_payload(
            store_name="サンプルスーパー",
            total_amount=238,
            line_total=238,
            base_quantity=10,
        ),
    )

    assert prepared_cheaper["receipt"]["purchased_at"] == format_yyyymmdd(date.today())
    assert prepared_cheaper["receipt"]["store_name"] == "サンプルスーパー"
    assert prepared_cheaper["receipt"]["items"][0]["product_id"] == product.id
    assert prepared_cheaper["receipt"]["items"][0]["normalized_name"] == "卵"
    assert prepared_cheaper["receipt"]["items"][0]["category_id"] == category.id
    assert prepared_cheaper["item_resolutions"][0]["resolution_status"] == "resolved"
    assert prepared_cheaper["item_resolutions"][0]["resolution_source"] == "raw_name_alias"
    assert prepared_cheaper["unresolved_items"] == []
    assert "status" not in prepared_cheaper["receipt"]
    assert "warnings" not in prepared_cheaper["receipt"]["items"][0]
    assert "confidence" not in prepared_cheaper["receipt"]["items"][0]

    expensive_detail = client.get(f"/receipts/{expensive_receipt['id']}").json()
    cheaper_detail = client.get(f"/receipts/{cheaper_receipt['id']}").json()
    assert expensive_detail["items"][0]["product_id"] == product.id
    assert cheaper_detail["items"][0]["product_id"] == product.id

    cheapest_response = client.get(f"/prices/cheapest?product_id={product.id}")

    assert cheapest_response.status_code == 200
    cheapest = cheapest_response.json()["cheapest"]
    assert cheapest["store_name"] == "サンプルスーパー"
    assert cheapest["price_per_base_unit"] == 23.8
    assert cheapest["line_total"] == 238
    assert cheapest["base_quantity"] == "10.00"


def test_unresolved_item_create_assigns_new_product_then_alias_learning(client, db_session):
    make_category(db_session)
    product = make_product(db_session, name="味噌", unit="g")

    unresolved_payload = make_ocr_payload(
        store_name="未解決スーパー",
        raw_name="ミソ特売",
        normalized_name="ミソ",
        total_amount=198,
        line_total=198,
        base_quantity=500,
        base_unit="g",
    )

    first_prepare, first_receipt = prepare_and_create_receipt(client, unresolved_payload)

    assert first_prepare["receipt"]["items"][0]["product_id"] is None
    assert first_prepare["item_resolutions"][0]["resolution_status"] == "unresolved"
    assert first_prepare["unresolved_items"] == [first_prepare["item_resolutions"][0]]

    first_detail = client.get(f"/receipts/{first_receipt['id']}").json()
    created_product_id = first_detail["items"][0]["product_id"]
    assert created_product_id is not None
    assert created_product_id != product.id

    no_price_response = client.get(f"/prices/cheapest?product_id={product.id}")
    assert no_price_response.status_code == 200
    assert no_price_response.json()["cheapest"] is None

    alias_response = client.post(
        "/product-aliases",
        json={
            "alias_name": "ミソ",
            "product_id": product.id,
            "source": "user_confirmed",
        },
    )
    assert alias_response.status_code == 200

    second_prepare = client.post("/receipts/prepare", json=unresolved_payload)

    assert second_prepare.status_code == 200
    body = second_prepare.json()
    assert body["receipt"]["items"][0]["product_id"] == product.id
    assert body["receipt"]["items"][0]["normalized_name"] == "味噌"
    assert body["item_resolutions"][0]["resolution_status"] == "resolved"
    assert body["item_resolutions"][0]["resolution_source"] == "normalized_name_alias"
    assert body["unresolved_items"] == []


def test_auto_create_creates_receipt_when_ocr_payload_is_safe(client, db_session):
    category = make_category(db_session)
    product = make_product(
        db_session,
        name="卵",
        unit="個",
        category_id=category.id,
    )
    alias_response = client.post(
        "/product-aliases",
        json={
            "alias_name": "タマゴM 10コ",
            "product_id": product.id,
            "source": "user_confirmed",
        },
    )
    assert alias_response.status_code == 200

    response = client.post("/receipts/auto-create", json=make_auto_create_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["created"] is True
    assert body["receipt_id"] == body["summary"]["id"]
    assert body["auto_registration"] == {
        "eligible": True,
        "reasons": [],
        "min_item_confidence": 0.85,
    }
    assert body["receipt"]["items"][0]["product_id"] == product.id

    receipt = db_session.get(Receipt, body["receipt_id"])
    assert receipt is not None
    assert receipt.source == "ocr_auto_registered"


def test_auto_create_rejects_low_confidence_without_saving(client, db_session):
    product = make_product(db_session, name="卵", unit="個")
    alias_response = client.post(
        "/product-aliases",
        json={
            "alias_name": "タマゴM 10コ",
            "product_id": product.id,
            "source": "user_confirmed",
        },
    )
    assert alias_response.status_code == 200
    payload = make_auto_create_payload()
    payload["items"][0]["confidence"] = 0.5

    response = client.post("/receipts/auto-create", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] is False
    assert body["receipt_id"] is None
    assert "item_0_confidence_below_threshold" in body["auto_registration"]["reasons"]
    assert db_session.query(Receipt).count() == 0


def test_auto_create_rejects_metadata_review_reason_without_saving(client, db_session):
    product = make_product(db_session, name="卵", unit="個")
    alias_response = client.post(
        "/product-aliases",
        json={
            "alias_name": "タマゴM 10コ",
            "product_id": product.id,
            "source": "user_confirmed",
        },
    )
    assert alias_response.status_code == 200
    payload = make_auto_create_payload()
    payload["items"][0]["ocr_metadata"]["auto_register_candidate"] = False
    payload["items"][0]["ocr_metadata"]["needs_review_reasons"] = [
        "base quantity requires review"
    ]

    response = client.post("/receipts/auto-create", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] is False
    assert "item_0_metadata_blocks_auto_registration" in (
        body["auto_registration"]["reasons"]
    )
    assert "item_0_needs_review:base quantity requires review" in (
        body["auto_registration"]["reasons"]
    )
    assert db_session.query(Receipt).count() == 0


def test_auto_create_respects_frontend_disabled_flag(client, db_session):
    product = make_product(db_session, name="卵", unit="個")
    alias_response = client.post(
        "/product-aliases",
        json={
            "alias_name": "タマゴM 10コ",
            "product_id": product.id,
            "source": "user_confirmed",
        },
    )
    assert alias_response.status_code == 200
    payload = make_auto_create_payload()
    payload["auto_register_enabled"] = False

    response = client.post("/receipts/auto-create", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] is False
    assert body["receipt_id"] is None
    assert body["receipt"]["items"][0]["product_id"] == product.id
    assert "auto_registration_disabled" in body["auto_registration"]["reasons"]
    assert db_session.query(Receipt).count() == 0
