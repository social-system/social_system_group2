# レシート・家計簿・在庫データベース API

このリポジトリは、ユーザー確認済みのレシート購入履歴、商品マスタ、価格比較、在庫情報を扱う FastAPI バックエンドです。

OCR API ではありません。画像アップロード、OCR 実行、レシート画像保存、OCR 仮データの永続保存、認証、ユーザー管理、世帯管理、レシピ提案 API はこのリポジトリでは扱いません。

```text
OCR 結果 = 仮データ
DB 登録データ = ユーザー確認済みデータ
```

OCR 連携では、OCR API のレスポンスを直接 `POST /receipts` に登録しません。フロントエンドはまず OCR 仮データを `POST /receipts/prepare` に送り、DB API 側で日付変換、OCR 専用項目の除去、`product_id` 解決、カテゴリ補完、数量確認課題の付与を行います。その結果を確認画面でユーザーが修正・確認した後、確定データだけを `POST /receipts` で保存します。

```text
OCR API
  -> OCR 仮 JSON
  -> DB API POST /receipts/prepare
  -> フロントエンド確認画面
  -> DB API POST /receipts
  -> 必要に応じて POST /inventory/receipts/{receipt_id}/apply
  -> GET /prices/cheapest
```

## 提供する機能

| 区分 | 内容 |
| --- | --- |
| レシート管理 | 登録、一覧、詳細、削除 |
| OCR 登録準備 | OCR 仮データの整形、商品解決、カテゴリ補完、登録前課題の返却 |
| OCR 自動登録ゲート | 安全条件を満たす OCR 仮データだけを自動保存 |
| 商品マスタ | 商品検索、商品作成、別名学習 |
| 価格比較 | 過去購入履歴から共通単位あたりの最安購入店舗を取得 |
| 在庫反映 | レシート明細を在庫ロットへ反映 |
| 在庫管理 | 在庫残量、在庫ロット、在庫増減履歴の取得と手動増減 |
| 運用指標 | 登録準備回数、未解決率、別名衝突数、未解決名上位を取得 |

## 使用技術

- Python 3.12+
- FastAPI
- SQLAlchemy
- Alembic
- SQLite（ローカル開発・テスト）
- Render PostgreSQL（本番デプロイ）
- Pydantic
- pytest
- uv

## データ設計

詳細は `docs/DATABASE_DESIGN.md` と `docs/INVENTORY_IMPLEMENTATION_SPEC.md` を参照してください。

主なテーブル:

```text
receipts
receipt_items
accounting_categories
products
product_aliases
product_unit_conversions
receipt_prepare_metrics
receipt_prepare_unresolved_names
product_alias_conflict_events
inventory_locations
inventory_batches
inventory_operations
inventory_movements
```

レシート明細では、購入時の表記とアプリ内で扱う共通単位を分けます。

| カラム | 意味 |
| --- | --- |
| `raw_name` | レシート上の商品名 |
| `normalized_name` | アプリ内で扱う商品名 |
| `purchased_quantity` | 購入時の数量 |
| `purchased_unit` | 購入時の単位 |
| `base_quantity` | 在庫・レシピ用に変換した数量 |
| `base_unit` | 在庫・レシピ用の共通単位 |

例:

```json
{
  "raw_name": "卵 1パック",
  "normalized_name": "卵",
  "purchased_quantity": 1,
  "purchased_unit": "パック",
  "base_quantity": 10,
  "base_unit": "個"
}
```

`total_amount == sum(line_total)` は必須にしません。実レシートでは割引、ポイント、税、レジ袋、OCR 漏れなどにより、明細行合計と最終支払額が一致しないことがあります。差額はサーバー側で `adjustment_amount = total_amount - items_total` として保存します。

## セットアップ

```bash
uv sync
```

必要に応じて仮想環境を有効化します。

```bash
source .venv/bin/activate
```

## ローカル起動

`DATABASE_URL` が未設定の場合は、開発用として `sqlite:///./receipts.db` を使います。

```bash
uv run uvicorn app.main:app --reload
```

既定の URL:

```text
http://localhost:8000
```

FastAPI の自動ドキュメント:

```text
http://localhost:8000/docs
http://localhost:8000/redoc
```

開発環境では `CORS_ALLOW_ORIGINS` 未設定時に `http://localhost:5173` を許可します。本番では `CORS_ALLOW_ORIGINS` にカンマ区切りでフロントエンド URL を指定します。

## 環境変数

| 変数 | 必須 | 説明 |
| --- | --- | --- |
| `DATABASE_URL` | 本番 yes | DB 接続 URL。未設定時は `sqlite:///./receipts.db` |
| `APP_ENV` | no | 本番では `production` を指定 |
| `CORS_ALLOW_ORIGINS` | 本番 yes | 許可するフロントエンド URL。カンマ区切り可 |
| `PORT` | Render が設定 | Uvicorn の待受ポート |

`DATABASE_URL` が `postgres://` または `postgresql://` で始まる場合、アプリ側で `postgresql+psycopg://` に正規化します。SQLite のときだけ `connect_args={"check_same_thread": False}` を使い、PostgreSQL には SQLite 専用設定を渡しません。

## API 一覧

| メソッド | パス | 概要 |
| --- | --- | --- |
| `GET` | `/` | ヘルスチェック |
| `POST` | `/receipts/prepare` | OCR 仮データを登録前確認用データへ整形 |
| `POST` | `/receipts/auto-create` | OCR 仮データを安全条件つきで自動登録 |
| `POST` | `/receipts` | ユーザー確認済みレシートを登録 |
| `GET` | `/receipts` | レシート一覧 |
| `GET` | `/receipts/{receipt_id}` | レシート詳細 |
| `DELETE` | `/receipts/{receipt_id}` | レシート削除 |
| `GET` | `/products/search` | 商品マスタ検索 |
| `POST` | `/products` | 商品マスタ作成 |
| `POST` | `/product-aliases` | 商品別名登録 |
| `GET` | `/prices/cheapest` | 商品の最安購入店舗取得 |
| `POST` | `/inventory/receipts/{receipt_id}/apply` | レシート明細を在庫へ反映 |
| `GET` | `/inventory/balances` | 在庫残量一覧 |
| `GET` | `/inventory/batches` | 在庫ロット一覧 |
| `POST` | `/inventory/movements` | 在庫増減登録 |
| `GET` | `/inventory/movements` | 在庫増減履歴 |
| `GET` | `/operations/receipt-prepare-metrics` | OCR 登録準備と別名学習の運用指標 |

## 共通ルール

外部 API の日付は主に `YYYYMMDD` の整数で扱い、DB では `Date` として保存します。

```json
{
  "purchased_at": 20260512
}
```

不正な日付は `422 Unprocessable Entity` です。

```text
20260230: invalid
20261301: invalid
20260512: valid
```

主なステータス:

| 状況 | ステータス |
| --- | ---: |
| 登録成功 | 201 |
| 取得成功 | 200 |
| 削除成功 | 200 |
| 型・形式が不正 | 422 |
| 形式は正しいが業務ルールに反する | 400 |
| 対象が存在しない | 404 |
| 一意制約・別名衝突 | 409 |

業務エラーは主に次の形式です。FastAPI / Pydantic 標準の `422` はそのまま返します。

```json
{
  "detail": {
    "code": "invalid_receipt",
    "message": "レシートデータが不正です"
  }
}
```

## API 詳細

### GET /

ヘルスチェックです。

レスポンス:

```json
{
  "status": "ok"
}
```

### POST /receipts/prepare

OCR レスポンスに近い JSON を受け取り、DB 登録前の確認画面で扱いやすい `receipt` オブジェクトへ整形します。この API はレシートを保存しません。

主な処理:

- `purchased_at: "YYYY-MM-DD"` を `YYYYMMDD` の整数に変換
- OCR 専用の `status`、`confidence`、明細内の `warnings`、`ocr_metadata` を登録用 `receipt` から除外
- `raw_name` / `normalized_name` と `product_aliases` / `products` から `product_id` を解決
- 解決できた場合は `normalized_name` を `products.name` に寄せる
- `products.default_category_id` から `category_id` を補完
- 商品別単位変換が可能な場合は `base_quantity` / `base_unit` を補完
- 未解決または確認が必要な明細を `unresolved_items` と `item_resolutions[].issues` に返す
- 登録準備の集約指標を保存する

リクエスト:

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
      "warnings": [],
      "ocr_metadata": {
        "auto_register_candidate": true,
        "needs_review_reasons": []
      }
    }
  ],
  "warnings": []
}
```

レスポンス:

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

数量・単位関連の主な `issues`:

| issue | 意味 |
| --- | --- |
| `unit_conversion_missing` | 商品別変換が必要だが、`product_unit_conversions` に該当行がない |
| `ambiguous_quantity` | 単位だけでは共通数量を決められない |
| `base_quantity_missing` | 在庫対象なのに `base_quantity` が最終的に空 |
| `base_unit_missing` | 在庫対象なのに `base_unit` が最終的に空 |

後方互換性のため、当面は `inventory_target_without_base_quantity` / `inventory_target_without_base_unit` も併せて返します。

### POST /receipts/auto-create

OCR レスポンスに近い JSON を受け取り、`POST /receipts/prepare` と同じ整形・解決を行ったうえで、自動登録してよい条件を満たす場合だけレシートを保存します。

主な自動登録条件:

- `auto_register_enabled = true`
- `validation_issues` が空
- `unresolved_items` が空
- OCR top-level `warnings` が空
- 各 item の `warnings` が空
- 各 item の `confidence` が `0.85` 以上
- 各 `item_resolutions[].issues` が空
- 各 `item_resolutions[].resolution_status` が `resolved`
- 購入日、合計金額、明細が揃っている
- 各明細の `raw_name` / `purchased_quantity` / `line_total` / `is_inventory_target` が揃っている
- 在庫対象明細は `product_id` / `normalized_name` / `base_quantity` / `base_unit` が揃っている
- OCR metadata が review reason を要求していない
- `total_amount` と `line_total` 合計が一致する

リクエスト:

```json
{
  "auto_register_enabled": true,
  "status": "needs_confirmation",
  "store_name": "サンプルスーパー",
  "purchased_at": "2026-05-12",
  "total_amount": 238,
  "items": [
    {
      "raw_name": "タマゴM 10コ",
      "normalized_name": "たまご",
      "purchased_quantity": 1,
      "purchased_unit": "パック",
      "base_quantity": 10,
      "base_unit": "個",
      "unit_price": 238,
      "line_total": 238,
      "is_inventory_target": true,
      "confidence": 0.98,
      "warnings": []
    }
  ],
  "warnings": []
}
```

登録された場合:

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
  "receipt": {
    "store_name": "サンプルスーパー",
    "purchased_at": 20260512,
    "total_amount": 238,
    "items": []
  },
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

登録されない場合は `created = false`、`receipt_id = null`、`summary = null` になり、`auto_registration.reasons` に理由が入ります。

### POST /receipts

ユーザー確認済みレシートを保存します。OCR 仮データを直接送る API ではありません。

リクエスト:

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
    },
    {
      "raw_name": "センザイ",
      "normalized_name": "洗剤",
      "product_id": null,
      "category_id": 2,
      "purchased_quantity": 1,
      "purchased_unit": "個",
      "base_quantity": null,
      "base_unit": null,
      "unit_price": 398,
      "line_total": 398,
      "is_inventory_target": false
    }
  ]
}
```

必須項目:

| 階層 | 必須項目 |
| --- | --- |
| レシート | `purchased_at`, `total_amount`, `items` |
| 明細 | `raw_name`, `purchased_quantity`, `line_total`, `is_inventory_target` |
| 在庫対象明細 | `normalized_name` または `product_id`, `base_quantity`, `base_unit` |

サーバー計算項目:

```text
items_total = sum(item.line_total)
adjustment_amount = total_amount - items_total
```

`unit_price * purchased_quantity == line_total` は必須条件にしません。`total_amount == sum(line_total)` も必須条件にしません。

成功レスポンス:

```json
{
  "id": 1,
  "purchased_at": 20260512,
  "store_name": "サンプルスーパー",
  "total_amount": 636,
  "items_total": 636,
  "adjustment_amount": 0,
  "item_count": 2
}
```

### GET /receipts

レシート一覧を返します。

クエリ:

| 名前 | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `skip` | int | `0` | 取得開始位置。`0` 以上 |
| `limit` | int | `50` | 取得件数。`1` 以上 `100` 以下 |
| `date_from` | int | null | `YYYYMMDD`。購入日の開始 |
| `date_to` | int | null | `YYYYMMDD`。購入日の終了 |
| `category_id` | int | null | 指定カテゴリの明細を含むレシートに絞り込み |
| `inventory_only` | bool | `false` | 在庫対象明細を含むレシートに絞り込み |

レスポンス:

```json
[
  {
    "id": 1,
    "purchased_at": 20260512,
    "store_name": "サンプルスーパー",
    "total_amount": 636,
    "items_total": 636,
    "adjustment_amount": 0,
    "item_count": 2
  }
]
```

### GET /receipts/{receipt_id}

レシート詳細を明細付きで返します。

レスポンス:

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

存在しない `receipt_id` は `404 Not Found` です。

### DELETE /receipts/{receipt_id}

レシートを削除します。明細は cascade で削除されます。

レスポンス:

```json
{
  "deleted": true,
  "id": 1
}
```

存在しない `receipt_id` は `404 Not Found` です。

### GET /products/search

商品マスタと商品別名から候補を検索します。確認画面で未解決商品に対する候補表示に使います。

クエリ:

| 名前 | 型 | 必須 | 既定値 | 説明 |
| --- | --- | ---: | --- | --- |
| `query` | string | yes | - | 検索語。1文字以上 |
| `limit` | int | no | `10` | `1` 以上 `50` 以下 |

レスポンス:

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

### POST /products

商品マスタを作成します。`name_key` は `name` からサーバー側で生成します。`initial_alias_name` が指定された場合は、同じトランザクションで `product_aliases` に登録します。

リクエスト:

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
| `name` | string | yes | 商品マスタ名 |
| `default_base_unit` | string | yes | 在庫・レシピで使う標準単位 |
| `is_inventory_target` | boolean | yes | 通常在庫対象にするか |
| `default_category_id` | int | no | 既定カテゴリ。指定時は存在確認する |
| `initial_alias_name` | string | no | 作成時に同時登録する別名 |
| `alias_source` | string | no | 既定値 `user_confirmed` |

レスポンス:

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

主なエラー:

| ステータス | 条件 |
| ---: | --- |
| 400 | `name` または `default_base_unit` が空白だけ |
| 404 | `default_category_id` が存在しない |
| 409 | 同じ `name_key` の商品が存在する |
| 409 | `initial_alias_name` が別商品の alias と衝突する |

### POST /product-aliases

ユーザーが確認した OCR 名や入力名と商品マスタの対応を保存します。同じ `alias_key` が同じ `product_id` に登録済みなら冪等に成功し、`created = false` を返します。別 `product_id` に登録済みなら `409 Conflict` です。

リクエスト:

```json
{
  "alias_name": "タマゴM 10コ",
  "product_id": 1,
  "source": "user_confirmed"
}
```

| source | 自動解決 | 候補検索 | 説明 |
| --- | --- | --- | --- |
| `user_confirmed` | 可 | 可 | ユーザーが確認画面で選択した alias |
| `seed` | 可 | 可 | 初期データ・テストデータとして安全に登録した alias |
| `admin` | 可 | 可 | 管理者が確認して登録した alias |
| `ocr_suggested` | 不可 | 可 | OCR や AI が推定しただけの alias |

レスポンス:

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

主なエラー:

| ステータス | 条件 |
| ---: | --- |
| 400 | `alias_name` が空白だけ、または `source` が許可外 |
| 404 | `product_id` が存在しない |
| 409 | 同じ `alias_key` が別商品に紐づいている |

### GET /prices/cheapest

指定した `product_id` の購入履歴から、共通単位あたり価格が最安の購入店舗を返します。

クエリ:

| 名前 | 型 | 必須 | 既定値 | 説明 |
| --- | --- | ---: | --- | --- |
| `product_id` | int | yes | - | 商品 ID。`1` 以上 |
| `period_days` | int | no | `90` | 過去何日分を見るか。`1` 以上 |

比較式:

```text
price_per_base_unit = line_total / base_quantity
```

`product_id` が未解決の明細、`base_quantity` が `null` または `0` 以下の明細、`base_unit` が `null` の明細、`store_name` が `null` のレシートは対象外です。

レスポンス:

```json
{
  "product_id": 1,
  "product_name": "卵",
  "period_days": 90,
  "cheapest": {
    "store_name": "サンプルスーパー",
    "price_per_base_unit": 23.8,
    "line_total": 238,
    "base_quantity": "10.00",
    "base_unit": "個",
    "purchased_at": 20260512,
    "receipt_item_id": 1
  }
}
```

商品は存在するが対象履歴がない場合、`cheapest` は `null` です。商品が存在しない場合は `404 Not Found` です。

### POST /inventory/receipts/{receipt_id}/apply

レシート明細から在庫対象の商品を在庫へ反映します。対象明細ごとに `inventory_batches` を作成し、購入による `inventory_movements` を記録します。

処理対象になる明細:

```text
is_inventory_target = true
product_id is not null
base_quantity is not null and base_quantity > 0
base_unit is not null
```

リクエスト:

```json
{
  "default_location_id": 1,
  "expires_at_by_receipt_item_id": {
    "31": "2026-05-20",
    "32": "2026-05-18"
  },
  "idempotency_key": "receipt:12:apply-inventory"
}
```

| 名前 | 型 | 必須 | 説明 |
| --- | --- | ---: | --- |
| `default_location_id` | int | no | 作成する在庫ロットの標準保管場所 |
| `expires_at_by_receipt_item_id` | object | no | 明細 ID ごとの期限日 |
| `idempotency_key` | string | no | 同じ API リクエストの二重送信防止キー |

レスポンス:

```json
{
  "receipt_id": 12,
  "operation_id": 100,
  "applied_count": 2,
  "skipped_count": 1,
  "items": [
    {
      "receipt_item_id": 31,
      "product_id": 1,
      "product_name": "卵",
      "quantity": "10.00",
      "unit": "個",
      "batch_id": 201,
      "status": "applied",
      "reason": null
    },
    {
      "receipt_item_id": 33,
      "product_id": null,
      "product_name": "洗剤",
      "quantity": null,
      "unit": null,
      "batch_id": null,
      "status": "skipped",
      "reason": "not_inventory_target"
    }
  ]
}
```

主な `skipped` 理由:

| reason | 意味 |
| --- | --- |
| `not_inventory_target` | 在庫対象ではない |
| `missing_product_or_base_quantity` | 在庫反映に必要な商品・数量・単位が不足 |
| `already_applied` | 既に同じレシート明細が在庫反映済み |

主なエラー:

| ステータス | 条件 |
| ---: | --- |
| 400 | `default_location_id` が存在しない |
| 404 | `receipt_id` が存在しない |

### GET /inventory/balances

現在在庫を商品単位、単位単位で集計して返します。

クエリ:

| 名前 | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `product_id` | int | null | 商品で絞り込み |
| `location_id` | int | null | 保管場所で絞り込み |
| `include_zero` | bool | `false` | 残量 0 や inactive を含めるか |

レスポンス:

```json
{
  "items": [
    {
      "product_id": 1,
      "product_name": "卵",
      "quantity": "16.00",
      "unit": "個",
      "nearest_expires_at": "2026-05-15",
      "batch_count": 2
    }
  ]
}
```

### GET /inventory/batches

在庫ロット一覧を返します。

クエリ:

| 名前 | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `product_id` | int | null | 商品で絞り込み |
| `location_id` | int | null | 保管場所で絞り込み |
| `status` | string | null | `active` / `depleted` / `discarded` |
| `expires_before` | date | null | 指定日以前に期限が来るもの |
| `include_zero` | bool | `false` | 残量 0 や inactive を含めるか |

レスポンス:

```json
{
  "items": [
    {
      "batch_id": 201,
      "product_id": 1,
      "product_name": "卵",
      "initial_quantity": "10.00",
      "current_quantity": "8.00",
      "unit": "個",
      "location_id": 1,
      "location_name": "冷蔵",
      "purchased_at": "2026-05-12",
      "expires_at": "2026-05-20",
      "status": "active",
      "receipt_item_id": 31
    }
  ]
}
```

不正な `status` は `400 Bad Request` です。

### POST /inventory/movements

手動で在庫を増減します。`consume` と `dispose` は在庫を減らします。`adjust` は `quantity > 0` なら新しいロットを追加し、`quantity < 0` なら既存ロットから減らします。

リクエスト:

```json
{
  "product_id": 1,
  "movement_type": "consume",
  "quantity": "2.00",
  "unit": "個",
  "batch_id": null,
  "location_id": 1,
  "reason": "卵焼きに使用",
  "occurred_at": "2026-05-13T08:00:00",
  "idempotency_key": "manual:consume:20260513:egg:001"
}
```

| 名前 | 型 | 必須 | 説明 |
| --- | --- | ---: | --- |
| `product_id` | int | yes | 商品 ID |
| `movement_type` | string | yes | `consume` / `dispose` / `adjust` |
| `quantity` | decimal | yes | `0` は不可。`consume` / `dispose` は正数のみ |
| `unit` | string | yes | 商品の `default_base_unit` と一致する必要がある |
| `batch_id` | int | no | 特定ロットだけを増減する場合 |
| `location_id` | int | no | 保管場所。手動追加時などに使用 |
| `reason` | string | no | 理由。255文字以内 |
| `occurred_at` | datetime | no | 発生日時。未指定ならサーバー時刻 |
| `idempotency_key` | string | no | 二重実行防止キー |

`batch_id` が未指定の減少系操作では、期限が近いロット、購入日が古いロット、ID が古いロットの順に自動で減らします。

レスポンス:

```json
{
  "operation_id": 101,
  "movement_type": "consume",
  "product_id": 1,
  "product_name": "卵",
  "requested_quantity": "2.00",
  "unit": "個",
  "movements": [
    {
      "movement_id": 401,
      "batch_id": 201,
      "quantity_delta": "-2.00",
      "remaining_quantity": "8.00"
    }
  ]
}
```

主なエラー:

| ステータス | 条件 |
| ---: | --- |
| 400 | 単位が商品の `default_base_unit` と一致しない |
| 400 | 指定ロットが対象商品・単位・状態に合わない |
| 400 | 在庫不足 |
| 404 | `product_id` または `batch_id` が存在しない |
| 422 | `quantity = 0`、または `consume` / `dispose` で `quantity <= 0` |

### GET /inventory/movements

在庫増減履歴を返します。

クエリ:

| 名前 | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `product_id` | int | null | 商品で絞り込み |
| `batch_id` | int | null | ロットで絞り込み |
| `operation_id` | int | null | 操作で絞り込み |
| `movement_type` | string | null | `purchase` / `consume` / `dispose` / `adjust` など |
| `from_date` | date | null | 発生日の開始 |
| `to_date` | date | null | 発生日の終了 |
| `limit` | int | `100` | `1` 以上 `500` 以下 |
| `offset` | int | `0` | `0` 以上 |

レスポンス:

```json
{
  "items": [
    {
      "movement_id": 301,
      "operation_id": 100,
      "batch_id": 201,
      "product_id": 1,
      "product_name": "卵",
      "movement_type": "purchase",
      "quantity_delta": "10.00",
      "unit": "個",
      "reason": "receipt apply",
      "occurred_at": "2026-05-12T10:00:00"
    }
  ]
}
```

### GET /operations/receipt-prepare-metrics

`POST /receipts/prepare` と alias 学習の最小限の運用指標を返します。OCR 生 JSON、価格、店舗名、購入日、全明細は保存しません。

クエリ:

| 名前 | 型 | 既定値 | 説明 |
| --- | --- | --- | --- |
| `top_limit` | int | `10` | 未解決名上位の件数。`1` 以上 `50` 以下 |

レスポンス:

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

## 確認画面での商品紐づけフロー

フロントエンドは OCR 結果を直接 `POST /receipts` へ送らず、次の順でユーザー確認済みデータを作ります。

```text
1. OCR 結果を POST /receipts/prepare に送る
2. 未解決商品の product_candidates を確認画面に表示する
3. 候補が足りない場合は GET /products/search?query=... で商品名または alias から検索する
4. 候補が存在しない場合は POST /products で商品を作成し、必要なら raw_name を initial_alias_name として登録する
5. 既存商品を選んだ場合は OCR 由来の raw_name を POST /product-aliases で product_aliases に登録する
6. 確認済みの receipt を POST /receipts で保存する
```

`raw_name` はレシート上の表記であり、最優先の alias 学習対象です。`normalized_name` は OCR や AI が推定した候補であり、DB 正式名とは限りません。そのため `POST /receipts/prepare` は `normalized_name` を自動で alias 登録しません。

## Render デプロイ

本番デプロイは Render Web Service + Render PostgreSQL を前提にします。

```text
API: Render Web Service
DB: Render PostgreSQL
DB接続: Render PostgreSQL の Internal Database URL
Schema管理: Alembic
ローカル開発DB: SQLite継続可
```

### Render に設定する値

| 項目 | 値 |
| --- | --- |
| Build Command | `pip install -e .` |
| Start Command | `bash scripts/start_render.sh` |
| Runtime | Python |
| Python version | `3.12` 系 |

環境変数:

| 変数 | 値 |
| --- | --- |
| `DATABASE_URL` | Render PostgreSQL の Internal Database URL |
| `APP_ENV` | `production` |
| `CORS_ALLOW_ORIGINS` | フロントエンドの本番 URL。カンマ区切り可 |
| `PORT` | Render が自動設定するため通常は手動設定不要 |

実際の `DATABASE_URL`、DB ユーザー名、DB パスワード、API キー、トークンはリポジトリにコミットしません。

### 起動時に行うこと

Render の Start Command は `scripts/start_render.sh` を実行します。

```bash
alembic upgrade head
python -m scripts.seed_master_data
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

本番では FastAPI アプリの import 時や起動時に `Base.metadata.create_all()` でテーブルを自動作成しません。スキーマ変更は Alembic migration で管理します。

### 手動デプロイ手順

1. Render で PostgreSQL を作成する。
2. Render で Web Service を作成する。
3. GitHub リポジトリを接続する。
4. Build Command に `pip install -e .` を設定する。
5. Start Command に `bash scripts/start_render.sh` を設定する。
6. `DATABASE_URL` に Render PostgreSQL の Internal Database URL を設定する。
7. `APP_ENV=production` を設定する。
8. `CORS_ALLOW_ORIGINS` に本番フロントエンド URL を設定する。
9. Deploy する。
10. `/` と `/docs` を確認する。

疎通確認:

```bash
curl https://YOUR_RENDER_SERVICE.onrender.com/
```

期待値:

```json
{"status":"ok"}
```

### render.yaml

このリポジトリには Render Blueprint の例として `render.yaml` を置いています。

```yaml
databases:
  - name: receipt-db
    databaseName: receipt_db
    user: receipt_user

services:
  - type: web
    name: receipt-api
    runtime: python
    buildCommand: pip install -e .
    startCommand: bash scripts/start_render.sh
    envVars:
      - key: APP_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: receipt-db
          property: connectionString
      - key: CORS_ALLOW_ORIGINS
        value: https://your-frontend.example.com
      - key: PYTHON_VERSION
        value: "3.12"
```

`CORS_ALLOW_ORIGINS` は実際のフロントエンド URL に差し替えます。

### よくある失敗

- `DATABASE_URL` が未設定で SQLite に接続してしまう
- Render PostgreSQL の External URL を誤って使い、同一リージョン内通信の想定から外れる
- `CORS_ALLOW_ORIGINS` にフロントエンド URL が入っていない
- `alembic upgrade head` が失敗してテーブルがない
- Start Command が `uvicorn app.main:app` だけになっていて migration と seed が実行されない
- 実際の DB 接続 URL やパスワードを README や `render.yaml` に直接書いてしまう

## Alembic

現在のモデルから初期 migration を作成済みです。Alembic はアプリ本体と同じ `DATABASE_URL` を使います。

一時 SQLite DB に migration を流す確認:

```bash
rm -f tmp_alembic_check.db
DATABASE_URL=sqlite:///./tmp_alembic_check.db uv run alembic upgrade head
rm -f tmp_alembic_check.db
```

本番 DB の schema 変更は必ず migration を追加してから `alembic upgrade head` で反映します。

## テスト

基本確認:

```bash
uv run python -m compileall app
```

テスト:

```bash
uv run pytest
```

利用可能なら実行:

```bash
uv run ruff check .
```

テストでは通常開発用の `receipts.db` を使わず、テスト用 SQLite DB に差し替えます。

## 開発時の注意

- 既存の `receipts.db` に実データが入っている可能性があるため、勝手に削除しないでください。
- OCR API、画像アップロード、画像保存、レシピ提案 API、認証、ユーザー管理、世帯管理はこのリポジトリでは実装しません。
- GitHub への push は行いません。
- ローカル commit は利用者から明示された場合のみ行います。
- `.env`、実際の `DATABASE_URL`、DB パスワード、API キー、秘密鍵、個人トークンをコミットしないでください。

## 関連ドキュメント

- `AGENTS.md`
- `docs/DATABASE_DESIGN.md`
- `docs/INVENTORY_IMPLEMENTATION_SPEC.md`
- `docs/API_SPEC.md`
- `docs/OCR_DB_INTERFACE.md`
- `docs/deploys/README.md`
