from __future__ import annotations

from decimal import Decimal
from typing import Literal, TypedDict


SampleSource = Literal["provided_example", "real_receipt", "test_seed"]


class ReceiptVariationSample(TypedDict):
    sample_source: SampleSource
    raw_name: str
    normalized_name: str | None
    purchased_quantity: Decimal | None
    purchased_unit: str | None
    expected_product_name: str
    expected_base_quantity: Decimal | None
    expected_base_unit: str | None
    auto_resolve_allowed: bool
    needs_user_confirmation: bool
    reason: str


RECEIPT_VARIATION_SAMPLES: list[ReceiptVariationSample] = [
    {
        "sample_source": "provided_example",
        "raw_name": "タマゴ",
        "normalized_name": None,
        "purchased_quantity": None,
        "purchased_unit": None,
        "expected_product_name": "卵",
        "expected_base_quantity": None,
        "expected_base_unit": None,
        "auto_resolve_allowed": True,
        "needs_user_confirmation": False,
        "reason": "信頼できるactive aliasが卵に完全一致する場合だけ自動解決できる商品名表記揺れ。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "卵",
        "normalized_name": None,
        "purchased_quantity": None,
        "purchased_unit": None,
        "expected_product_name": "卵",
        "expected_base_quantity": None,
        "expected_base_unit": None,
        "auto_resolve_allowed": True,
        "needs_user_confirmation": False,
        "reason": "products.name_keyに完全一致するため自動解決できる。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "たまご",
        "normalized_name": None,
        "purchased_quantity": None,
        "purchased_unit": None,
        "expected_product_name": "卵",
        "expected_base_quantity": None,
        "expected_base_unit": None,
        "auto_resolve_allowed": True,
        "needs_user_confirmation": False,
        "reason": "信頼できるactive aliasが卵に完全一致する場合だけ自動解決できる商品名表記揺れ。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "玉子",
        "normalized_name": None,
        "purchased_quantity": None,
        "purchased_unit": None,
        "expected_product_name": "卵",
        "expected_base_quantity": None,
        "expected_base_unit": None,
        "auto_resolve_allowed": True,
        "needs_user_confirmation": False,
        "reason": "信頼できるactive aliasが卵に完全一致する場合だけ自動解決できる商品名表記揺れ。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "タマゴM 10コ",
        "normalized_name": None,
        "purchased_quantity": Decimal("10"),
        "purchased_unit": "個",
        "expected_product_name": "卵",
        "expected_base_quantity": None,
        "expected_base_unit": None,
        "auto_resolve_allowed": False,
        "needs_user_confirmation": True,
        "reason": "商品名にサイズと数量が混在しており、信頼済みaliasなしでは候補提示に留める。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "卵 1パック",
        "normalized_name": "卵",
        "purchased_quantity": Decimal("1"),
        "purchased_unit": "パック",
        "expected_product_name": "卵",
        "expected_base_quantity": Decimal("10"),
        "expected_base_unit": "個",
        "auto_resolve_allowed": True,
        "needs_user_confirmation": False,
        "reason": "卵を解決後、商品別変換 1パック=10個 があればbase_quantityを補完できる。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "卵 2個",
        "normalized_name": "卵",
        "purchased_quantity": Decimal("2"),
        "purchased_unit": "個",
        "expected_product_name": "卵",
        "expected_base_quantity": Decimal("2"),
        "expected_base_unit": "個",
        "auto_resolve_allowed": True,
        "needs_user_confirmation": False,
        "reason": "卵を解決後、購入単位と標準単位が同じなのでそのまま補完できる。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "牛乳 1本",
        "normalized_name": "牛乳",
        "purchased_quantity": Decimal("1"),
        "purchased_unit": "本",
        "expected_product_name": "牛乳",
        "expected_base_quantity": Decimal("1000"),
        "expected_base_unit": "ml",
        "auto_resolve_allowed": True,
        "needs_user_confirmation": False,
        "reason": "牛乳を解決後、商品別変換 1本=1000ml があればbase_quantityを補完できる。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "牛乳 1000ml",
        "normalized_name": "牛乳",
        "purchased_quantity": Decimal("1000"),
        "purchased_unit": "ml",
        "expected_product_name": "牛乳",
        "expected_base_quantity": Decimal("1000"),
        "expected_base_unit": "ml",
        "auto_resolve_allowed": True,
        "needs_user_confirmation": False,
        "reason": "牛乳を解決後、購入単位と標準単位が同じなのでそのまま補完できる。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "牛乳 1L",
        "normalized_name": "牛乳",
        "purchased_quantity": Decimal("1"),
        "purchased_unit": "L",
        "expected_product_name": "牛乳",
        "expected_base_quantity": Decimal("1000"),
        "expected_base_unit": "ml",
        "auto_resolve_allowed": True,
        "needs_user_confirmation": False,
        "reason": "牛乳を解決後、Lからmlへの変換があればbase_quantityを補完できる。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "米 1kg",
        "normalized_name": "米",
        "purchased_quantity": Decimal("1"),
        "purchased_unit": "kg",
        "expected_product_name": "米",
        "expected_base_quantity": Decimal("1000"),
        "expected_base_unit": "g",
        "auto_resolve_allowed": True,
        "needs_user_confirmation": False,
        "reason": "米を解決後、商品別変換 1kg=1000g があればbase_quantityを補完できる。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "豚肉 100g",
        "normalized_name": "豚肉",
        "purchased_quantity": Decimal("100"),
        "purchased_unit": "g",
        "expected_product_name": "豚肉",
        "expected_base_quantity": Decimal("100"),
        "expected_base_unit": "g",
        "auto_resolve_allowed": True,
        "needs_user_confirmation": False,
        "reason": "豚肉を解決後、購入単位と標準単位が同じなのでそのまま補完できる。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "トマト 2個",
        "normalized_name": "トマト",
        "purchased_quantity": Decimal("2"),
        "purchased_unit": "個",
        "expected_product_name": "トマト",
        "expected_base_quantity": None,
        "expected_base_unit": None,
        "auto_resolve_allowed": True,
        "needs_user_confirmation": True,
        "reason": "トマトは個数だけではg換算できないため、商品解決後もbase_quantityは自動補完しない。",
    },
    {
        "sample_source": "provided_example",
        "raw_name": "肉 1パック",
        "normalized_name": "肉",
        "purchased_quantity": Decimal("1"),
        "purchased_unit": "パック",
        "expected_product_name": "肉",
        "expected_base_quantity": None,
        "expected_base_unit": None,
        "auto_resolve_allowed": True,
        "needs_user_confirmation": True,
        "reason": "肉の1パックは商品や店舗で重量が変わるため、g換算を推測せずユーザー確認に回す。",
    },
]


PROVIDED_EXAMPLE_SAMPLES = [
    sample for sample in RECEIPT_VARIATION_SAMPLES if sample["sample_source"] == "provided_example"
]

REAL_RECEIPT_SAMPLES = [
    sample for sample in RECEIPT_VARIATION_SAMPLES if sample["sample_source"] == "real_receipt"
]

PRODUCT_NAME_VARIATION_SAMPLES = [
    sample
    for sample in PROVIDED_EXAMPLE_SAMPLES
    if sample["raw_name"] in {"タマゴ", "卵", "たまご", "玉子"}
]
