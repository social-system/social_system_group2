from pydantic import BaseModel, Field

from app.common.product_alias_sources import DEFAULT_ALIAS_SOURCE


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


class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    default_base_unit: str = Field(min_length=1, max_length=50)
    is_inventory_target: bool
    default_category_id: int | None = Field(default=None, ge=1)
    initial_alias_name: str | None = Field(default=None, max_length=255)
    alias_source: str = Field(default=DEFAULT_ALIAS_SOURCE, min_length=1, max_length=50)


class ProductCreatedAliasResponse(BaseModel):
    id: int
    alias_name: str
    alias_key: str
    product_id: int
    source: str


class ProductCreateResponse(BaseModel):
    id: int
    name: str
    name_key: str
    default_base_unit: str
    default_category_id: int | None
    is_inventory_target: bool
    created_alias: ProductCreatedAliasResponse | None


class ProductAliasCreateRequest(BaseModel):
    alias_name: str = Field(min_length=1, max_length=255)
    product_id: int = Field(ge=1)
    source: str = Field(default=DEFAULT_ALIAS_SOURCE, min_length=1, max_length=50)


class ProductAliasResponse(BaseModel):
    id: int
    alias_name: str
    alias_key: str
    product_id: int
    product_name: str
    source: str
    created: bool
