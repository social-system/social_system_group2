# API_SPEC.md

## 前提

この API は、ユーザー確認済みのレシートデータだけを受け取る。

OCR の生結果や不確定な値をそのまま登録しない。

## 日付形式

外部 API では `YYYYMMDD` の整数を受け取り、DB では `Date` として保存する。

例:

```json
{
  "purchased_at": 20260512
}
```

不正な日付は `422` とする。

```text
20260230: invalid
20261301: invalid
20260512: valid
```

## POST /receipts

### Request

```json
{
  "purchased_at": 20260512,
  "store_name": "サンプルスーパー",
  "total_amount": 636,
  "items": [
    {
      "raw_name": "タマゴM 10コ",
      "normalized_name": "卵",
      "product_id": 1,
      "category_id": 1,
      "purchased_quantity": 1,
      "purchased_unit": "パック",
      "base_quantity": 10,
      "base_unit": "個",
      "unit_price": 238,
      "line_total": 238,
      "is_inventory_target": true
    }
  ]
}
```

### Required fields

Receipt:

```text
purchased_at
total_amount
items
```

ReceiptItem:

```text
raw_name
purchased_quantity
line_total
is_inventory_target
```

在庫対象の場合は次も必須。

```text
normalized_name
base_quantity
base_unit
```

### Server computed fields

以下はクライアントから受け取らず、サーバーで計算する。

```text
items_total
adjustment_amount
```

計算式:

```text
items_total = sum(item.line_total)
adjustment_amount = total_amount - items_total
```

### Success response

Status: `201 Created`

```json
{
  "id": 1,
  "purchased_at": 20260512,
  "store_name": "サンプルスーパー",
  "total_amount": 636,
  "items_total": 636,
  "adjustment_amount": 0,
  "item_count": 1
}
```

## GET /receipts

### Query parameters

| 名前 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `skip` | int | no | 取得開始位置 |
| `limit` | int | no | 取得件数 |
| `date_from` | int | no | `YYYYMMDD` |
| `date_to` | int | no | `YYYYMMDD` |
| `category_id` | int | no | カテゴリで絞り込み |
| `inventory_only` | bool | no | 在庫対象明細を含むものに絞り込み |

### Success response

```json
[
  {
    "id": 1,
    "purchased_at": 20260512,
    "store_name": "サンプルスーパー",
    "total_amount": 636,
    "items_total": 636,
    "adjustment_amount": 0,
    "item_count": 1
  }
]
```

## GET /receipts/{receipt_id}

### Success response

```json
{
  "id": 1,
  "purchased_at": 20260512,
  "store_name": "サンプルスーパー",
  "total_amount": 636,
  "items_total": 636,
  "adjustment_amount": 0,
  "items": [
    {
      "id": 1,
      "raw_name": "タマゴM 10コ",
      "normalized_name": "卵",
      "product_id": 1,
      "category_id": 1,
      "purchased_quantity": "1.00",
      "purchased_unit": "パック",
      "base_quantity": "10.00",
      "base_unit": "個",
      "unit_price": 238,
      "line_total": 238,
      "is_inventory_target": true
    }
  ]
}
```

## DELETE /receipts/{receipt_id}

### Success response

```json
{
  "deleted": true,
  "id": 1
}
```

## Error response

エラー形式はできるだけ統一する。

```json
{
  "detail": {
    "code": "invalid_receipt",
    "message": "レシートデータが不正です"
  }
}
```

FastAPI / Pydantic 標準の `422` 形式を使う場合は、そのままでもよい。

## ステータスコード

| 状況 | ステータス |
| --- | ---: |
| 登録成功 | 201 |
| 取得成功 | 200 |
| 削除成功 | 200 |
| 型・形式が不正 | 422 |
| 形式は正しいが業務ルールに反する | 400 |
| 対象が存在しない | 404 |
