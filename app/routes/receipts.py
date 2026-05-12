from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.common.date import format_yyyymmdd, parse_yyyymmdd
from app.crud.receipts import delete_receipt, get_receipt_detail, list_receipts
from app.db.session import get_db
from app.routes import receipts_create
from app.schemas.receipts_responses import (
    DeleteReceiptResponse,
    ReceiptDetailResponse,
    ReceiptItemResponse,
    ReceiptSummaryResponse,
)

router = APIRouter()

router.include_router(receipts_create.router)


@router.get("/receipts", response_model=list[ReceiptSummaryResponse])
def read_receipts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    date_from: int | None = None,
    date_to: int | None = None,
    category_id: int | None = None,
    inventory_only: bool = False,
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
            purchased_at=receipt.purchased_at,
            store_name=receipt.store_name,
            total_amount=receipt.total_amount,
            items_total=receipt.items_total,
            adjustment_amount=receipt.adjustment_amount,
            item_count=receipt.item_count,
        )
        for receipt in list_receipts(
            db,
            skip=skip,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
            category_id=category_id,
            inventory_only=inventory_only,
        )
    ]


@router.delete("/receipts/{receipt_id}", response_model=DeleteReceiptResponse)
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
    return DeleteReceiptResponse(deleted=True, id=deleted_id)


@router.get("/receipts/{receipt_id}", response_model=ReceiptDetailResponse)
def read_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
):
    receipt = get_receipt_detail(db, receipt_id)
    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="receipt not found",
        )

    return ReceiptDetailResponse(
        id=receipt.id,
        purchased_at=format_yyyymmdd(receipt.purchased_at),
        store_name=receipt.store_name,
        total_amount=receipt.total_amount,
        items_total=receipt.items_total,
        adjustment_amount=receipt.adjustment_amount,
        items=[
            ReceiptItemResponse(
                id=item.id,
                raw_name=item.raw_name,
                normalized_name=item.normalized_name,
                product_id=item.product_id,
                category_id=item.category_id,
                purchased_quantity=item.purchased_quantity,
                purchased_unit=item.purchased_unit,
                base_quantity=item.base_quantity,
                base_unit=item.base_unit,
                unit_price=item.unit_price,
                line_total=item.line_total,
                is_inventory_target=item.is_inventory_target,
            )
            for item in receipt.items
        ],
    )
