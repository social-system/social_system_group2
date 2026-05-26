from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.product_alias_sources import (
    ALLOWED_ALIAS_SOURCES,
    CANDIDATE_ALIAS_SOURCES,
    DEFAULT_ALIAS_SOURCE,
)
from app.receipts.models import AccountingCategory, Product, ProductAlias
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


@dataclass(frozen=True)
class ProductCreateResult:
    product: Product
    created_alias: ProductAlias | None


class ProductAliasConflictError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        alias_key: str | None = None,
        requested_product_id: int | None = None,
        existing_product_id: int | None = None,
    ) -> None:
        super().__init__(message)
        self.alias_key = alias_key
        self.requested_product_id = requested_product_id
        self.existing_product_id = existing_product_id


class ProductConflictError(ValueError):
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
        .where(ProductAlias.source.in_(CANDIDATE_ALIAS_SOURCES))
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


def create_product(
    db: Session,
    *,
    name: str,
    default_base_unit: str,
    is_inventory_target: bool,
    default_category_id: int | None = None,
    initial_alias_name: str | None = None,
    alias_source: str = DEFAULT_ALIAS_SOURCE,
) -> ProductCreateResult:
    name_key = normalize_product_key(name)
    if name_key is None:
        raise ValueError("name must not be empty")

    default_base_unit = default_base_unit.strip()
    if not default_base_unit:
        raise ValueError("default_base_unit must not be empty")

    if default_category_id is not None and db.get(AccountingCategory, default_category_id) is None:
        raise LookupError(f"default_category_id does not exist: {default_category_id}")

    existing = db.scalars(select(Product).where(Product.name_key == name_key)).first()
    if existing is not None:
        raise ProductConflictError("name_key is already used by another product")

    product = Product(
        name=name.strip(),
        name_key=name_key,
        default_base_unit=default_base_unit,
        default_category_id=default_category_id,
        is_inventory_target=is_inventory_target,
    )
    db.add(product)
    db.flush()

    created_alias = None
    if initial_alias_name is not None:
        alias_result = create_product_alias(
            db,
            alias_name=initial_alias_name,
            product_id=product.id,
            source=alias_source,
        )
        created_alias = alias_result.alias

    return ProductCreateResult(product=product, created_alias=created_alias)


def create_product_alias(
    db: Session,
    *,
    alias_name: str,
    product_id: int,
    source: str = DEFAULT_ALIAS_SOURCE,
) -> ProductAliasCreateResult:
    alias_key = normalize_product_key(alias_name)
    if alias_key is None:
        raise ValueError("alias_name must not be empty")

    normalized_source = source.strip()
    if normalized_source not in ALLOWED_ALIAS_SOURCES:
        allowed = ", ".join(sorted(ALLOWED_ALIAS_SOURCES))
        raise ValueError(f"source must be one of: {allowed}")

    product = db.get(Product, product_id)
    if product is None:
        raise LookupError(f"product_id does not exist: {product_id}")

    existing = db.scalars(
        select(ProductAlias).where(ProductAlias.alias_key == alias_key)
    ).first()
    if existing is not None:
        if existing.product_id != product_id:
            raise ProductAliasConflictError(
                "alias_key is already linked to another product",
                alias_key=alias_key,
                requested_product_id=product_id,
                existing_product_id=existing.product_id,
            )
        return ProductAliasCreateResult(alias=existing, created=False)

    alias = ProductAlias(
        product_id=product_id,
        alias_name=alias_name.strip(),
        alias_key=alias_key,
        source=normalized_source,
        is_active=True,
    )
    db.add(alias)
    db.flush()
    return ProductAliasCreateResult(alias=alias, created=True)
