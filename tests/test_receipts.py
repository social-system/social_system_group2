from app.receipts.models import AccountingCategory, Product


def make_receipt_payload(
    *,
    purchased_at: int = 20260428,
    store_name: str | None = "sample store",
    total_amount: int = 500,
    raw_name: str = "milk",
    normalized_name: str | None = "milk",
    line_total: int | None = None,
    is_inventory_target: bool = True,
    base_quantity: int | None = 1000,
    base_unit: str | None = "ml",
    category_id: int | None = None,
    product_id: int | None = None,
) -> dict:
    if line_total is None:
        line_total = total_amount

    return {
        "purchased_at": purchased_at,
        "store_name": store_name,
        "total_amount": total_amount,
        "items": [
            {
                "raw_name": raw_name,
                "normalized_name": normalized_name,
                "product_id": product_id,
                "category_id": category_id,
                "purchased_quantity": 1,
                "purchased_unit": "本",
                "base_quantity": base_quantity,
                "base_unit": base_unit,
                "unit_price": line_total,
                "line_total": line_total,
                "is_inventory_target": is_inventory_target,
            }
        ],
    }


def create_receipt(client, **kwargs) -> dict:
    response = client.post("/receipts", json=make_receipt_payload(**kwargs))
    assert response.status_code == 201
    return response.json()


def test_create_receipt(client):
    response = client.post("/receipts", json=make_receipt_payload())

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "id": body["id"],
        "purchased_at": 20260428,
        "store_name": "sample store",
        "total_amount": 500,
        "items_total": 500,
        "adjustment_amount": 0,
        "item_count": 1,
    }


def test_create_receipt_allows_total_amount_and_items_total_mismatch(client):
    response = client.post(
        "/receipts",
        json=make_receipt_payload(total_amount=450, line_total=500),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["total_amount"] == 450
    assert body["items_total"] == 500
    assert body["adjustment_amount"] == -50


def test_create_receipt_rejects_empty_items(client):
    payload = make_receipt_payload()
    payload["items"] = []

    response = client.post("/receipts", json=payload)

    assert response.status_code == 422


def test_create_receipt_rejects_invalid_date(client):
    response = client.post(
        "/receipts",
        json=make_receipt_payload(purchased_at=20260230),
    )

    assert response.status_code == 422


def test_create_receipt_rejects_blank_normalized_name_for_inventory_target(client):
    response = client.post(
        "/receipts",
        json=make_receipt_payload(normalized_name=""),
    )

    assert response.status_code == 422


def test_create_receipt_rejects_missing_base_quantity_for_inventory_target(client):
    response = client.post(
        "/receipts",
        json=make_receipt_payload(base_quantity=None),
    )

    assert response.status_code == 422


def test_create_receipt_rejects_missing_product_id(client):
    response = client.post(
        "/receipts",
        json=make_receipt_payload(product_id=999),
    )

    assert response.status_code == 400


def test_create_receipt_rejects_missing_category_id(client):
    response = client.post(
        "/receipts",
        json=make_receipt_payload(category_id=999),
    )

    assert response.status_code == 400


def test_get_receipt(client):
    created = create_receipt(client, total_amount=700, raw_name="bread")

    response = client.get(f"/receipts/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "id": created["id"],
        "purchased_at": 20260428,
        "store_name": "sample store",
        "total_amount": 700,
        "items_total": 700,
        "adjustment_amount": 0,
        "items": [
            {
                "id": body["items"][0]["id"],
                "raw_name": "bread",
                "normalized_name": "milk",
                "product_id": None,
                "category_id": None,
                "purchased_quantity": "1.00",
                "purchased_unit": "本",
                "base_quantity": "1000.00",
                "base_unit": "ml",
                "unit_price": 700,
                "line_total": 700,
                "is_inventory_target": True,
            }
        ],
    }


def test_get_receipt_returns_404_for_missing_id(client):
    response = client.get("/receipts/999")

    assert response.status_code == 404


def test_list_receipts(client):
    first = create_receipt(client, total_amount=100, raw_name="milk")
    second = create_receipt(client, total_amount=200, raw_name="bread")

    response = client.get("/receipts")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": first["id"],
            "purchased_at": 20260428,
            "store_name": "sample store",
            "total_amount": 100,
            "items_total": 100,
            "adjustment_amount": 0,
            "item_count": 1,
        },
        {
            "id": second["id"],
            "purchased_at": 20260428,
            "store_name": "sample store",
            "total_amount": 200,
            "items_total": 200,
            "adjustment_amount": 0,
            "item_count": 1,
        },
    ]


def test_list_receipts_uses_skip_and_limit(client):
    create_receipt(client, total_amount=100, raw_name="milk")
    second = create_receipt(client, total_amount=200, raw_name="bread")
    create_receipt(client, total_amount=300, raw_name="eggs")

    response = client.get("/receipts?skip=1&limit=1")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == second["id"]


def test_list_receipts_uses_date_filter(client):
    create_receipt(client, total_amount=100, purchased_at=20260401, raw_name="milk")
    matched = create_receipt(
        client,
        total_amount=200,
        purchased_at=20260415,
        raw_name="bread",
    )
    create_receipt(client, total_amount=300, purchased_at=20260501, raw_name="eggs")

    response = client.get("/receipts?date_from=20260410&date_to=20260430")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == matched["id"]
    assert body[0]["purchased_at"] == 20260415


def test_list_receipts_uses_category_filter(client, db_session):
    category = AccountingCategory(name="food", sort_order=1)
    db_session.add(category)
    db_session.commit()

    matched = create_receipt(
        client,
        total_amount=100,
        raw_name="milk",
        category_id=category.id,
    )
    create_receipt(client, total_amount=200, raw_name="soap", is_inventory_target=False)

    response = client.get(f"/receipts?category_id={category.id}")

    assert response.status_code == 200
    assert response.json() == [matched]


def test_list_receipts_uses_inventory_only_filter(client):
    matched = create_receipt(client, total_amount=100, raw_name="milk")
    create_receipt(
        client,
        total_amount=200,
        raw_name="soap",
        normalized_name=None,
        is_inventory_target=False,
        base_quantity=None,
        base_unit=None,
    )

    response = client.get("/receipts?inventory_only=true")

    assert response.status_code == 200
    assert response.json() == [matched]


def test_create_receipt_accepts_existing_product_and_category(client, db_session):
    category = AccountingCategory(name="food", sort_order=1)
    db_session.add(category)
    db_session.flush()
    product = Product(
        name="milk",
        name_key="milk",
        default_base_unit="ml",
        default_category_id=category.id,
        is_inventory_target=True,
    )
    db_session.add(product)
    db_session.commit()

    response = client.post(
        "/receipts",
        json=make_receipt_payload(product_id=product.id, category_id=category.id),
    )

    assert response.status_code == 201
    detail_response = client.get(f"/receipts/{response.json()['id']}")
    assert detail_response.status_code == 200
    item = detail_response.json()["items"][0]
    assert item["product_id"] == product.id
    assert item["category_id"] == category.id


def test_delete_receipt(client):
    created = create_receipt(client)

    response = client.delete(f"/receipts/{created['id']}")

    assert response.status_code == 200
    assert response.json() == {"deleted": True, "id": created["id"]}

    get_response = client.get(f"/receipts/{created['id']}")
    assert get_response.status_code == 404


def test_delete_receipt_returns_404_for_missing_id(client):
    response = client.delete("/receipts/999")

    assert response.status_code == 404
