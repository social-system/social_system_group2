from app.receipts.models import Product, ProductAlias, Receipt
from app.services.product_normalization import normalize_product_key


def make_product(db_session, *, name: str, unit: str = "個") -> Product:
    product = Product(
        name=name,
        name_key=normalize_product_key(name),
        default_base_unit=unit,
        is_inventory_target=True,
    )
    db_session.add(product)
    db_session.commit()
    return product


def make_alias(
    db_session,
    *,
    product: Product,
    alias_name: str,
    is_active: bool = True,
) -> ProductAlias:
    alias = ProductAlias(
        product_id=product.id,
        alias_name=alias_name,
        alias_key=normalize_product_key(alias_name),
        source="seed",
        is_active=is_active,
    )
    db_session.add(alias)
    db_session.commit()
    return alias


def test_receipt_prepare_metrics_returns_empty_state(client):
    response = client.get("/operations/receipt-prepare-metrics")

    assert response.status_code == 200
    assert response.json() == {
        "prepare_count": 0,
        "total_item_count": 0,
        "unresolved_item_count": 0,
        "unresolved_rate": 0.0,
        "alias_count": 0,
        "active_alias_count": 0,
        "alias_conflict_count": 0,
        "inventory_base_quantity_missing_count": 0,
        "top_unresolved_raw_names": [],
    }


def test_receipt_prepare_metrics_are_recorded_after_prepare(client, db_session):
    response = client.post(
        "/receipts/prepare",
        json={
            "status": "needs_confirmation",
            "store_name": "保存しない店舗名",
            "purchased_at": "2026-05-12",
            "total_amount": 300,
            "items": [
                {
                    "raw_name": "未知の商品",
                    "normalized_name": "未知の商品",
                    "purchased_quantity": 1,
                    "purchased_unit": "個",
                    "line_total": 100,
                    "is_inventory_target": False,
                },
                {
                    "raw_name": "トマト 2個",
                    "normalized_name": "トマト",
                    "purchased_quantity": 2,
                    "purchased_unit": "個",
                    "line_total": 200,
                    "is_inventory_target": True,
                },
            ],
            "warnings": [],
        },
    )
    assert response.status_code == 200
    assert db_session.query(Receipt).count() == 0

    metrics = client.get("/operations/receipt-prepare-metrics").json()

    assert metrics["prepare_count"] == 1
    assert metrics["total_item_count"] == 2
    assert metrics["unresolved_item_count"] == 2
    assert metrics["unresolved_rate"] == 1.0
    assert metrics["inventory_base_quantity_missing_count"] == 1
    assert {
        "raw_name": "トマト 2個",
        "raw_name_key": "とまと2個",
        "count": 1,
    } in metrics["top_unresolved_raw_names"]


def test_alias_conflict_count_is_recorded(client, db_session):
    egg = make_product(db_session, name="卵", unit="個")
    milk = make_product(db_session, name="牛乳", unit="ml")
    first = client.post(
        "/product-aliases",
        json={"alias_name": "タマゴM 10コ", "product_id": egg.id},
    )
    assert first.status_code == 200

    conflict = client.post(
        "/product-aliases",
        json={"alias_name": "タマゴM 10コ", "product_id": milk.id},
    )
    assert conflict.status_code == 409

    metrics = client.get("/operations/receipt-prepare-metrics").json()
    assert metrics["alias_conflict_count"] == 1


def test_alias_counts_are_read_from_product_aliases(client, db_session):
    product = make_product(db_session, name="卵", unit="個")
    make_alias(db_session, product=product, alias_name="タマゴM 10コ", is_active=True)
    make_alias(db_session, product=product, alias_name="白たまご", is_active=False)

    response = client.get("/operations/receipt-prepare-metrics")

    assert response.status_code == 200
    metrics = response.json()
    assert metrics["alias_count"] == 2
    assert metrics["active_alias_count"] == 1
