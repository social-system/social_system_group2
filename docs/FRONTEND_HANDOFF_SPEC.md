# Frontend Handoff Specification

## Purpose

The OCR API returns provisional candidate data for a frontend confirmation screen.

The frontend must allow the user to review, correct, remove, and add item rows before sending confirmed data to the database API.

## OCR response is not final data

The following fields are candidates only:

- `store_name`
- `purchased_at`
- `total_amount`
- `raw_name`
- `normalized_name`
- `category_name`
- `purchased_quantity`
- `purchased_unit`
- `base_quantity`
- `base_unit`
- `unit_price`
- `line_total`
- `is_inventory_target`

The frontend must not treat OCR output as already confirmed.

## Suggested confirmation UI behavior

For each receipt:

- Show store name
- Show purchase date
- Show total amount
- Show all item rows
- Show warning messages
- Allow correction of all item fields
- Highlight rows with warnings
- Highlight rows with missing important fields

## Fields that should be required before DB registration

For confirmed database registration, the frontend or database API should require:

- `purchased_at`
- `total_amount`
- item `raw_name`
- item `line_total`
- item `is_inventory_target`

For inventory target items, confirmation should also require:

- `normalized_name`
- `purchased_quantity`
- `purchased_unit`
- `base_quantity`
- `base_unit`

The OCR API does not enforce final DB rules. It only returns candidates.

## ID fields

The OCR API must not return:

- `product_id`
- `category_id`
- `receipt_id`
- `receipt_item_id`

Those IDs belong to database-side master data and confirmed records.

## Warning examples

Top-level warnings:

```json
[
  "購入日を読み取れませんでした",
  "合計金額と明細合計が一致しない可能性があります"
]
```

Item warnings:

```json
[
  "商品名の読み取り精度が低い可能性があります",
  "パックから個数への変換を確認してください"
]
```

## Final handoff to database API

The frontend or another integration layer should convert confirmed OCR response into the database API request.

OCR response uses names such as `category_name` and `normalized_name`.
The database API may resolve these into IDs after confirmation.

This OCR project does not implement that conversion.
