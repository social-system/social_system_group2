from app.receipts.models import Product, ProductAlias
from app.services.product_normalization import normalize_product_key
from app.services.product_resolution import (
    ProductResolutionInput,
    resolve_product,
    search_product_candidates,
)


def make_product(
    db_session,
    *,
    name: str,
    name_key: str | None = None,
    unit: str = "個",
) -> Product:
    product = Product(
        name=name,
        name_key=name_key or normalize_product_key(name),
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
    alias_key: str | None = None,
) -> ProductAlias:
    alias = ProductAlias(
        product_id=product.id,
        alias_name=alias_name,
        alias_key=alias_key or normalize_product_key(alias_name),
        source="seed",
    )
    db_session.add(alias)
    db_session.commit()
    return alias


def test_normalize_product_key_strips_whitespace():
    assert normalize_product_key(" 卵 ") == normalize_product_key("卵")


def test_normalize_product_key_uses_nfkc_and_lowercase():
    assert normalize_product_key(" ＡＢＣ　１０個 ") == "abc10個"


def test_normalize_product_key_converts_katakana_to_hiragana():
    assert normalize_product_key("タマゴ") == normalize_product_key("たまご")


def test_resolve_product_prefers_request_product_id(db_session):
    requested = make_product(db_session, name="牛乳", unit="ml")
    alias_target = make_product(db_session, name="卵")
    make_alias(db_session, product=alias_target, alias_name="タマゴ")

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=requested.id,
            raw_name="タマゴ",
            normalized_name="卵",
        ),
    )

    assert result.resolution_status == "resolved"
    assert result.resolution_source == "request_product_id"
    assert result.product_id == requested.id
    assert result.product_name == "牛乳"


def test_resolve_product_returns_invalid_product_id(db_session):
    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=999,
            raw_name="卵",
            normalized_name="卵",
        ),
    )

    assert result.resolution_status == "invalid_product_id"
    assert result.resolution_source == "request_product_id"
    assert result.product_id is None
    assert result.candidates == []


def test_resolve_product_uses_raw_name_alias(db_session):
    product = make_product(db_session, name="卵")
    make_alias(db_session, product=product, alias_name="タマゴ")

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name="タマゴ",
            normalized_name=None,
        ),
    )

    assert result.resolution_status == "resolved"
    assert result.resolution_source == "raw_name_alias"
    assert result.product_id == product.id
    assert result.normalized_name == "卵"


def test_resolve_product_uses_normalized_name_alias(db_session):
    product = make_product(db_session, name="卵")
    make_alias(db_session, product=product, alias_name="タマゴ")

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name="unknown",
            normalized_name="タマゴ",
        ),
    )

    assert result.resolution_status == "resolved"
    assert result.resolution_source == "normalized_name_alias"
    assert result.product_id == product.id


def test_resolve_product_uses_normalized_name_product_key(db_session):
    product = make_product(db_session, name="卵")

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name=None,
            normalized_name=" 卵 ",
        ),
    )

    assert result.resolution_status == "resolved"
    assert result.resolution_source == "normalized_name_product"
    assert result.product_id == product.id


def test_resolve_product_uses_raw_name_product_key(db_session):
    product = make_product(db_session, name="卵")

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name=" 卵 ",
            normalized_name=None,
        ),
    )

    assert result.resolution_status == "resolved"
    assert result.resolution_source == "raw_name_product"
    assert result.product_id == product.id


def test_resolve_product_uses_priority_order_for_raw_and_normalized_names(db_session):
    raw_match = make_product(db_session, name="卵")
    normalized_match = make_product(db_session, name="牛乳", unit="ml")
    make_alias(db_session, product=raw_match, alias_name="タマゴ")

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name="タマゴ",
            normalized_name="牛乳",
        ),
    )

    assert result.resolution_status == "resolved"
    assert result.resolution_source == "raw_name_alias"
    assert result.product_id == raw_match.id
    assert result.product_id != normalized_match.id


def test_resolve_product_returns_unresolved_without_candidates(db_session):
    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name="unknown",
            normalized_name=None,
        ),
    )

    assert result.resolution_status == "unresolved"
    assert result.resolution_source == "none"
    assert result.product_id is None
    assert result.candidates == []


def test_resolve_product_does_not_auto_resolve_candidate_only_match(db_session):
    product = make_product(db_session, name="卵")

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name="卵10個",
            normalized_name=None,
        ),
    )

    assert result.resolution_status == "unresolved"
    assert result.resolution_source == "candidate_only"
    assert result.product_id is None
    assert [candidate.product_id for candidate in result.candidates] == [product.id]


def test_search_product_candidates_uses_alias_name_without_auto_adopting(db_session):
    product = make_product(db_session, name="卵")
    make_alias(db_session, product=product, alias_name="白たまご")

    candidates = search_product_candidates(
        db_session,
        raw_name="白たまご10個",
    )

    assert len(candidates) == 1
    assert candidates[0].product_id == product.id
    assert candidates[0].match_source == "alias"
