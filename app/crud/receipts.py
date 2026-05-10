from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.common.date import format_yyyymmdd, parse_yyyymmdd
from app.receipts.models import Receipt
from app.receipts.models import ReceiptItem


@dataclass(frozen=True)
class ReceiptSummary:
    id: int
    receipt_total: int
    item_count: int
    date_min: int
    date_max: int


def get_receipt(db: Session, receipt_id: int) -> Receipt | None:
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
) -> list[ReceiptSummary]:
    statement = (
        select(
            Receipt.id,
            Receipt.receipt_total,
            func.count(ReceiptItem.id).label("item_count"),
            func.min(ReceiptItem.date).label("date_min"),
            func.max(ReceiptItem.date).label("date_max"),
        )
        .join(Receipt.items)
        .group_by(Receipt.id, Receipt.receipt_total)
        .order_by(Receipt.id)
        .offset(skip)
        .limit(limit)
    )

    if date_from is not None:
        statement = statement.where(ReceiptItem.date >= parse_yyyymmdd(date_from))
    if date_to is not None:
        statement = statement.where(ReceiptItem.date <= parse_yyyymmdd(date_to))

    return [
        ReceiptSummary(
            id=row.id,
            receipt_total=row.receipt_total,
            item_count=row.item_count,
            date_min=format_yyyymmdd(row.date_min),
            date_max=format_yyyymmdd(row.date_max),
        )
        for row in db.execute(statement)
    ]
