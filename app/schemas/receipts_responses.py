from pydantic import BaseModel


class ReceiptItemResponse(BaseModel):
    id: int
    item: str
    num: int
    amount: int
    total: int
    date: int
    ingredients: int


class ReceiptResponse(BaseModel):
    id: int
    receipt_total: int
    items: list[ReceiptItemResponse]


class ReceiptSummaryResponse(BaseModel):
    id: int
    receipt_total: int
    item_count: int
    date_min: int
    date_max: int
