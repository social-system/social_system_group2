from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.products import (
    ProductAliasCreateRequest,
    ProductAliasResponse,
    ProductSearchItem,
    ProductSearchResponse,
)
from app.services.products import (
    ProductAliasConflictError,
    create_product_alias,
    search_products,
)

router = APIRouter(tags=["products"])


@router.get("/products/search", response_model=ProductSearchResponse)
def search_product_master(
    query: str = Query(..., min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    try:
        query_key, items = search_products(db, query=query, limit=limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_query", "message": str(e)},
        )

    return ProductSearchResponse(
        query=query,
        query_key=query_key,
        items=[
            ProductSearchItem(
                product_id=item.product_id,
                name=item.name,
                default_base_unit=item.default_base_unit,
                default_category_id=item.default_category_id,
                is_inventory_target=item.is_inventory_target,
            )
            for item in items
        ],
    )


@router.post("/product-aliases", response_model=ProductAliasResponse)
def post_product_alias(
    payload: ProductAliasCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        result = create_product_alias(
            db,
            alias_name=payload.alias_name,
            product_id=payload.product_id,
            source=payload.source,
        )
        db.commit()
        db.refresh(result.alias)
    except LookupError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "product_not_found", "message": str(e)},
        )
    except ProductAliasConflictError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "alias_conflict", "message": str(e)},
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_alias", "message": str(e)},
        )
    except Exception:
        db.rollback()
        raise

    return ProductAliasResponse(
        id=result.alias.id,
        alias_name=result.alias.alias_name,
        alias_key=result.alias.alias_key,
        product_id=result.alias.product_id,
        product_name=result.alias.product.name,
        source=result.alias.source,
        created=result.created,
    )
