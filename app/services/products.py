from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.receipts.models import Product, ProductAlias
from app.services.product_normalization import normalize_product_key


@dataclass(frozen=True)
class ProductSearchResultItem:
    product_id: int
    name: str
    default_base_unit: str
    default_category_id: int | None
    is_inventory_target: bool


@dataclass(frozen=True)
class ProductAliasCreateResult:
    alias: ProductAlias
    created: bool


class ProductAliasConflictError(ValueError):
    pass


def _search_item_from_product(product: Product) -> ProductSearchResultItem:
    return ProductSearchResultItem(
        product_id=product.id,
        name=product.name,
        default_base_unit=product.default_base_unit,
        default_category_id=product.default_category_id,
        is_inventory_target=product.is_inventory_target,
    )


def search_products(
    db: Session,
    *,
    query: str,
    limit: int = 10,
) -> tuple[str, list[ProductSearchResultItem]]:
    query_key = normalize_product_key(query)
    if query_key is None:
        raise ValueError("query must not be empty")

    items_by_product_id: dict[int, ProductSearchResultItem] = {}

    product_statement = (
        select(Product)
        .where(Product.name_key.contains(query_key))
        .order_by(Product.id)
    )
    for product in db.scalars(product_statement):
        items_by_product_id[product.id] = _search_item_from_product(product)
        if len(items_by_product_id) >= limit:
            return query_key, list(items_by_product_id.values())

    alias_statement = (
        select(ProductAlias)
        .where(ProductAlias.is_active.is_(True))
        .where(ProductAlias.alias_key.contains(query_key))
        .order_by(ProductAlias.id)
    )
    for alias in db.scalars(alias_statement):
        items_by_product_id.setdefault(
            alias.product_id,
            _search_item_from_product(alias.product),
        )
        if len(items_by_product_id) >= limit:
            break

    return query_key, list(items_by_product_id.values())[:limit]


def create_product_alias(
    db: Session,
    *,
    alias_name: str,
    product_id: int,
    source: str = "user_confirmed",
) -> ProductAliasCreateResult:
    alias_key = normalize_product_key(alias_name)
    if alias_key is None:
        raise ValueError("alias_name must not be empty")

    product = db.get(Product, product_id)
    if product is None:
        raise LookupError(f"product_id does not exist: {product_id}")

    existing = db.scalars(
        select(ProductAlias).where(ProductAlias.alias_key == alias_key)
    ).first()
    if existing is not None:
        if existing.product_id != product_id:
            raise ProductAliasConflictError(
                "alias_key is already linked to another product"
            )
        return ProductAliasCreateResult(alias=existing, created=False)

    alias = ProductAlias(
        product_id=product_id,
        alias_name=alias_name.strip(),
        alias_key=alias_key,
        source=source.strip(),
        is_active=True,
    )
    db.add(alias)
    db.flush()
    return ProductAliasCreateResult(alias=alias, created=True)
