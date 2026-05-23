from sqlalchemy.orm import Session

from app.common.date import parse_yyyymmdd
from app.receipts.models import AccountingCategory, Product, Receipt, ReceiptItem
from app.schemas.receipts_requests import ReceiptCreate


def _get_referenced_products(db: Session, data: ReceiptCreate) -> dict[int, Product]:
    product_ids = {item.product_id for item in data.items if item.product_id is not None}
    products: dict[int, Product] = {}

    for product_id in product_ids:
        product = db.get(Product, product_id)
        if product is None:
            raise ValueError(f"product_id does not exist: {product_id}")
        products[product_id] = product

    return products


def _validate_category_ids(db: Session, data: ReceiptCreate) -> None:
    category_ids = {item.category_id for item in data.items if item.category_id is not None}
    for category_id in category_ids:
        if db.get(AccountingCategory, category_id) is None:
            raise ValueError(f"category_id does not exist: {category_id}")


def create_receipt(db: Session, data: ReceiptCreate) -> Receipt:
    products = _get_referenced_products(db, data)
    _validate_category_ids(db, data)

    items_total = sum(item.line_total for item in data.items)
    adjustment_amount = data.total_amount - items_total

    receipt = Receipt(
        purchased_at=parse_yyyymmdd(data.purchased_at),
        store_name=data.store_name,
        total_amount=data.total_amount,
        items_total=items_total,
        adjustment_amount=adjustment_amount,
    )

    for item_data in data.items:
        product = products.get(item_data.product_id) if item_data.product_id is not None else None
        normalized_name = item_data.normalized_name
        category_id = item_data.category_id
        if product is not None:
            normalized_name = normalized_name or product.name
            category_id = category_id or product.default_category_id

        receipt.items.append(
            ReceiptItem(
                product_id=item_data.product_id,
                category_id=category_id,
                raw_name=item_data.raw_name,
                normalized_name=normalized_name,
                purchased_quantity=item_data.purchased_quantity,
                purchased_unit=item_data.purchased_unit,
                base_quantity=item_data.base_quantity,
                base_unit=item_data.base_unit,
                unit_price=item_data.unit_price,
                line_total=item_data.line_total,
                is_inventory_target=item_data.is_inventory_target,
            )
        )

    db.add(receipt)
    db.flush()
    return receipt
