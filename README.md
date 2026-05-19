# レシート・家計簿・在庫データベース API

このリポジトリは、ユーザー確認済みのレシート購入履歴を保存する FastAPI バックエンドです。

OCR API ではありません。画像アップロード、OCR 処理、OCR 仮データ保存、Gemini 連携、OpenAI Structured Outputs、フロントエンド、レシピ提案 API、認証、ユーザー管理はこのリポジトリでは扱いません。

```text
OCR 結果 = 仮データ
DB 登録データ = ユーザー確認済みデータ
```

フロントエンドで購入日、店舗名、合計金額、明細、在庫対象、共通単位をユーザーが確認した後、その確定データだけを `POST /receipts` で登録します。

## 責務

この API は、家計簿、在庫管理、AI レシピ提案などの外部機能が共通で使える購入履歴と在庫情報を提供します。

| 利用先 | この API が提供するデータ |
| --- | --- |
| 家計簿 | 購入日、店舗名、カテゴリ、支払額、明細合計、差額 |
| 在庫管理 | 商品、数量、単位、保管場所、期限、在庫増減履歴 |
| 価格比較 | 商品ごとの共通単位あたり価格と最安購入店舗 |
| AI レシピ提案 | 在庫 API から取得できる商品名、数量、単位、期限 |

料理 AI やレシピ提案は、この API の外側で実装します。AI 側は `GET /inventory/balances` や `GET /inventory/batches` のレスポンスを利用します。

## 実装済み機能

| 区分 | 内容 |
| --- | --- |
| レシート管理 | 登録、一覧、詳細、削除 |
| 明細管理 | 購入時の商品名・数量と、在庫/レシピ用の正規化名・共通単位を保存 |
| 店舗名管理 | `receipts.store_name` を nullable で保存・返却 |
| 価格比較 | 指定商品の過去購入履歴から共通単位あたり最安店舗を取得 |
| 在庫反映 | レシート明細を在庫ロットへ反映 |
| 在庫残量 | 商品単位の現在在庫を取得 |
| 在庫ロット | 購入日、期限、保管場所、残量、ステータスを管理 |
| 在庫増減 | 消費、廃棄、手動調整と履歴取得 |

## 使用技術

- Python 3.12+
- FastAPI
- SQLAlchemy
- SQLite
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
inventory_locations
inventory_batches
inventory_operations
inventory_movements
```

レシート明細では、購入時の表記とアプリ内で扱う共通単位を分けます。

```text
raw_name              レシート上の商品名
normalized_name       アプリ内で扱う商品名
purchased_quantity    購入時の数量
purchased_unit        購入時の単位
base_quantity         在庫・レシピ用に変換した数量
base_unit             在庫・レシピ用の共通単位
```

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

`store_name` は nullable です。OCR で店名が取れない場合や、ユーザーが空欄で確定する場合を許容します。

## セットアップ

```bash
uv sync
```

必要に応じて仮想環境を有効化します。

```bash
source .venv/bin/activate
```

## 起動

```bash
uv run uvicorn app.main:app --reload
```

既定の URL:

```text
http://localhost:8000
```

開発環境では `http://localhost:5173` からの CORS を許可しています。

## API

### ヘルスチェック

```http
GET /
```

Response:

```json
{
  "status": "ok"
}
```

### レシート登録

```http
POST /receipts
```

フロントエンドでユーザー確認が完了したレシートだけを登録します。

Request:

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

Response:

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

`items_total` と `adjustment_amount` はサーバー側で計算します。

```text
items_total = sum(line_total)
adjustment_amount = total_amount - items_total
```

レシートには割引、ポイント、税、レジ袋、OCR 漏れなどがあるため、`total_amount == items_total` は必須にしません。

### レシート一覧

```http
GET /receipts
```

Query parameters:

| 名前 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `skip` | int | no | 取得開始位置 |
| `limit` | int | no | 取得件数 |
| `date_from` | int | no | 開始日。`YYYYMMDD` |
| `date_to` | int | no | 終了日。`YYYYMMDD` |
| `category_id` | int | no | カテゴリで絞り込み |
| `inventory_only` | bool | no | 在庫対象明細を含むレシートに絞り込み |

Response:

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

### レシート詳細

```http
GET /receipts/{receipt_id}
```

Response:

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

### レシート削除

```http
DELETE /receipts/{receipt_id}
```

Response:

```json
{
  "deleted": true,
  "id": 1
}
```

### 最安購入店舗取得

```http
GET /prices/cheapest
```

Query parameters:

| 名前 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `product_id` | int | yes | 対象商品 ID |
| `period_days` | int | no | 過去何日を対象にするか。既定値は `90` |

指定された `product_id` について、過去 `period_days` 日間の購入履歴から、共通単位あたり価格が最も安い購入明細と店名を返します。

比較には `line_total / base_quantity` を使います。単純に `line_total` が最小の明細は選びません。

対象外になる明細:

- `base_quantity` が `null`
- `base_quantity <= 0`
- `base_unit` が `null`
- `receipts.store_name` が `null`
- `product_id` が一致しない
- `purchased_at` が `period_days` の範囲外

Response:

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
    "receipt_item_id": 31
  }
}
```

該当データがない場合:

```json
{
  "product_id": 1,
  "product_name": "卵",
  "period_days": 90,
  "cheapest": null
}
```

### レシートを在庫へ反映

```http
POST /inventory/receipts/{receipt_id}/apply
```

`is_inventory_target = true` で、`product_id`、`base_quantity`、`base_unit` がそろっている明細を在庫ロットへ反映します。同じレシート明細は二重に在庫化しません。

Request:

```json
{
  "default_location_id": 1,
  "expires_at_by_receipt_item_id": {
    "31": "2026-05-20"
  },
  "idempotency_key": "receipt:12:apply-inventory"
}
```

Response:

```json
{
  "receipt_id": 12,
  "operation_id": 100,
  "applied_count": 1,
  "skipped_count": 0,
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
    }
  ]
}
```

### 在庫残量

```http
GET /inventory/balances
```

Query parameters:

| 名前 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `product_id` | int | no | 商品で絞り込み |
| `location_id` | int | no | 保管場所で絞り込み |
| `include_zero` | bool | no | 残量 0 の在庫も含める |

Response:

```json
{
  "items": [
    {
      "product_id": 1,
      "product_name": "卵",
      "quantity": "16.00",
      "unit": "個",
      "nearest_expires_at": "2026-05-20",
      "batch_count": 2
    }
  ]
}
```

### 在庫ロット一覧

```http
GET /inventory/batches
```

Query parameters:

| 名前 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `product_id` | int | no | 商品で絞り込み |
| `location_id` | int | no | 保管場所で絞り込み |
| `status` | string | no | `active` / `depleted` / `discarded` |
| `expires_before` | date | no | 指定日以前に期限が来るもの |
| `include_zero` | bool | no | 残量 0 の在庫も含める |

Response:

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

### 在庫増減登録

```http
POST /inventory/movements
```

`movement_type` は `consume`、`dispose`、`adjust` を受け取ります。`batch_id` を指定しない消費・廃棄では、期限が近いロットから順に差し引きます。

Request:

```json
{
  "product_id": 1,
  "movement_type": "consume",
  "quantity": "2.00",
  "unit": "個",
  "batch_id": null,
  "location_id": null,
  "reason": "夕食で使用",
  "occurred_at": "2026-05-13T18:30:00",
  "idempotency_key": "manual:consume:egg:20260513-001"
}
```

Response:

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
      "movement_id": 301,
      "batch_id": 201,
      "quantity_delta": "-2.00",
      "remaining_quantity": "8.00"
    }
  ]
}
```

### 在庫増減履歴

```http
GET /inventory/movements
```

Query parameters:

| 名前 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `product_id` | int | no | 商品で絞り込み |
| `batch_id` | int | no | 在庫ロットで絞り込み |
| `operation_id` | int | no | 操作単位で絞り込み |
| `movement_type` | string | no | 増減種別で絞り込み |
| `from_date` | date | no | 発生日の開始日 |
| `to_date` | date | no | 発生日の終了日 |
| `limit` | int | no | 取得件数。既定値は `100` |
| `offset` | int | no | 取得開始位置。既定値は `0` |

Response:

```json
{
  "items": [
    {
      "movement_id": 301,
      "operation_id": 101,
      "batch_id": 201,
      "product_id": 1,
      "product_name": "卵",
      "movement_type": "consume",
      "quantity_delta": "-2.00",
      "unit": "個",
      "reason": "夕食で使用",
      "occurred_at": "2026-05-13T18:30:00"
    }
  ]
}
```

## バリデーション

| 条件 | ステータス |
| --- | ---: |
| `items` が空 | 422 |
| `purchased_at` が実在しない日付 | 422 |
| `total_amount` が 0 未満 | 422 |
| `raw_name` が空 | 422 |
| `purchased_quantity` が 0 以下 | 422 |
| `line_total` が 0 未満 | 422 |
| `is_inventory_target = true` なのに `normalized_name` が空 | 422 |
| `is_inventory_target = true` なのに `base_quantity` または `base_unit` が空 | 422 |
| 存在しない `receipt_id` | 404 |
| 存在しない `product_id` または `category_id` | 400 |

在庫 API では、存在しない `receipt_id`、`product_id`、`batch_id` は `404`、存在しない `location_id`、単位不一致、在庫不足、無効な `status` は `400` として扱います。

`unit_price * purchased_quantity == line_total` は必須にしません。

`total_amount == sum(line_total)` も必須にしません。

## テスト

```bash
uv run python -m compileall app
uv run pytest
```

利用可能なら実行:

```bash
uv run ruff check .
```

テストでは通常開発用の `receipts.db` を使わず、一時 SQLite DB に差し替えます。

## 開発時の注意

- 既存の `receipts.db` に実データが入っている可能性があるため、勝手に削除しないでください。
- Alembic は導入していません。
- 本番 DB 対応は未実装です。
- GitHub への push は行いません。
- ローカル commit は利用者から明示された場合のみ行います。

## 関連ドキュメント

- `AGENTS.md`
- `docs/DATABASE_DESIGN.md`
- `docs/API_SPEC.md`
- `docs/OCR_DB_INTERFACE.md`
- `docs/CODEX_IMPLEMENTATION_PLAN.md`
- `docs/INVENTORY_IMPLEMENTATION_SPEC.md`
