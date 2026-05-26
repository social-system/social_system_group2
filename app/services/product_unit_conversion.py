from decimal import Decimal
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.receipts.models import ProductUnitConversion


def normalize_unit(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    return normalized or None


def find_product_unit_conversion(
    db: Session,
    *,
    product_id: int | None,
    from_unit: str | None,
    to_unit: str | None,
) -> ProductUnitConversion | None:
    if product_id is None:
        return None

    normalized_from_unit = normalize_unit(from_unit)
    normalized_to_unit = normalize_unit(to_unit)
    if normalized_from_unit is None or normalized_to_unit is None:
        return None

    conversions = db.scalars(
        select(ProductUnitConversion).where(
            ProductUnitConversion.product_id == product_id
        )
    ).all()
    for conversion in conversions:
        if (
            normalize_unit(conversion.from_unit) == normalized_from_unit
            and normalize_unit(conversion.to_unit) == normalized_to_unit
        ):
            return conversion

    return None


def convert_to_base_quantity(
    db: Session,
    *,
    product_id: int | None,
    purchased_quantity: Decimal | None,
    purchased_unit: str | None,
    base_unit: str | None,
) -> Decimal | None:
    if product_id is None or purchased_quantity is None:
        return None

    normalized_purchased_unit = normalize_unit(purchased_unit)
    normalized_base_unit = normalize_unit(base_unit)
    if normalized_purchased_unit is None or normalized_base_unit is None:
        return None

    if normalized_purchased_unit == normalized_base_unit:
        return purchased_quantity

    conversion = find_product_unit_conversion(
        db,
        product_id=product_id,
        from_unit=purchased_unit,
        to_unit=base_unit,
    )
    if conversion is not None:
        return purchased_quantity * conversion.multiplier

    return None
