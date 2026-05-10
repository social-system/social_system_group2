from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.common.date import format_yyyymmdd
from app.common.date import parse_yyyymmdd
from app.crud.receipts import delete_receipt, get_receipt, list_receipts
from app.db.session import get_db
from app.routes import receipts_create
from app.schemas.receipts_responses import (
    ReceiptDeleteResponse,
    ReceiptItemResponse,
    ReceiptResponse,
    ReceiptSummaryResponse,
)

# レシート関連のAPIをまとめるrouter
router = APIRouter()

router.include_router(receipts_create.router)


@router.get("/receipts", response_model=list[ReceiptSummaryResponse])
def read_receipts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    date_from: int | None = None,
    date_to: int | None = None,
    db: Session = Depends(get_db),
):
    try:
        if date_from is not None:
            parse_yyyymmdd(date_from)
        if date_to is not None:
            parse_yyyymmdd(date_to)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    return [
        ReceiptSummaryResponse(
            id=receipt.id,
            receipt_total=receipt.receipt_total,
            item_count=receipt.item_count,
            date_min=receipt.date_min,
            date_max=receipt.date_max,
        )
        for receipt in list_receipts(
            db,
            skip=skip,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
        )
    ]


@router.delete("/receipts/{receipt_id}", response_model=ReceiptDeleteResponse)
def remove_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
):
    deleted_id = delete_receipt(db, receipt_id)
    if deleted_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="receipt not found",
        )

    db.commit()
    return ReceiptDeleteResponse(deleted=True, id=deleted_id)


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
