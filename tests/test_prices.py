from datetime import date, timedelta

from app.common.date import format_yyyymmdd
from app.receipts.models import Product


def make_product(db_session, *, name: str = "egg", unit: str = "個") -> Product:
    product = Product(
        name=name,
        default_base_unit=unit,
        is_inventory_target=True,
    )
    db_session.add(product)
    db_session.commit()
    return product


def make_receipt_payload(
    *,
    product_id: int,
    purchased_at: int | None = None,
    store_name: str | None = "sample store",
    raw_name: str = "egg",
    normalized_name: str = "egg",
    line_total: int = 238,
    base_quantity: int | None = 10,
    base_unit: str | None = "個",
) -> dict:
    return {
        "purchased_at": purchased_at or format_yyyymmdd(date.today()),
        "store_name": store_name,
        "total_amount": line_total,
        "items": [
            {
                "raw_name": raw_name,
                "normalized_name": normalized_name,
                "product_id": product_id,
                "category_id": None,
                "purchased_quantity": 1,
                "purchased_unit": "パック",
                "base_quantity": base_quantity,
                "base_unit": base_unit,
                "unit_price": line_total,
                "line_total": line_total,
                "is_inventory_target": False,
            }
        ],
    }


def create_receipt(client, **kwargs) -> dict:
    response = client.post("/receipts", json=make_receipt_payload(**kwargs))
    assert response.status_code == 201
    return response.json()


def test_cheapest_price_returns_cheapest_store(client, db_session):
    product = make_product(db_session)
    create_receipt(client, product_id=product.id, store_name="expensive store", line_total=300)
    expected = create_receipt(client, product_id=product.id, store_name="cheap store", line_total=200)

    response = client.get(f"/prices/cheapest?product_id={product.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["product_id"] == product.id
    assert body["product_name"] == product.name
    assert body["period_days"] == 90
    assert body["cheapest"] == {
        "store_name": "cheap store",
        "price_per_base_unit": 20.0,
        "line_total": 200,
        "base_quantity": "10.00",
        "base_unit": "個",
        "purchased_at": format_yyyymmdd(date.today()),
        "receipt_item_id": body["cheapest"]["receipt_item_id"],
    }
    detail = client.get(f"/receipts/{expected['id']}").json()
    assert body["cheapest"]["receipt_item_id"] == detail["items"][0]["id"]


def test_cheapest_price_compares_price_per_base_unit_not_line_total(client, db_session):
    product = make_product(db_session)
    create_receipt(
        client,
        product_id=product.id,
        store_name="six pack store",
        line_total=180,
        base_quantity=6,
    )
    create_receipt(
        client,
        product_id=product.id,
        store_name="ten pack store",
        line_total=238,
        base_quantity=10,
    )

    response = client.get(f"/prices/cheapest?product_id={product.id}")

    assert response.status_code == 200
    cheapest = response.json()["cheapest"]
    assert cheapest["store_name"] == "ten pack store"
    assert cheapest["price_per_base_unit"] == 23.8
    assert cheapest["line_total"] == 238
    assert cheapest["base_quantity"] == "10.00"


def test_cheapest_price_excludes_null_base_quantity(client, db_session):
    product = make_product(db_session)
    create_receipt(
        client,
        product_id=product.id,
        store_name="missing quantity store",
        line_total=1,
        base_quantity=None,
    )
    create_receipt(client, product_id=product.id, store_name="valid store", line_total=300)

    response = client.get(f"/prices/cheapest?product_id={product.id}")

    assert response.status_code == 200
    assert response.json()["cheapest"]["store_name"] == "valid store"


def test_cheapest_price_excludes_zero_base_quantity(client, db_session):
    product = make_product(db_session)
    create_receipt(
        client,
        product_id=product.id,
        store_name="zero quantity store",
        line_total=1,
        base_quantity=0,
    )
    create_receipt(client, product_id=product.id, store_name="valid store", line_total=300)

    response = client.get(f"/prices/cheapest?product_id={product.id}")

    assert response.status_code == 200
    assert response.json()["cheapest"]["store_name"] == "valid store"


def test_cheapest_price_excludes_null_base_unit(client, db_session):
    product = make_product(db_session)
    create_receipt(
        client,
        product_id=product.id,
        store_name="missing unit store",
        line_total=1,
        base_unit=None,
    )
    create_receipt(client, product_id=product.id, store_name="valid store", line_total=300)

    response = client.get(f"/prices/cheapest?product_id={product.id}")

    assert response.status_code == 200
    assert response.json()["cheapest"]["store_name"] == "valid store"


def test_cheapest_price_excludes_null_store_name(client, db_session):
    product = make_product(db_session)
    create_receipt(
        client,
        product_id=product.id,
        store_name=None,
        line_total=1,
    )
    create_receipt(client, product_id=product.id, store_name="valid store", line_total=300)

    response = client.get(f"/prices/cheapest?product_id={product.id}")

    assert response.status_code == 200
    assert response.json()["cheapest"]["store_name"] == "valid store"


def test_cheapest_price_excludes_receipts_outside_period(client, db_session):
    product = make_product(db_session)
    old_date = format_yyyymmdd(date.today() - timedelta(days=91))
    create_receipt(
        client,
        product_id=product.id,
        purchased_at=old_date,
        store_name="old cheap store",
        line_total=1,
    )
    create_receipt(client, product_id=product.id, store_name="current store", line_total=300)

    response = client.get(f"/prices/cheapest?product_id={product.id}&period_days=90")

    assert response.status_code == 200
    assert response.json()["cheapest"]["store_name"] == "current store"


def test_cheapest_price_returns_null_when_no_data(client, db_session):
    product = make_product(db_session)

    response = client.get(f"/prices/cheapest?product_id={product.id}")

    assert response.status_code == 200
    assert response.json() == {
        "product_id": product.id,
        "product_name": product.name,
        "period_days": 90,
        "cheapest": None,
    }
