# API_SPEC.md

## 前提

この API は、ユーザー確認済みのレシートデータだけを受け取る。

OCR の生結果や不確定な値をそのまま登録しない。

OCR API は `product_id` と `category_id` を決めない。OCR の `normalized_name` は商品名候補であり、DB の正式な `products.name` と一致する保証はない。

フロントエンドは OCR 仮データを直接 `POST /receipts` へ送らず、先に `POST /receipts/prepare` を呼び出す。DB API は `products.name_key` と `product_aliases.alias_key` を使って `product_id` を解決し、未解決の商品はユーザー確認後に `POST /product-aliases` で学習させる。

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

## POST /receipts/prepare

### Request

OCR レスポンスに近い JSON を受け取る。

```json
{
  "status": "needs_confirmation",
  "store_name": "サンプルスーパー",
  "purchased_at": "2026-05-12",
  "total_amount": 238,
  "items": [
    {
      "raw_name": "タマゴM 10コ",
      "normalized_name": "たまご",
      "category_name": "食費",
      "purchased_quantity": 1,
      "purchased_unit": "パック",
      "base_quantity": 10,
      "base_unit": "個",
      "unit_price": 238,
      "line_total": 238,
      "is_inventory_target": true,
      "confidence": 0.82,
      "warnings": []
    }
  ],
  "warnings": []
}
```

### Behavior

`POST /receipts/prepare` は DB にレシートを保存しない。

主な処理:

```text
purchased_at の YYYY-MM-DD -> YYYYMMDD 変換
OCR 専用項目の除去
raw_name / normalized_name から product_id 解決
products.default_category_id による category_id 補完
未解決商品の unresolved_items / product_candidates 返却
```

`product_id` が解決できた場合、`normalized_name` は DB 正式名である `products.name` に寄せる。解決できない場合は `product_id = null` のまま返す。

### Success response

```json
{
  "receipt": {
    "store_name": "サンプルスーパー",
    "purchased_at": 20260512,
    "total_amount": 238,
    "items": [
      {
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
  },
  "item_resolutions": [
    {
      "index": 0,
      "resolution_status": "resolved",
      "resolution_source": "raw_name_alias",
      "product_id": 1,
      "product_name": "卵",
      "product_candidates": [],
      "issues": []
    }
  ],
  "unresolved_items": [],
  "warnings": [],
  "validation_issues": []
}
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

## GET /products/search

未解決商品に対して、フロントエンドが商品候補を検索する。

Query parameters:

| 名前 | 型 | 必須 | 説明 |
| --- | --- | ---: | --- |
| `query` | string | yes | 検索語 |
| `limit` | int | no | 既定値 `10` |

検索には `products.name_key` と `product_aliases.alias_key` を使う。

## POST /product-aliases

ユーザーが確認した OCR 名と商品マスタの対応を `product_aliases` に保存する。

```json
{
  "alias_name": "タマゴM 10コ",
  "product_id": 1,
  "source": "user_confirmed"
}
```

`alias_name` から `alias_key` を生成する。同じ `alias_key` が同じ `product_id` に登録済みなら冪等に成功し、別 `product_id` に登録済みなら `409` とする。

## GET /prices/cheapest

指定した `product_id` の購入履歴から、最安購入店舗を返す。

Query parameters:

| 名前 | 型 | 必須 | 説明 |
| --- | --- | ---: | --- |
| `product_id` | int | yes | 商品 ID |
| `period_days` | int | no | 既定値 `90` |

比較式:

```text
price_per_base_unit = line_total / base_quantity
```

`line_total` が最小の明細ではなく、共通単位あたり価格が最小の明細を返す。`product_id` が未解決の明細、`base_quantity` が `null` または `0` 以下の明細、`base_unit` が `null` の明細、`store_name` が `null` のレシートは対象外。

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
