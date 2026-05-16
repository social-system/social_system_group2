from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReceiptOcrItem(BaseModel):
    raw_name: str | None = None
    normalized_name: str | None = None
    category_name: str | None = None
    purchased_quantity: float | None = Field(default=None, gt=0)
    purchased_unit: str | None = None
    base_quantity: float | None = Field(default=None, gt=0)
    base_unit: str | None = None
    unit_price: int | None = Field(default=None, ge=0)
    line_total: int | None = Field(default=None, ge=0)
    is_inventory_target: bool | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ReceiptOcrResponse(BaseModel):
    status: Literal["needs_confirmation"] = "needs_confirmation"
    store_name: str | None = None
    purchased_at: str | None = None
    total_amount: int | None = Field(default=None, ge=0)
    items: list[ReceiptOcrItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @field_validator("purchased_at")
    @classmethod
    def validate_purchased_at(cls, value: str | None) -> str | None:
        if value is None:
            return value

        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("purchased_at must be in YYYY-MM-DD format") from exc

        return value
