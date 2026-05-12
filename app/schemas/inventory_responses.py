from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer


def _format_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return f"{value:.2f}"


class InventoryReceiptApplyItemResponse(BaseModel):
    receipt_item_id: int
    product_id: int | None = None
    product_name: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    batch_id: int | None = None
    status: str
    reason: str | None = None

    @field_serializer("quantity")
    def serialize_quantity(self, value: Decimal | None) -> str | None:
        return _format_decimal(value)


class InventoryReceiptApplyResponse(BaseModel):
    receipt_id: int
    operation_id: int | None
    applied_count: int
    skipped_count: int
    items: list[InventoryReceiptApplyItemResponse]


class InventoryBalanceItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: Decimal
    unit: str
    nearest_expires_at: date | None
    batch_count: int

    @field_serializer("quantity")
    def serialize_quantity(self, value: Decimal) -> str:
        return _format_decimal(value) or "0.00"


class InventoryBalanceListResponse(BaseModel):
    items: list[InventoryBalanceItemResponse]


class InventoryBatchResponse(BaseModel):
    batch_id: int
    product_id: int
    product_name: str
    initial_quantity: Decimal
    current_quantity: Decimal
    unit: str
    location_id: int | None
    location_name: str | None
    purchased_at: date | None
    expires_at: date | None
    status: str
    receipt_item_id: int | None

    @field_serializer("initial_quantity", "current_quantity")
    def serialize_decimal(self, value: Decimal) -> str:
        return _format_decimal(value) or "0.00"


class InventoryBatchListResponse(BaseModel):
    items: list[InventoryBatchResponse]


class InventoryMovementResult(BaseModel):
    movement_id: int
    batch_id: int
    quantity_delta: Decimal
    remaining_quantity: Decimal

    @field_serializer("quantity_delta", "remaining_quantity")
    def serialize_decimal(self, value: Decimal) -> str:
        return _format_decimal(value) or "0.00"


class InventoryMovementCreateResponse(BaseModel):
    operation_id: int
    movement_type: str
    product_id: int
    product_name: str
    requested_quantity: Decimal
    unit: str
    movements: list[InventoryMovementResult]

    @field_serializer("requested_quantity")
    def serialize_requested_quantity(self, value: Decimal) -> str:
        return _format_decimal(value) or "0.00"


class InventoryMovementResponse(BaseModel):
    movement_id: int
    operation_id: int
    batch_id: int | None
    product_id: int
    product_name: str
    movement_type: str
    quantity_delta: Decimal
    unit: str
    reason: str | None
    occurred_at: datetime

    @field_serializer("quantity_delta")
    def serialize_quantity_delta(self, value: Decimal) -> str:
        return _format_decimal(value) or "0.00"


class InventoryMovementListResponse(BaseModel):
    items: list[InventoryMovementResponse]
