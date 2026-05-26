from pydantic import BaseModel


class TopUnresolvedRawNameResponse(BaseModel):
    raw_name: str
    raw_name_key: str
    count: int


class ReceiptPrepareMetricsResponse(BaseModel):
    prepare_count: int
    total_item_count: int
    unresolved_item_count: int
    unresolved_rate: float
    alias_count: int
    active_alias_count: int
    alias_conflict_count: int
    inventory_base_quantity_missing_count: int
    top_unresolved_raw_names: list[TopUnresolvedRawNameResponse]
