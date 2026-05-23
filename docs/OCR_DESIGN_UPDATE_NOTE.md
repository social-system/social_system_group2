# OCR_DESIGN_UPDATE_NOTE.md

OCR リポジトリ側の `DESIGN.md` を更新する場合は、古いレスポンス項目をそのまま使わない。

廃止する古い項目:

```text
item
num
amount
total
date
ingredients
receipt_total
```

DB API と合わせる新しい項目:

```text
raw_name
normalized_name
purchased_quantity
purchased_unit
base_quantity
base_unit
unit_price
line_total
purchased_at
total_amount
is_inventory_target
```

ただし、OCR API は仮データを返すため、不明値は `null` を許す。

OCR API は `product_id` や `category_id` を返さない。OCR の `normalized_name` は商品名候補であり、DB の正式な `products.name` と一致する保証はない。

DB API に送る前に、まず `POST /receipts/prepare` を呼び出す。DB 側は `products.name_key` と `product_aliases.alias_key` で `product_id` を解決し、解決できない商品は `unresolved_items` として返す。

ユーザーが未解決商品を確認した場合は、`POST /product-aliases` で `product_aliases` に学習させる。次回以降の prepare flow では、その alias が表記揺れを吸収する。

最安店表示では `product_id` と `base_quantity` を使い、`line_total / base_quantity` で共通単位あたり価格を比較する。`product_id` 未解決の商品は購入履歴として保存できるが、最安店検索の対象にはならない。
