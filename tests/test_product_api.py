from app.receipts.models import AccountingCategory, Product, ProductAlias
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


def make_category(db_session, *, name: str = "食費") -> AccountingCategory:
    category = AccountingCategory(name=name, sort_order=10)
    db_session.add(category)
    db_session.commit()
    return category


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


def test_search_products_normalizes_halfwidth_kana_and_ocr_noise(client, db_session):
    product = make_product(db_session, name="卵", unit="個")
    make_alias(db_session, product=product, alias_name="タマゴM 10コ")

    response = client.get("/products/search?query=ﾀﾏｺﾞ-M")

    assert response.status_code == 200
    body = response.json()
    assert body["query_key"] == "たまごm"
    assert [item["product_id"] for item in body["items"]] == [product.id]


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


def test_create_product_alias_rejects_blank_alias_name(client, db_session):
    product = make_product(db_session, name="卵", unit="個")

    response = client.post(
        "/product-aliases",
        json={
            "alias_name": "   ",
            "product_id": product.id,
            "source": "user_confirmed",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_alias"


def test_create_product_alias_rejects_invalid_source(client, db_session):
    product = make_product(db_session, name="卵", unit="個")

    response = client.post(
        "/product-aliases",
        json={
            "alias_name": "タマゴM 10コ",
            "product_id": product.id,
            "source": "manual",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_alias"
    assert "source must be one of" in response.json()["detail"]["message"]


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


def test_create_product(client, db_session):
    category = make_category(db_session)

    response = client.post(
        "/products",
        json={
            "name": "豆腐",
            "default_base_unit": "g",
            "is_inventory_target": True,
            "default_category_id": category.id,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "id": body["id"],
        "name": "豆腐",
        "name_key": "豆腐",
        "default_base_unit": "g",
        "default_category_id": category.id,
        "is_inventory_target": True,
        "created_alias": None,
    }
    product = db_session.get(Product, body["id"])
    assert product is not None
    assert product.name_key == "豆腐"


def test_create_product_generates_name_key_server_side(client):
    response = client.post(
        "/products",
        json={
            "name": "ＴＯＦＵ１２３",
            "name_key": "client-value-is-ignored",
            "default_base_unit": "g",
            "is_inventory_target": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["name_key"] == "tofu123"


def test_create_product_rejects_blank_name(client):
    response = client.post(
        "/products",
        json={
            "name": "   ",
            "default_base_unit": "g",
            "is_inventory_target": True,
        },
    )

    assert response.status_code in {400, 422}


def test_create_product_rejects_blank_default_base_unit(client):
    response = client.post(
        "/products",
        json={
            "name": "豆腐",
            "default_base_unit": "   ",
            "is_inventory_target": True,
        },
    )

    assert response.status_code in {400, 422}


def test_create_product_requires_is_inventory_target(client):
    response = client.post(
        "/products",
        json={
            "name": "豆腐",
            "default_base_unit": "g",
        },
    )

    assert response.status_code == 422


def test_create_product_returns_404_for_missing_default_category(client):
    response = client.post(
        "/products",
        json={
            "name": "豆腐",
            "default_base_unit": "g",
            "is_inventory_target": True,
            "default_category_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "category_not_found"


def test_create_product_conflicts_for_same_name_key(client, db_session):
    make_product(db_session, name="たまご", unit="個")

    response = client.post(
        "/products",
        json={
            "name": "タマゴ",
            "default_base_unit": "個",
            "is_inventory_target": True,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "product_conflict"


def test_create_product_registers_initial_alias(client, db_session):
    response = client.post(
        "/products",
        json={
            "name": "豆腐",
            "default_base_unit": "g",
            "is_inventory_target": True,
            "initial_alias_name": "絹とうふ 300g",
            "alias_source": "user_confirmed",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["created_alias"] == {
        "id": body["created_alias"]["id"],
        "alias_name": "絹とうふ 300g",
        "alias_key": "絹とうふ300g",
        "product_id": body["id"],
        "source": "user_confirmed",
    }

    alias = db_session.get(ProductAlias, body["created_alias"]["id"])
    assert alias is not None
    assert alias.product_id == body["id"]


def test_create_product_rolls_back_when_initial_alias_conflicts(client, db_session):
    existing = make_product(db_session, name="厚揚げ", unit="g")
    make_alias(db_session, product=existing, alias_name="絹とうふ 300g")

    response = client.post(
        "/products",
        json={
            "name": "豆腐",
            "default_base_unit": "g",
            "is_inventory_target": True,
            "initial_alias_name": "絹とうふ 300g",
            "alias_source": "user_confirmed",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "alias_conflict"
    assert (
        db_session.query(Product)
        .filter(Product.name_key == normalize_product_key("豆腐"))
        .first()
        is None
    )


def test_created_product_initial_alias_is_used_by_product_resolution(client, db_session):
    response = client.post(
        "/products",
        json={
            "name": "豆腐",
            "default_base_unit": "g",
            "is_inventory_target": True,
            "initial_alias_name": "絹とうふ 300g",
            "alias_source": "user_confirmed",
        },
    )
    assert response.status_code == 201

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name="絹とうふ 300g",
            normalized_name=None,
        ),
    )

    assert result.resolution_status == "resolved"
    assert result.resolution_source == "raw_name_alias"
    assert result.product_id == response.json()["id"]
