from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud.prices import get_cheapest_price
from app.db.session import get_db
from app.schemas.prices_responses import CheapestPriceItemResponse, CheapestPriceResponse

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/cheapest", response_model=CheapestPriceResponse)
def read_cheapest_price(
    product_id: int = Query(..., ge=1),
    period_days: int = Query(default=90, ge=1),
    db: Session = Depends(get_db),
):
    result = get_cheapest_price(
        db,
        product_id=product_id,
        period_days=period_days,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="product not found",
        )

    cheapest = None
    if result.cheapest is not None:
        cheapest = CheapestPriceItemResponse(
            store_name=result.cheapest.store_name,
            price_per_base_unit=float(result.cheapest.price_per_base_unit),
            line_total=result.cheapest.line_total,
            base_quantity=result.cheapest.base_quantity,
            base_unit=result.cheapest.base_unit,
            purchased_at=result.cheapest.purchased_at,
            receipt_item_id=result.cheapest.receipt_item_id,
        )

    return CheapestPriceResponse(
        product_id=result.product_id,
        product_name=result.product_name,
        period_days=result.period_days,
        cheapest=cheapest,
    )
