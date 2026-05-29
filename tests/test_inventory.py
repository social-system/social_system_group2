from datetime import date
from decimal import Decimal

from app.inventory.models import InventoryBatch, InventoryMovement, InventoryOperation
from app.receipts.models import Product, Receipt, ReceiptItem


def create_product(db_session, *, name: str = "eggs", unit: str = "pcs") -> Product:
    product = Product(
        name=name,
        name_key=name,
        default_base_unit=unit,
        is_inventory_target=True,
    )
    db_session.add(product)
    db_session.commit()
    return product


def create_receipt_with_items(db_session, items: list[dict], *, purchased_at: date | None = None) -> Receipt:
    receipt = Receipt(
        purchased_at=purchased_at or date(2026, 5, 12),
        store_name="sample store",
        total_amount=1000,
        items_total=1000,
        adjustment_amount=0,
    )
    for item in items:
        receipt.items.append(
            ReceiptItem(
                product_id=item.get("product_id"),
                raw_name=item.get("raw_name", "item"),
                normalized_name=item.get("normalized_name"),
                purchased_quantity=Decimal("1"),
                purchased_unit="pack",
                base_quantity=item.get("base_quantity"),
                base_unit=item.get("base_unit"),
                unit_price=1000,
                line_total=1000,
                is_inventory_target=item.get("is_inventory_target", True),
            )
        )
    db_session.add(receipt)
    db_session.commit()
    return receipt


def apply_receipt(client, receipt_id: int, payload: dict | None = None) -> dict:
    response = client.post(f"/inventory/receipts/{receipt_id}/apply", json=payload or {})
    assert response.status_code == 200
    return response.json()


def add_inventory(client, product: Product, *, quantity: str = "10.00") -> dict:
    response = client.post(
        "/inventory/movements",
        json={
            "product_id": product.id,
            "movement_type": "adjust",
            "quantity": quantity,
            "unit": product.default_base_unit,
            "reason": "initial stock",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_apply_receipt_to_inventory_success(client, db_session):
    product = create_product(db_session)
    receipt = create_receipt_with_items(
        db_session,
        [
            {
                "product_id": product.id,
                "normalized_name": product.name,
                "base_quantity": Decimal("10"),
                "base_unit": product.default_base_unit,
            }
        ],
    )

    body = apply_receipt(client, receipt.id)

    assert body["applied_count"] == 1
    assert body["skipped_count"] == 0
    assert body["items"][0]["status"] == "applied"
    batch = db_session.query(InventoryBatch).one()
    movement = db_session.query(InventoryMovement).one()
    assert batch.current_quantity == Decimal("10.00")
    assert batch.receipt_item_id == receipt.items[0].id
    assert movement.quantity_delta == Decimal("10.00")
    assert movement.movement_type == "purchase"


def test_apply_receipt_twice_skips_existing_item(client, db_session):
    product = create_product(db_session)
    receipt = create_receipt_with_items(
        db_session,
        [
            {
                "product_id": product.id,
                "normalized_name": product.name,
                "base_quantity": Decimal("10"),
                "base_unit": product.default_base_unit,
            }
        ],
    )

    first = apply_receipt(client, receipt.id)
    second = apply_receipt(client, receipt.id)

    assert first["applied_count"] == 1
    assert second["applied_count"] == 0
    assert second["skipped_count"] == 1
    assert second["items"][0]["reason"] == "already_applied"
    assert db_session.query(InventoryBatch).count() == 1


def test_apply_receipt_skips_non_inventory_item(client, db_session):
    product = create_product(db_session)
    receipt = create_receipt_with_items(
        db_session,
        [
            {
                "product_id": product.id,
                "normalized_name": product.name,
                "base_quantity": Decimal("10"),
                "base_unit": product.default_base_unit,
                "is_inventory_target": False,
            }
        ],
    )

    body = apply_receipt(client, receipt.id)

    assert body["applied_count"] == 0
    assert body["skipped_count"] == 1
    assert body["items"][0]["reason"] == "not_inventory_target"
    assert db_session.query(InventoryBatch).count() == 0


def test_apply_receipt_skips_missing_base_quantity_or_unit(client, db_session):
    product = create_product(db_session)
    receipt = create_receipt_with_items(
        db_session,
        [
            {
                "product_id": product.id,
                "normalized_name": product.name,
                "base_quantity": None,
                "base_unit": product.default_base_unit,
            },
            {
                "product_id": product.id,
                "normalized_name": product.name,
                "base_quantity": Decimal("10"),
                "base_unit": None,
            },
        ],
    )

    body = apply_receipt(client, receipt.id)

    assert body["applied_count"] == 0
    assert body["skipped_count"] == 2
    assert {item["reason"] for item in body["items"]} == {"missing_product_or_base_quantity"}
    assert db_session.query(InventoryBatch).count() == 0


def test_inventory_balances_group_by_product_and_unit(client, db_session):
    product = create_product(db_session)
    first = create_receipt_with_items(
        db_session,
        [
            {
                "product_id": product.id,
                "normalized_name": product.name,
                "base_quantity": Decimal("10"),
                "base_unit": product.default_base_unit,
            }
        ],
    )
    second = create_receipt_with_items(
        db_session,
        [
            {
                "product_id": product.id,
                "normalized_name": product.name,
                "base_quantity": Decimal("6"),
                "base_unit": product.default_base_unit,
            }
        ],
    )
    apply_receipt(client, first.id)
    apply_receipt(client, second.id)

    response = client.get("/inventory/balances")

    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "product_id": product.id,
            "product_name": product.name,
            "quantity": "16.00",
            "unit": product.default_base_unit,
            "nearest_expires_at": None,
            "batch_count": 2,
            "normalized_name": product.name,
            "current_quantity": "16.00",
            "base_unit": product.default_base_unit,
        }
    ]


def test_consume_decreases_inventory(client, db_session):
    product = create_product(db_session)
    add_inventory(client, product, quantity="10.00")

    response = client.post(
        "/inventory/movements",
        json={
            "product_id": product.id,
            "movement_type": "consume",
            "quantity": "3.00",
            "unit": product.default_base_unit,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["movements"][0]["quantity_delta"] == "-3.00"
    assert body["movements"][0]["remaining_quantity"] == "7.00"
    assert db_session.query(InventoryBatch).one().current_quantity == Decimal("7.00")


def test_consume_without_batch_id_uses_nearest_expiry_first(client, db_session):
    product = create_product(db_session)
    receipt = create_receipt_with_items(
        db_session,
        [
            {
                "product_id": product.id,
                "normalized_name": product.name,
                "base_quantity": Decimal("5"),
                "base_unit": product.default_base_unit,
            },
            {
                "product_id": product.id,
                "normalized_name": product.name,
                "base_quantity": Decimal("5"),
                "base_unit": product.default_base_unit,
            },
        ],
    )
    first_item_id = receipt.items[0].id
    second_item_id = receipt.items[1].id
    apply_receipt(
        client,
        receipt.id,
        {
            "expires_at_by_receipt_item_id": {
                str(first_item_id): "2026-05-20",
                str(second_item_id): "2026-06-01",
            }
        },
    )

    response = client.post(
        "/inventory/movements",
        json={
            "product_id": product.id,
            "movement_type": "consume",
            "quantity": "6.00",
            "unit": product.default_base_unit,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["movements"]) == 2
    assert body["movements"][0]["quantity_delta"] == "-5.00"
    assert body["movements"][0]["remaining_quantity"] == "0.00"
    assert body["movements"][1]["quantity_delta"] == "-1.00"
    assert body["movements"][1]["remaining_quantity"] == "4.00"


def test_consume_insufficient_inventory_returns_400(client, db_session):
    product = create_product(db_session)
    add_inventory(client, product, quantity="4.00")

    response = client.post(
        "/inventory/movements",
        json={
            "product_id": product.id,
            "movement_type": "consume",
            "quantity": "5.00",
            "unit": product.default_base_unit,
        },
    )

    assert response.status_code == 400
    assert db_session.query(InventoryBatch).one().current_quantity == Decimal("4.00")
    assert db_session.query(InventoryMovement).count() == 1


def test_adjust_positive_creates_inventory_batch(client, db_session):
    product = create_product(db_session)

    response = client.post(
        "/inventory/movements",
        json={
            "product_id": product.id,
            "movement_type": "adjust",
            "quantity": "6.00",
            "unit": product.default_base_unit,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["movements"][0]["quantity_delta"] == "6.00"
    batch = db_session.query(InventoryBatch).one()
    assert batch.receipt_item_id is None
    assert batch.current_quantity == Decimal("6.00")


def test_blank_idempotency_key_is_not_stored_in_unique_columns(client, db_session):
    product = create_product(db_session)

    for _ in range(2):
        response = client.post(
            "/inventory/movements",
            json={
                "product_id": product.id,
                "movement_type": "adjust",
                "quantity": "1.00",
                "unit": product.default_base_unit,
                "idempotency_key": "  ",
            },
        )
        assert response.status_code == 200

    operations = db_session.query(InventoryOperation).order_by(InventoryOperation.id).all()
    movements = db_session.query(InventoryMovement).order_by(InventoryMovement.id).all()

    assert len(operations) == 2
    assert len(movements) == 2
    assert [operation.idempotency_key for operation in operations] == [None, None]
    assert [movement.idempotency_key for movement in movements] == [None, None]


def test_dispose_decreases_inventory_and_records_movement(client, db_session):
    product = create_product(db_session)
    add_inventory(client, product, quantity="8.00")

    response = client.post(
        "/inventory/movements",
        json={
            "product_id": product.id,
            "movement_type": "dispose",
            "quantity": "2.00",
            "unit": product.default_base_unit,
            "reason": "expired",
        },
    )

    assert response.status_code == 200
    assert db_session.query(InventoryBatch).one().current_quantity == Decimal("6.00")
    movements_response = client.get(f"/inventory/movements?product_id={product.id}")
    assert movements_response.status_code == 200
    movements = movements_response.json()["items"]
    assert any(
        movement["movement_type"] == "dispose"
        and movement["quantity_delta"] == "-2.00"
        and movement["reason"] == "expired"
        for movement in movements
    )
