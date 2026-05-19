from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.date import format_yyyymmdd
from app.receipts.models import Product, Receipt, ReceiptItem


@dataclass(frozen=True)
class CheapestPriceItem:
    store_name: str
    price_per_base_unit: Decimal
    line_total: int
    base_quantity: Decimal
    base_unit: str
    purchased_at: int
    receipt_item_id: int


@dataclass(frozen=True)
class CheapestPriceResult:
    product_id: int
    product_name: str
    period_days: int
    cheapest: CheapestPriceItem | None


def get_cheapest_price(
    db: Session,
    *,
    product_id: int,
    period_days: int = 90,
    today: date | None = None,
) -> CheapestPriceResult | None:
    product = db.get(Product, product_id)
    if product is None:
        return None

    end_date = today or date.today()
    start_date = end_date - timedelta(days=period_days)

    statement = (
        select(ReceiptItem, Receipt)
        .join(Receipt, ReceiptItem.receipt_id == Receipt.id)
        .where(ReceiptItem.product_id == product_id)
        .where(ReceiptItem.base_quantity.is_not(None))
        .where(ReceiptItem.base_quantity > 0)
        .where(ReceiptItem.base_unit.is_not(None))
        .where(Receipt.store_name.is_not(None))
        .where(Receipt.purchased_at >= start_date)
        .where(Receipt.purchased_at <= end_date)
        .order_by(ReceiptItem.id)
    )
    candidates = db.execute(statement).all()

    if not candidates:
        return CheapestPriceResult(
            product_id=product.id,
            product_name=product.name,
            period_days=period_days,
            cheapest=None,
        )

    item, receipt = min(
        candidates,
        key=lambda row: (
            Decimal(row[0].line_total) / row[0].base_quantity,
            row[0].id,
        ),
    )

    return CheapestPriceResult(
        product_id=product.id,
        product_name=product.name,
        period_days=period_days,
        cheapest=CheapestPriceItem(
            store_name=receipt.store_name,
            price_per_base_unit=Decimal(item.line_total) / item.base_quantity,
            line_total=item.line_total,
            base_quantity=item.base_quantity,
            base_unit=item.base_unit,
            purchased_at=format_yyyymmdd(receipt.purchased_at),
            receipt_item_id=item.id,
        ),
    )
