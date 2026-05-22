import pytest
from sqlalchemy.exc import IntegrityError

from app.receipts.models import Product, ProductAlias


def make_product(db_session, *, name: str = "egg", name_key: str = "egg") -> Product:
    product = Product(
        name=name,
        name_key=name_key,
        default_base_unit="pcs",
        is_inventory_target=True,
    )
    db_session.add(product)
    db_session.commit()
    return product


def test_product_saves_name_key(db_session):
    product = make_product(db_session, name="egg", name_key="egg")

    assert product.id is not None
    assert product.name == "egg"
    assert product.name_key == "egg"


def test_product_name_key_must_be_unique(db_session):
    make_product(db_session, name="egg", name_key="egg")
    db_session.add(
        Product(
            name="eggs",
            name_key="egg",
            default_base_unit="pcs",
            is_inventory_target=True,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_product_alias_saves_alias_key_and_links_product(db_session):
    product = make_product(db_session)
    alias = ProductAlias(
        product_id=product.id,
        alias_name="white egg",
        alias_key="whiteegg",
        source="seed",
    )
    db_session.add(alias)
    db_session.commit()
    db_session.refresh(alias)

    assert alias.id is not None
    assert alias.alias_name == "white egg"
    assert alias.alias_key == "whiteegg"
    assert alias.source == "seed"
    assert alias.is_active is True
    assert alias.product_id == product.id
    assert alias.product == product
    assert product.aliases == [alias]


def test_product_alias_key_must_be_unique(db_session):
    product = make_product(db_session)
    db_session.add(
        ProductAlias(
            product_id=product.id,
            alias_name="egg pack",
            alias_key="eggpack",
        )
    )
    db_session.commit()
    db_session.add(
        ProductAlias(
            product_id=product.id,
            alias_name="egg pack duplicate",
            alias_key="eggpack",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
