from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.product_alias_sources import (
    AUTO_RESOLVE_ALIAS_SOURCES,
    CANDIDATE_ALIAS_SOURCES,
)
from app.receipts.models import Product, ProductAlias
from app.services.product_normalization import normalize_product_key


@dataclass(frozen=True)
class ProductResolutionInput:
    product_id: int | None
    raw_name: str | None
    normalized_name: str | None


@dataclass(frozen=True)
class ProductCandidate:
    product_id: int
    product_name: str
    default_category_id: int | None
    default_base_unit: str
    is_inventory_target: bool
    matched_name: str
    match_source: str


@dataclass(frozen=True)
class ProductResolutionResult:
    product_id: int | None
    product_name: str | None
    normalized_name: str | None
    default_category_id: int | None
    default_base_unit: str | None
    is_inventory_target: bool | None
    resolution_status: str
    resolution_source: str | None
    candidates: list[ProductCandidate]


def _candidate_from_product(
    product: Product,
    *,
    matched_name: str,
    match_source: str,
) -> ProductCandidate:
    return ProductCandidate(
        product_id=product.id,
        product_name=product.name,
        default_category_id=product.default_category_id,
        default_base_unit=product.default_base_unit,
        is_inventory_target=product.is_inventory_target,
        matched_name=matched_name,
        match_source=match_source,
    )


def _resolved_result(product: Product, *, resolution_source: str) -> ProductResolutionResult:
    return ProductResolutionResult(
        product_id=product.id,
        product_name=product.name,
        normalized_name=product.name,
        default_category_id=product.default_category_id,
        default_base_unit=product.default_base_unit,
        is_inventory_target=product.is_inventory_target,
        resolution_status="resolved",
        resolution_source=resolution_source,
        candidates=[],
    )


def _find_alias_product_by_key(db: Session, key: str | None) -> Product | None:
    if key is None:
        return None

    statement = (
        select(Product)
        .join(ProductAlias)
        .where(ProductAlias.alias_key == key)
        .where(ProductAlias.is_active.is_(True))
        .where(ProductAlias.source.in_(AUTO_RESOLVE_ALIAS_SOURCES))
    )
    return db.scalars(statement).first()


def _find_product_by_key(db: Session, key: str | None) -> Product | None:
    if key is None:
        return None

    statement = select(Product).where(Product.name_key == key)
    return db.scalars(statement).first()


def search_product_candidates(
    db: Session,
    *,
    raw_name: str | None = None,
    normalized_name: str | None = None,
    limit: int = 5,
) -> list[ProductCandidate]:
    query_keys = [
        key
        for key in (
            normalize_product_key(normalized_name),
            normalize_product_key(raw_name),
        )
        if key is not None
    ]
    if not query_keys:
        return []

    candidates_by_product_id: dict[int, ProductCandidate] = {}

    products = db.scalars(select(Product).order_by(Product.id)).all()
    for product in products:
        for query_key in query_keys:
            if query_key in product.name_key or product.name_key in query_key:
                candidates_by_product_id[product.id] = _candidate_from_product(
                    product,
                    matched_name=product.name,
                    match_source="product",
                )
                break
        if len(candidates_by_product_id) >= limit:
            return list(candidates_by_product_id.values())

    aliases = db.scalars(
        select(ProductAlias)
        .where(ProductAlias.is_active.is_(True))
        .where(ProductAlias.source.in_(CANDIDATE_ALIAS_SOURCES))
        .order_by(ProductAlias.id)
    ).all()
    for alias in aliases:
        alias_name_key = normalize_product_key(alias.alias_name)
        for query_key in query_keys:
            if (
                query_key in alias.alias_key
                or alias.alias_key in query_key
                or (alias_name_key is not None and query_key in alias_name_key)
                or (alias_name_key is not None and alias_name_key in query_key)
            ):
                candidates_by_product_id.setdefault(
                    alias.product_id,
                    _candidate_from_product(
                        alias.product,
                        matched_name=alias.alias_name,
                        match_source="alias",
                    ),
                )
                break
        if len(candidates_by_product_id) >= limit:
            break

    return list(candidates_by_product_id.values())[:limit]


def resolve_product(
    db: Session,
    request: ProductResolutionInput,
) -> ProductResolutionResult:
    if request.product_id is not None:
        product = db.get(Product, request.product_id)
        if product is None:
            return ProductResolutionResult(
                product_id=None,
                product_name=None,
                normalized_name=None,
                default_category_id=None,
                default_base_unit=None,
                is_inventory_target=None,
                resolution_status="invalid_product_id",
                resolution_source="request_product_id",
                candidates=[],
            )
        return _resolved_result(product, resolution_source="request_product_id")

    raw_name_key = normalize_product_key(request.raw_name)
    normalized_name_key = normalize_product_key(request.normalized_name)

    product = _find_alias_product_by_key(db, raw_name_key)
    if product is not None:
        return _resolved_result(product, resolution_source="raw_name_alias")

    product = _find_alias_product_by_key(db, normalized_name_key)
    if product is not None:
        return _resolved_result(product, resolution_source="normalized_name_alias")

    product = _find_product_by_key(db, normalized_name_key)
    if product is not None:
        return _resolved_result(product, resolution_source="normalized_name_product")

    product = _find_product_by_key(db, raw_name_key)
    if product is not None:
        return _resolved_result(product, resolution_source="raw_name_product")

    candidates = search_product_candidates(
        db,
        raw_name=request.raw_name,
        normalized_name=request.normalized_name,
    )
    return ProductResolutionResult(
        product_id=None,
        product_name=None,
        normalized_name=request.normalized_name,
        default_category_id=None,
        default_base_unit=None,
        is_inventory_target=None,
        resolution_status="unresolved",
        resolution_source="candidate_only" if candidates else "none",
        candidates=candidates,
    )
