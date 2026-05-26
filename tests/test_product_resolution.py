import pytest

from app.receipts.models import Product, ProductAlias
from app.services.product_normalization import normalize_product_key
from app.services.product_resolution import (
    ProductResolutionInput,
    resolve_product,
    search_product_candidates,
)
from tests.fixtures.receipt_variation_samples import PRODUCT_NAME_VARIATION_SAMPLES


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
    source: str = "seed",
    is_active: bool = True,
) -> ProductAlias:
    alias = ProductAlias(
        product_id=product.id,
        alias_name=alias_name,
        alias_key=alias_key or normalize_product_key(alias_name),
        source=source,
        is_active=is_active,
    )
    db_session.add(alias)
    db_session.commit()
    return alias


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ﾀﾏｺﾞ", "たまご"),
        ("ＴＡＭＡＧＯ１２３", "tamago123"),
        ("タ マ ゴ", "たまご"),
        ("タマゴ-M 10コ", "たまごm10こ"),
        ("たまご", "たまご"),
        ("タマゴ", "たまご"),
        (" 卵 ", "卵"),
        (" ＡＢＣ　１０個 ", "abc10個"),
        ("タマゴ・M（10コ）", "たまごm10こ"),
    ],
)
def test_normalize_product_key_handles_ocr_variations(value, expected):
    assert normalize_product_key(value) == expected


def test_normalize_product_key_returns_none_for_none_and_blank_values():
    assert normalize_product_key(None) is None
    assert normalize_product_key("") is None
    assert normalize_product_key(" \t　\n") is None


def test_normalize_product_key_does_not_drop_numbers_units_or_specs():
    assert normalize_product_key("卵10個") == "卵10個"
    assert normalize_product_key("牛乳1L") == "牛乳1l"
    assert normalize_product_key("タマゴM") == "たまごm"


def test_normalize_product_key_does_not_convert_synonyms():
    assert normalize_product_key("玉子") != normalize_product_key("卵")


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


@pytest.mark.parametrize("source", ["user_confirmed", "seed", "admin"])
def test_resolve_product_uses_trusted_alias_sources(db_session, source):
    product = make_product(db_session, name="卵")
    make_alias(
        db_session,
        product=product,
        alias_name=f"タマゴ-{source}",
        source=source,
    )

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name=f"タマゴ-{source}",
            normalized_name=None,
        ),
    )

    assert result.resolution_status == "resolved"
    assert result.resolution_source == "raw_name_alias"
    assert result.product_id == product.id


def test_resolve_product_does_not_auto_resolve_ocr_suggested_alias(db_session):
    product = make_product(db_session, name="卵")
    make_alias(
        db_session,
        product=product,
        alias_name="タマゴM 10コ",
        source="ocr_suggested",
    )

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name="タマゴM 10コ",
            normalized_name=None,
        ),
    )

    assert result.resolution_status == "unresolved"
    assert result.resolution_source == "candidate_only"
    assert result.product_id is None
    assert [candidate.product_id for candidate in result.candidates] == [product.id]
    assert result.candidates[0].match_source == "alias"


def test_resolve_product_uses_alias_after_registration(db_session):
    product = make_product(db_session, name="卵")
    raw_name = "タマゴM 10コ"

    before = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name=raw_name,
            normalized_name=None,
        ),
    )
    assert before.resolution_status == "unresolved"
    assert before.resolution_source == "none"

    make_alias(db_session, product=product, alias_name=raw_name)

    after = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name=raw_name,
            normalized_name=None,
        ),
    )

    assert after.resolution_status == "resolved"
    assert after.resolution_source == "raw_name_alias"
    assert after.product_id == product.id


def test_resolve_product_does_not_use_inactive_alias(db_session):
    product = make_product(db_session, name="卵")
    make_alias(db_session, product=product, alias_name="タマゴ", is_active=False)

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name="タマゴ",
            normalized_name=None,
        ),
    )

    assert result.resolution_status == "unresolved"
    assert result.resolution_source == "none"
    assert result.product_id is None
    assert result.candidates == []


def test_search_product_candidates_does_not_use_inactive_alias(db_session):
    product = make_product(db_session, name="卵")
    make_alias(
        db_session,
        product=product,
        alias_name="タマゴM 10コ",
        source="ocr_suggested",
        is_active=False,
    )

    candidates = search_product_candidates(
        db_session,
        raw_name="タマゴM 10コ",
    )

    assert candidates == []


@pytest.mark.parametrize("sample", PRODUCT_NAME_VARIATION_SAMPLES)
def test_provided_product_name_samples_resolve_only_with_safe_exact_matches(
    db_session,
    sample,
):
    product = make_product(db_session, name=sample["expected_product_name"])
    if sample["raw_name"] != sample["expected_product_name"]:
        make_alias(db_session, product=product, alias_name=sample["raw_name"])

    result = resolve_product(
        db_session,
        ProductResolutionInput(
            product_id=None,
            raw_name=sample["raw_name"],
            normalized_name=sample["normalized_name"],
        ),
    )

    assert result.resolution_status == "resolved"
    assert result.product_id == product.id


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
