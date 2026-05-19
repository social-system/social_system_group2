from decimal import Decimal

from pydantic import BaseModel, field_serializer


def _format_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return f"{value:.2f}"


class CheapestPriceItemResponse(BaseModel):
    store_name: str
    price_per_base_unit: float
    line_total: int
    base_quantity: Decimal
    base_unit: str
    purchased_at: int
    receipt_item_id: int

    @field_serializer("base_quantity")
    def serialize_base_quantity(self, value: Decimal) -> str:
        return _format_decimal(value) or "0.00"


class CheapestPriceResponse(BaseModel):
    product_id: int
    product_name: str
    period_days: int
    cheapest: CheapestPriceItemResponse | None
