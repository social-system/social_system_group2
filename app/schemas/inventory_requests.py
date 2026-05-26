from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def _normalize_optional_key(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class InventoryReceiptApplyRequest(BaseModel):
    default_location_id: int | None = None
    expires_at_by_receipt_item_id: dict[int, date] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=255)

    @field_validator("idempotency_key")
    @classmethod
    def normalize_idempotency_key(cls, value: str | None) -> str | None:
        return _normalize_optional_key(value)


class InventoryMovementCreateRequest(BaseModel):
    product_id: int
    movement_type: Literal["consume", "dispose", "adjust"]
    quantity: Decimal
    unit: str = Field(min_length=1, max_length=50)
    batch_id: int | None = None
    location_id: int | None = None
    reason: str | None = Field(default=None, max_length=255)
    occurred_at: datetime | None = None
    idempotency_key: str | None = Field(default=None, max_length=255)

    @field_validator("idempotency_key")
    @classmethod
    def normalize_idempotency_key(cls, value: str | None) -> str | None:
        return _normalize_optional_key(value)

    @field_validator("unit")
    @classmethod
    def normalize_unit(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("unit must not be empty")
        return stripped

    @model_validator(mode="after")
    def validate_quantity(self) -> "InventoryMovementCreateRequest":
        if self.quantity == 0:
            raise ValueError("quantity must not be zero")
        if self.movement_type in {"consume", "dispose"} and self.quantity <= 0:
            raise ValueError("quantity must be greater than 0")
        return self
