from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.date import format_yyyymmdd
from app.crud.receipts import get_receipt
from app.db.session import get_db
from app.routes import receipts_create
from app.schemas.receipts_responses import ReceiptItemResponse, ReceiptResponse

# レシート関連のAPIをまとめるrouter
router = APIRouter()

router.include_router(receipts_create.router)


@router.get("/receipts/{receipt_id}", response_model=ReceiptResponse)
def read_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
):
    receipt = get_receipt(db, receipt_id)
    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="receipt not found",
        )

    return ReceiptResponse(
        id=receipt.id,
        receipt_total=receipt.receipt_total,
        items=[
            ReceiptItemResponse(
                id=item.id,
                item=item.item,
                num=item.num,
                amount=item.amount,
                total=item.total,
                date=format_yyyymmdd(item.date),
                ingredients=item.ingredients,
            )
            for item in receipt.items
        ],
    )
