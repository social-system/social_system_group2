from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.operations import (
    ReceiptPrepareMetricsResponse,
    TopUnresolvedRawNameResponse,
)
from app.services.operations_metrics import get_receipt_prepare_metrics

router = APIRouter(tags=["operations"])


@router.get(
    "/operations/receipt-prepare-metrics",
    response_model=ReceiptPrepareMetricsResponse,
)
def read_receipt_prepare_metrics(
    top_limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    metrics = get_receipt_prepare_metrics(db, top_limit=top_limit)
    return ReceiptPrepareMetricsResponse(
        prepare_count=metrics.prepare_count,
        total_item_count=metrics.total_item_count,
        unresolved_item_count=metrics.unresolved_item_count,
        unresolved_rate=metrics.unresolved_rate,
        alias_count=metrics.alias_count,
        active_alias_count=metrics.active_alias_count,
        alias_conflict_count=metrics.alias_conflict_count,
        inventory_base_quantity_missing_count=metrics.inventory_base_quantity_missing_count,
        top_unresolved_raw_names=[
            TopUnresolvedRawNameResponse(
                raw_name=item.raw_name,
                raw_name_key=item.raw_name_key,
                count=item.count,
            )
            for item in metrics.top_unresolved_raw_names
        ],
    )
