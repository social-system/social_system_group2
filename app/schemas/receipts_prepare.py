from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ReceiptPrepareItemRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    raw_name: str | None = None
    normalized_name: str | None = None
    product_id: int | None = None
    category_id: int | None = None
    category_name: str | None = None
    purchased_quantity: Decimal | None = None
    purchased_unit: str | None = None
    base_quantity: Decimal | None = None
    base_unit: str | None = None
    unit_price: int | None = None
    line_total: int | None = None
    is_inventory_target: bool | None = None
    confidence: float | None = None
    warnings: list[str] = Field(default_factory=list)


class ReceiptPrepareRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str | None = None
    store_name: str | None = None
    purchased_at: int | str | None = None
    total_amount: int | None = None
    items: list[ReceiptPrepareItemRequest] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PreparedReceiptItem(BaseModel):
    raw_name: str | None
    normalized_name: str | None
    product_id: int | None
    category_id: int | None
    purchased_quantity: Decimal | None
    purchased_unit: str | None
    base_quantity: Decimal | None
    base_unit: str | None
    unit_price: int | None
    line_total: int | None
    is_inventory_target: bool | None

    @field_serializer("purchased_quantity", "base_quantity")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        if value is None:
            return None
        return f"{value:.2f}"


class PreparedReceipt(BaseModel):
    store_name: str | None
    purchased_at: int | None
    total_amount: int | None
    items: list[PreparedReceiptItem]


class PreparedProductCandidate(BaseModel):
    product_id: int
    name: str
    default_category_id: int | None
    default_base_unit: str
    is_inventory_target: bool
    matched_name: str
    match_source: str


class PreparedItemResolution(BaseModel):
    index: int
    resolution_status: str
    resolution_source: str | None
    product_id: int | None
    product_name: str | None
    product_candidates: list[PreparedProductCandidate]
    issues: list[str]


class ReceiptPrepareResponse(BaseModel):
    receipt: PreparedReceipt
    item_resolutions: list[PreparedItemResolution]
    unresolved_items: list[PreparedItemResolution]
    warnings: list[str]
    validation_issues: list[str]
