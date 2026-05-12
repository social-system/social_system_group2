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

DB API に送る前に、フロントエンド確認画面で必要項目を埋める。
