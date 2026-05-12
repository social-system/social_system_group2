from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


def _format_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return f"{value:.2f}"


class ReceiptItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    raw_name: str
    normalized_name: str | None
    product_id: int | None
    category_id: int | None
    purchased_quantity: Decimal
    purchased_unit: str | None
    base_quantity: Decimal | None
    base_unit: str | None
    unit_price: int | None
    line_total: int
    is_inventory_target: bool

    @field_serializer("purchased_quantity", "base_quantity")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        return _format_decimal(value)


class ReceiptSummaryResponse(BaseModel):
    id: int
    purchased_at: int
    store_name: str | None
    total_amount: int
    items_total: int
    adjustment_amount: int
    item_count: int


class ReceiptDetailResponse(BaseModel):
    id: int
    purchased_at: int
    store_name: str | None
    total_amount: int
    items_total: int
    adjustment_amount: int
    items: list[ReceiptItemResponse]


class DeleteReceiptResponse(BaseModel):
    deleted: bool
    id: int
