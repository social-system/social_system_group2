from pydantic import BaseModel, Field


class ReceiptItemCreate(BaseModel):
    item: str = Field(min_length=1, max_length=255)
    num: int = Field(ge=1)
    amount: int = Field(ge=0)
    total: int = Field(ge=0)
    date: int
    ingredients: int


class ReceiptCreate(BaseModel):
    receipt_total: int = Field(ge=0)  # 合計金額0以上
    items: list[ReceiptItemCreate]  # 配列/min_lengthなし(空レシート許可)
