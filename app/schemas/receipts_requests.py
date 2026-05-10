from pydantic import BaseModel, Field
from pydantic import field_validator

from app.common.date import parse_yyyymmdd


class ReceiptItemCreate(BaseModel):
    item: str = Field(min_length=1, max_length=255)
    num: int = Field(ge=1)
    amount: int = Field(ge=0)
    total: int = Field(ge=0)
    date: int
    ingredients: int

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: int) -> int:
        parse_yyyymmdd(value)
        return value


class ReceiptCreate(BaseModel):
    receipt_total: int = Field(ge=0)  # 合計金額0以上
    items: list[ReceiptItemCreate] = Field(min_length=1)
