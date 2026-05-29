from app.crud.inventory import seed_inventory_locations
from app.db.session import SessionLocal
from app.receipts.models import AccountingCategory, Product, ProductAlias
from app.services.product_normalization import normalize_product_key


DEFAULT_CATEGORIES = [
    ("食費", 10),
    ("日用品", 20),
    ("その他", 90),
]

DEFAULT_PRODUCTS = [
    ("手動登録商品", "個", True, ["手動登録商品"]),
    ("牛乳", "ml", True, ["牛乳", "ミルク", "プレミアム牛乳"]),
    ("卵", "個", True, ["卵", "たまご", "玉子", "新鮮たまご"]),
    ("パン", "個", True, ["パン", "食パン"]),
    ("米", "g", True, ["米", "お米"]),
]


def _seed_accounting_categories(db) -> dict[str, AccountingCategory]:
    categories_by_name = {
        category.name: category
        for category in db.query(AccountingCategory).all()
    }
    for name, sort_order in DEFAULT_CATEGORIES:
        if name not in categories_by_name:
            category = AccountingCategory(name=name, sort_order=sort_order)
            db.add(category)
            db.flush()
            categories_by_name[name] = category
    return categories_by_name


def _seed_products(db, *, default_category_id: int | None) -> None:
    for name, default_base_unit, is_inventory_target, aliases in DEFAULT_PRODUCTS:
        name_key = normalize_product_key(name)
        if name_key is None:
            continue

        product = db.query(Product).filter(Product.name_key == name_key).first()
        if product is None:
            product = Product(
                name=name,
                name_key=name_key,
                default_base_unit=default_base_unit,
                default_category_id=default_category_id,
                is_inventory_target=is_inventory_target,
            )
            db.add(product)
            db.flush()
        elif product.default_category_id is None and default_category_id is not None:
            product.default_category_id = default_category_id

        for alias_name in aliases:
            alias_key = normalize_product_key(alias_name)
            if alias_key is None:
                continue
            existing_alias = db.query(ProductAlias).filter(
                ProductAlias.alias_key == alias_key
            ).first()
            if existing_alias is None:
                db.add(
                    ProductAlias(
                        product_id=product.id,
                        alias_name=alias_name,
                        alias_key=alias_key,
                        source="seed",
                        is_active=True,
                    )
                )


def seed_master_data() -> None:
    db = SessionLocal()
    try:
        seed_inventory_locations(db)
        categories = _seed_accounting_categories(db)
        _seed_products(db, default_category_id=categories["食費"].id)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    seed_master_data()


if __name__ == "__main__":
    main()
