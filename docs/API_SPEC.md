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

在庫対象明細で `base_quantity` / `base_unit` を確定できない場合、`item_resolutions[].issues` に理由を返す。明細固有の問題は `item_resolutions[].issues` を主とし、確認画面が全体表示しやすいように `validation_issues` に `inventory_items_require_quantity_confirmation` を追加する。

数量・単位関連の issue:

| issue | 意味 |
| --- | --- |
| `unit_conversion_missing` | 商品別変換が必要だが、`product_unit_conversions` に該当行がない |
| `ambiguous_quantity` | 単位だけでは共通数量を決められない |
| `base_quantity_missing` | 在庫対象なのに `base_quantity` が最終的に空 |
| `base_unit_missing` | 在庫対象なのに `base_unit` が最終的に空 |

後方互換性のため、当面は既存の `inventory_target_without_base_quantity` / `inventory_target_without_base_unit` も併せて返す。

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

### Quantity confirmation example

```json
{
  "receipt": {
    "store_name": "サンプルスーパー",
    "purchased_at": 20260512,
    "total_amount": 198,
    "items": [
      {
        "raw_name": "トマト 2個",
        "normalized_name": "トマト",
        "product_id": 1,
        "category_id": null,
        "purchased_quantity": "2.00",
        "purchased_unit": "個",
        "base_quantity": null,
        "base_unit": "g",
        "unit_price": null,
        "line_total": 198,
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
      "product_name": "トマト",
      "product_candidates": [],
      "issues": [
        "inventory_target_without_base_quantity",
        "base_quantity_missing",
        "unit_conversion_missing",
        "ambiguous_quantity"
      ]
    }
  ],
  "unresolved_items": [
    {
      "index": 0,
      "resolution_status": "resolved",
      "resolution_source": "raw_name_alias",
      "product_id": 1,
      "product_name": "トマト",
      "product_candidates": [],
      "issues": [
        "inventory_target_without_base_quantity",
        "base_quantity_missing",
        "unit_conversion_missing",
        "ambiguous_quantity"
      ]
    }
  ],
  "warnings": [],
  "validation_issues": [
    "inventory_items_require_quantity_confirmation"
  ]
}
```

この例では、確認画面でユーザーが `base_quantity` / `base_unit` を修正してから `POST /receipts` で保存する。

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

## POST /receipts/auto-create

OCRレスポンスに近いJSONを受け取り、`POST /receipts/prepare` と同じ整形・解決を行ったうえで、自動登録してよい条件を満たす場合だけレシートを保存する。

このAPIは既存の `POST /receipts` のJSON構造を変更しない。保存時は `prepare` が返す `receipt` を既存の登録schemaに変換して保存する。

### Auto-registration gate

自動登録する条件:

```text
validation_issues が空
unresolved_items が空
OCR top-level warnings が空
各itemの warnings が空
各itemの confidence が 0.85 以上
各item_resolutions[].issues が空
各item_resolutions[].resolution_status が resolved
購入日、合計金額、明細が揃っている
各明細の raw_name / purchased_quantity / line_total / is_inventory_target が揃っている
在庫対象明細は product_id / normalized_name / base_quantity / base_unit が揃っている
OCR metadata が review reason を要求していない
total_amount と line_total 合計が一致する
```

条件を満たさない場合、レシートは保存せず、`created = false` と `auto_registration.reasons` を返す。

### Request

`POST /receipts/prepare` と同じOCR寄りJSONを受け取る。itemには任意で `ocr_metadata` を含めてよい。

フロントエンドの自動登録チェックボックスは `auto_register_enabled` として送る。

```json
{
  "auto_register_enabled": true,
  "status": "needs_confirmation",
  "store_name": "サンプルスーパー",
  "purchased_at": "2026-05-12",
  "total_amount": 238,
  "items": []
}
```

`auto_register_enabled = false` の場合、他の条件を満たしていても保存しない。レスポンスは `created = false` になり、`auto_registration.reasons` に `auto_registration_disabled` を含める。これにより、フロントエンドは同じレスポンスを確認画面に回せる。

### Response example: created

```json
{
  "created": true,
  "receipt_id": 1,
  "summary": {
    "id": 1,
    "purchased_at": 20260512,
    "store_name": "サンプルスーパー",
    "total_amount": 238,
    "items_total": 238,
    "adjustment_amount": 0,
    "item_count": 1
  },
  "receipt": {},
  "item_resolutions": [],
  "unresolved_items": [],
  "warnings": [],
  "validation_issues": [],
  "auto_registration": {
    "eligible": true,
    "reasons": [],
    "min_item_confidence": 0.85
  }
}
```

### Response example: not created

```json
{
  "created": false,
  "receipt_id": null,
  "summary": null,
  "receipt": {},
  "item_resolutions": [],
  "unresolved_items": [],
  "warnings": [],
  "validation_issues": [],
  "auto_registration": {
    "eligible": false,
    "reasons": [
      "item_0_confidence_below_threshold",
      "item_0_needs_review:base_quantity_uncertain"
    ],
    "min_item_confidence": 0.85
  }
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

## POST /products

確認画面で商品候補が存在しない場合に、商品マスタを新規作成する。

`name_key` はリクエストで自由入力させず、サーバー側で `name` から生成する。生成できない場合は `400` とする。

### Request

```json
{
  "name": "豆腐",
  "default_base_unit": "g",
  "is_inventory_target": true,
  "default_category_id": 1,
  "initial_alias_name": "絹とうふ 300g",
  "alias_source": "user_confirmed"
}
```

| 名前 | 型 | 必須 | 説明 |
| --- | --- | ---: | --- |
| `name` | string | yes | 商品マスタ名。空白だけは不可 |
| `default_base_unit` | string | yes | 在庫・レシピで使う標準単位。空白だけは不可 |
| `is_inventory_target` | boolean | yes | 通常在庫対象にするか |
| `default_category_id` | int | no | 既定カテゴリ。指定された場合は存在確認する |
| `initial_alias_name` | string | no | 確認画面で元になった `raw_name` を登録する |
| `alias_source` | string | no | `initial_alias_name` の source。既定値は `user_confirmed` |

`initial_alias_name` が指定された場合、商品作成と同じトランザクションで `product_aliases` に登録する。alias が別商品と衝突した場合は `409 Conflict` を返し、商品作成も rollback する。

### Success response

```json
{
  "id": 1,
  "name": "豆腐",
  "name_key": "豆腐",
  "default_base_unit": "g",
  "default_category_id": 1,
  "is_inventory_target": true,
  "created_alias": {
    "id": 10,
    "alias_name": "絹とうふ 300g",
    "alias_key": "絹とうふ300g",
    "product_id": 1,
    "source": "user_confirmed"
  }
}
```

`initial_alias_name` がない場合、`created_alias` は `null` になる。

### Error responses

同じ `name_key` の商品が既にある:

```json
{
  "detail": {
    "code": "product_conflict",
    "message": "name_key is already used by another product"
  }
}
```

存在しないカテゴリ:

```json
{
  "detail": {
    "code": "category_not_found",
    "message": "default_category_id does not exist: 999"
  }
}
```

別商品の alias と衝突:

```json
{
  "detail": {
    "code": "alias_conflict",
    "message": "alias_key is already linked to another product"
  }
}
```

## GET /products/search

未解決商品に対して、フロントエンドが商品候補を検索する。

Query parameters:

| 名前 | 型 | 必須 | 説明 |
| --- | --- | ---: | --- |
| `query` | string | yes | 検索語 |
| `limit` | int | no | 既定値 `10` |

検索には `products.name_key` と `product_aliases.alias_key` を使う。alias は `is_active = true` かつ `source` が `user_confirmed`, `seed`, `admin`, `ocr_suggested` のものだけを候補検索に使う。

### Success response

```json
{
  "query": "タマゴ",
  "query_key": "たまご",
  "items": [
    {
      "product_id": 1,
      "name": "卵",
      "default_base_unit": "個",
      "default_category_id": 1,
      "is_inventory_target": true
    }
  ]
}
```

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

`alias_name` は空白だけを許可しない。`product_id` が存在しない場合は `404` とする。

`source` の既定値は `user_confirmed` である。許可値は次の通り。

| source | 自動解決 | 候補検索 | 説明 |
| --- | --- | --- | --- |
| `user_confirmed` | 可 | 可 | ユーザーが確認画面で選択したalias |
| `seed` | 可 | 可 | 初期データ・テストデータとして安全に登録したalias |
| `admin` | 可 | 可 | 管理者が確認して登録したalias |
| `ocr_suggested` | 不可 | 可 | OCRやAIが推定しただけのalias |

`POST /receipts/prepare` の自動解決では、完全一致した active alias のうち `user_confirmed`, `seed`, `admin` だけを使う。`ocr_suggested` は `product_candidates` には出してよいが、自動で `resolved` にしない。`is_active = false` の alias は自動解決にも候補検索にも使わない。

### Success response

```json
{
  "id": 1,
  "alias_name": "タマゴM 10コ",
  "alias_key": "たまごm10こ",
  "product_id": 1,
  "product_name": "卵",
  "source": "user_confirmed",
  "created": true
}
```

### Error responses

存在しない商品:

```json
{
  "detail": {
    "code": "product_not_found",
    "message": "product_id does not exist: 999"
  }
}
```

別商品の alias と衝突:

```json
{
  "detail": {
    "code": "alias_conflict",
    "message": "alias_key is already linked to another product"
  }
}
```

空白だけの alias:

```json
{
  "detail": {
    "code": "invalid_alias",
    "message": "alias_name must not be empty"
  }
}
```

許可されていない source:

```json
{
  "detail": {
    "code": "invalid_alias",
    "message": "source must be one of: admin, ocr_suggested, seed, user_confirmed"
  }
}
```

## 確認画面での商品紐づけフロー

フロントエンドは OCR 結果を直接 `POST /receipts` へ送らず、次の順でユーザー確認済みデータを作る。

```text
1. OCR 結果を POST /receipts/prepare に送る
2. 未解決商品の product_candidates を確認画面に表示する
3. 候補が足りない場合は GET /products/search?query=... で商品名または alias から検索する
4. 候補が存在しない場合は POST /products で商品を作成し、必要なら raw_name を initial_alias_name として登録する
5. 既存商品を選んだ場合は OCR 由来の raw_name を POST /product-aliases で product_aliases に登録する
6. 確認済みの receipt を POST /receipts で保存する
```

`raw_name` はレシート上の表記であり、最優先の alias 学習対象である。

`normalized_name` は OCR や AI が推定した候補であり、DB 正式名とは限らない。そのため `POST /receipts/prepare` は `normalized_name` を自動で alias 登録しない。`normalized_name` を alias として登録したい場合は、ユーザーが明示的に確認した値を `POST /product-aliases` の `alias_name` として送る。

在庫対象明細で `item_resolutions[].issues` に `base_quantity_missing`, `base_unit_missing`, `unit_conversion_missing`, `ambiguous_quantity` が含まれる場合は、確認画面でユーザーに `base_quantity` / `base_unit` を修正させる。修正された値はユーザー確認済みデータとして `POST /receipts` に送る。

## GET /operations/receipt-prepare-metrics

`POST /receipts/prepare` と alias 学習の最小限の運用指標を返す。

この API のために保存するのは集約情報だけである。`POST /receipts/prepare` の入力全体、OCR 生 JSON、価格、店舗名、購入日、全明細は保存しない。

### Success response

```json
{
  "prepare_count": 120,
  "total_item_count": 640,
  "unresolved_item_count": 38,
  "unresolved_rate": 0.059375,
  "alias_count": 82,
  "active_alias_count": 80,
  "alias_conflict_count": 3,
  "inventory_base_quantity_missing_count": 11,
  "top_unresolved_raw_names": [
    {
      "raw_name": "タマゴM 10コ",
      "raw_name_key": "たまごm10こ",
      "count": 9
    }
  ]
}
```

`unresolved_rate` は `unresolved_item_count / total_item_count` で計算する。`total_item_count = 0` の場合は `0` を返す。

`top_unresolved_raw_names` は未解決明細の `raw_name` だけを件数集約して返す。レシート全体や解決済み明細の `raw_name` は保存しない。

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
