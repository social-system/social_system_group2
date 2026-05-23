from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.date import parse_yyyymmdd


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class ReceiptItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_name: str = Field(min_length=1, max_length=255)
    normalized_name: str | None = Field(default=None, max_length=255)
    product_id: int | None = None
    category_id: int | None = None
    purchased_quantity: Decimal = Field(gt=0)
    purchased_unit: str | None = Field(default=None, max_length=50)
    base_quantity: Decimal | None = None
    base_unit: str | None = Field(default=None, max_length=50)
    unit_price: int | None = Field(default=None, ge=0)
    line_total: int = Field(ge=0)
    is_inventory_target: bool

    @field_validator("raw_name")
    @classmethod
    def validate_raw_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("raw_name must not be empty")
        return stripped

    @field_validator("normalized_name", "purchased_unit", "base_unit")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _blank_to_none(value)

    @model_validator(mode="after")
    def validate_inventory_fields(self) -> "ReceiptItemCreate":
        if not self.is_inventory_target:
            return self

        if self.normalized_name is None and self.product_id is None:
            raise ValueError("normalized_name is required for inventory target items")
        if self.base_quantity is None:
            raise ValueError("base_quantity is required for inventory target items")
        if self.base_unit is None:
            raise ValueError("base_unit is required for inventory target items")

        return self


class ReceiptCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purchased_at: int
    store_name: str | None = Field(default=None, max_length=255)
    total_amount: int = Field(ge=0)
    items: list[ReceiptItemCreate] = Field(min_length=1)

    @field_validator("purchased_at")
    @classmethod
    def validate_purchased_at(cls, value: int) -> int:
        parse_yyyymmdd(value)
        return value

    @field_validator("store_name")
    @classmethod
    def normalize_store_name(cls, value: str | None) -> str | None:
        return _blank_to_none(value)
