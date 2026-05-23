from pydantic import BaseModel, Field


class ProductSearchItem(BaseModel):
    product_id: int
    name: str
    default_base_unit: str
    default_category_id: int | None
    is_inventory_target: bool


class ProductSearchResponse(BaseModel):
    query: str
    query_key: str
    items: list[ProductSearchItem]


class ProductAliasCreateRequest(BaseModel):
    alias_name: str = Field(min_length=1, max_length=255)
    product_id: int = Field(ge=1)
    source: str = Field(default="user_confirmed", min_length=1, max_length=50)


class ProductAliasResponse(BaseModel):
    id: int
    alias_name: str
    alias_key: str
    product_id: int
    product_name: str
    source: str
    created: bool
