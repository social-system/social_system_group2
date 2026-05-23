from app.receipts.models import Product, ProductAlias
from app.services.product_normalization import normalize_product_key
from app.services.product_resolution import ProductResolutionInput, resolve_product


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


def test_search_products_finds_product_by_name_key(client, db_session):
    product = make_product(db_session, name="卵", unit="個")

    response = client.get("/products/search?query=卵")

    assert response.status_code == 200
    assert response.json() == {
        "query": "卵",
        "query_key": "卵",
        "items": [
            {
                "product_id": product.id,
                "name": "卵",
                "default_base_unit": "個",
                "default_category_id": None,
                "is_inventory_target": True,
            }
        ],
    }


def test_search_products_finds_product_by_alias_key(client, db_session):
    product = make_product(db_session, name="卵", unit="個")
    make_alias(db_session, product=product, alias_name="タマゴM 10コ")

    response = client.get("/products/search?query=タマゴ")

    assert response.status_code == 200
    body = response.json()
    assert body["query_key"] == "たまご"
    assert body["items"] == [
        {
            "product_id": product.id,
            "name": "卵",
            "default_base_unit": "個",
            "default_category_id": None,
            "is_inventory_target": True,
        }
    ]


def test_search_products_deduplicates_product_matches(client, db_session):
    product = make_product(db_session, name="たまご", unit="個")
    make_alias(db_session, product=product, alias_name="タマゴM 10コ")

    response = client.get("/products/search?query=タマゴ")

    assert response.status_code == 200
    assert [item["product_id"] for item in response.json()["items"]] == [product.id]


def test_search_products_rejects_blank_query(client):
    response = client.get("/products/search?query=   ")

    assert response.status_code == 400


def test_create_product_alias(client, db_session):
    product = make_product(db_session, name="卵", unit="個")

    response = client.post(
        "/product-aliases",
        json={
            "alias_name": "タマゴM 10コ",
            "product_id": product.id,
            "source": "user_confirmed",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "id": body["id"],
        "alias_name": "タマゴM 10コ",
        "alias_key": "たまごm10こ",
        "product_id": product.id,
        "product_name": "卵",
        "source": "user_confirmed",
        "created": True,
    }


def test_create_product_alias_is_idempotent_for_same_product(client, db_session):
    product = make_product(db_session, name="卵", unit="個")
    first = client.post(
        "/product-aliases",
        json={"alias_name": "タマゴM 10コ", "product_id": product.id},
    )
    second = client.post(
        "/product-aliases",
        json={"alias_name": "タマゴM 10コ", "product_id": product.id},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["created"] is False


def test_create_product_alias_conflicts_for_other_product(client, db_session):
    egg = make_product(db_session, name="卵", unit="個")
    milk = make_product(db_session, name="牛乳", unit="ml")
    first = client.post(
        "/product-aliases",
        json={"alias_name": "タマゴM 10コ", "product_id": egg.id},
    )

    response = client.post(
        "/product-aliases",
        json={"alias_name": "タマゴM 10コ", "product_id": milk.id},
    )

    assert first.status_code == 200
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "alias_conflict"


def test_create_product_alias_returns_404_for_missing_product(client):
    response = client.post(
        "/product-aliases",
        json={"alias_name": "タマゴM 10コ", "product_id": 999},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "product_not_found"


def test_created_alias_is_used_by_product_resolution(client, db_session):
    product = make_product(db_session, name="卵", unit="個")
    response = client.post(
        "/product-aliases",
        json={"alias_name": "タマゴM 10コ", "product_id": product.id},
    )
    assert response.status_code == 200

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name="タマゴM 10コ",
            normalized_name=None,
        ),
    )

    assert result.resolution_status == "resolved"
    assert result.resolution_source == "raw_name_alias"
    assert result.product_id == product.id
