from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.receipts.models import Receipt


def get_receipt(db: Session, receipt_id: int) -> Receipt | None:
    statement = (
        select(Receipt)
        .options(selectinload(Receipt.items))
        .where(Receipt.id == receipt_id)
    )
    return db.scalars(statement).first()
