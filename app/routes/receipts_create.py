from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.date import format_yyyymmdd
from app.crud.receipts_create import create_receipt
from app.db.session import get_db
from app.schemas.receipts_requests import ReceiptCreate
from app.schemas.receipts_responses import ReceiptSummaryResponse

router = APIRouter(
    prefix="/receipts",
    tags=["receipts"],
)


@router.post(
    "",
    response_model=ReceiptSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_receipt(
    payload: ReceiptCreate,
    db: Session = Depends(get_db),
):
    try:
        receipt = create_receipt(db, payload)
        db.commit()
        db.refresh(receipt)
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_receipt", "message": str(e)},
        )
    except Exception:
        db.rollback()
        raise

    return ReceiptSummaryResponse(
        id=receipt.id,
        purchased_at=format_yyyymmdd(receipt.purchased_at),
        store_name=receipt.store_name,
        total_amount=receipt.total_amount,
        items_total=receipt.items_total,
        adjustment_amount=receipt.adjustment_amount,
        item_count=len(receipt.items),
    )
