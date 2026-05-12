from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.common.date import format_yyyymmdd, parse_yyyymmdd
from app.receipts.models import Receipt, ReceiptItem


@dataclass(frozen=True)
class ReceiptSummary:
    id: int
    purchased_at: int
    store_name: str | None
    total_amount: int
    items_total: int
    adjustment_amount: int
    item_count: int


def get_receipt_detail(db: Session, receipt_id: int) -> Receipt | None:
    statement = (
        select(Receipt)
        .options(selectinload(Receipt.items))
        .where(Receipt.id == receipt_id)
    )
    return db.scalars(statement).first()


def list_receipts(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    date_from: int | None = None,
    date_to: int | None = None,
    category_id: int | None = None,
    inventory_only: bool = False,
) -> list[ReceiptSummary]:
    statement = select(Receipt).options(selectinload(Receipt.items)).order_by(Receipt.id)

    if date_from is not None:
        statement = statement.where(Receipt.purchased_at >= parse_yyyymmdd(date_from))
    if date_to is not None:
        statement = statement.where(Receipt.purchased_at <= parse_yyyymmdd(date_to))

    if category_id is not None or inventory_only:
        statement = statement.join(Receipt.items).distinct()
        if category_id is not None:
            statement = statement.where(ReceiptItem.category_id == category_id)
        if inventory_only:
            statement = statement.where(ReceiptItem.is_inventory_target.is_(True))

    statement = statement.offset(skip).limit(limit)
    receipts = db.scalars(statement).all()

    return [
        ReceiptSummary(
            id=receipt.id,
            purchased_at=format_yyyymmdd(receipt.purchased_at),
            store_name=receipt.store_name,
            total_amount=receipt.total_amount,
            items_total=receipt.items_total,
            adjustment_amount=receipt.adjustment_amount,
            item_count=len(receipt.items),
        )
        for receipt in receipts
    ]


def delete_receipt(db: Session, receipt_id: int) -> int | None:
    receipt = get_receipt_detail(db, receipt_id)
    if receipt is None:
        return None

    deleted_id = receipt.id
    db.delete(receipt)
    db.flush()
    return deleted_id
