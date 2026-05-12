# レシート・家計簿・在庫データベース API

このリポジトリは、レシート OCR の結果を直接保存するためのものではなく、ユーザーが確認した購入履歴を保存するバックエンドです。

OCR は誤読や欠損を含む可能性があるため、OCR 結果は一度フロントエンドに返し、ユーザーが修正・確認した後で、この API に登録します。

```text
レシート画像
  -> OCR API
  -> Gemini で画像読解
  -> OpenAI Structured Outputs で仮 JSON 化
  -> フロントエンドでユーザー確認
  -> この DB API に確定データとして登録
  -> 在庫対象の商品を在庫へ反映
  -> 家計簿・在庫管理・AI レシピ提案で利用
```

## この API の責務

この API の責務は、確認済みの購入履歴と現在在庫を保存し、次の機能から使える形にすることです。

| 利用先 | 必要なデータ |
| --- | --- |
| 家計簿 | 購入日、店舗名、カテゴリ、金額 |
| 在庫管理 | 商品名、数量、単位、保管場所、期限、増減履歴 |
| AI レシピ提案 | 正規化された商品名、現在数量、共通単位、期限 |

この API は OCR を実行しません。画像ファイルも保存しません。料理AIもこの API の内部では実行せず、外部のAI機能が在庫APIのレスポンスを読んで献立やレシピを提案する構成です。

## 現在実装されている機能

| 区分 | 内容 |
| --- | --- |
| レシート管理 | 確認済みレシートの登録、一覧、詳細、削除 |
| 明細管理 | 購入時の商品名・数量と、在庫/レシピ用の正規化名・共通単位を保存 |
| 家計簿連携 | 購入日、店舗、カテゴリ、支払額、明細合計、差額を取得可能 |
| 在庫反映 | レシート明細のうち在庫対象の商品を在庫ロットへ反映 |
| 在庫残量 | 商品単位の現在在庫を取得 |
| 在庫ロット | 購入日、期限、保管場所、残量、ステータスをロット単位で管理 |
| 在庫増減履歴 | 購入反映、消費、廃棄、手動調整の履歴を保存 |

## 外部機能との連携方針

このバックエンドは、外部機能に対して「確定済みデータ」と「現在在庫」を提供するデータAPIです。OCR、画像保存、料理AI、フロントエンド画面そのものは別コンポーネントとして扱います。

```text
フロントエンド
  -> OCR API から仮データを受け取る
  -> ユーザーが購入日、店舗、金額、明細、在庫対象、共通単位を確認する
  -> POST /receipts に確定データを送る
  -> 必要に応じて POST /inventory/receipts/{receipt_id}/apply を呼ぶ
  -> GET /receipts / GET /inventory/* で画面表示する

料理AI・レシピ提案
  -> GET /inventory/balances で使える食材と数量を取得する
  -> GET /inventory/batches で期限の近い食材を取得する
  -> 外部AI側でレシピ候補を生成する
  -> 使用後は POST /inventory/movements で消費量を在庫から差し引く
```

フロントエンドからの利用を想定し、開発環境では `http://localhost:5173` からの CORS を許可しています。

## 使用技術

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- pytest
- uv

## 設計方針

開発初期のため、既存テーブルとの互換性は維持せず、テーブル定義を作り直します。

現時点では一人用のローカルアプリとして扱うため、認証、ユーザー管理、世帯管理、`user_id` によるデータ分離は実装しません。

商品名は、レシート上の表記とアプリ内で扱う表記を分けます。

```text
raw_name           レシート上の商品名
normalized_name    アプリ内で扱う商品名
```

数量と単位も、購入時の表記と在庫・レシピ用の共通単位を分けます。

```text
purchased_quantity / purchased_unit    購入時の数量と単位
base_quantity / base_unit              在庫・レシピ用に変換した数量と単位
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

## 主要テーブル

レシート、商品、カテゴリの詳細は `docs/DATABASE_DESIGN.md` を参照してください。在庫管理の詳細は `docs/INVENTORY_IMPLEMENTATION_SPEC.md` を参照してください。

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

Response:

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

`items_total` と `adjustment_amount` はサーバー側で計算します。

```text
items_total = sum(item.line_total)
adjustment_amount = total_amount - items_total
```

レシートには割引、ポイント利用、税、OCR 漏れがあるため、`total_amount == items_total` は必須条件にしません。

### レシート一覧取得

```http
GET /receipts
```

Query parameters:

| 名前 | 内容 |
| --- | --- |
| `skip` | 取得開始位置 |
| `limit` | 取得件数 |
| `date_from` | 開始日。`YYYYMMDD` 形式 |
| `date_to` | 終了日。`YYYYMMDD` 形式 |
| `category_id` | カテゴリで絞り込む場合に指定 |
| `inventory_only` | `true` の場合、在庫対象を含むレシートだけを対象にする |

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
    "item_count": 2
  }
]
```

### レシート詳細取得

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

Decimal は JSON では文字列または数値のどちらでもよいですが、プロジェクト内で統一してください。推奨は文字列です。

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

### レシートを在庫へ反映

```http
POST /inventory/receipts/{receipt_id}/apply
```

レシート明細のうち、`is_inventory_target = true` で、`product_id`、`base_quantity`、`base_unit` がそろっている明細を在庫ロットへ反映します。同じレシート明細は二重に在庫化しません。

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
  "skipped_count": 1,
  "items": [
    {
      "receipt_item_id": 31,
      "product_id": 1,
      "product_name": "卵",
      "quantity": "10.00",
      "unit": "個",
      "batch_id": 201,
      "status": "applied"
    },
    {
      "receipt_item_id": 32,
      "product_name": "洗剤",
      "status": "skipped",
      "reason": "not_inventory_target"
    }
  ]
}
```

### 在庫残量取得

```http
GET /inventory/balances
```

Query parameters:

| 名前 | 内容 |
| --- | --- |
| `product_id` | 商品で絞り込む場合に指定 |
| `location_id` | 保管場所で絞り込む場合に指定 |
| `include_zero` | `true` の場合、残量 0 の在庫も含める |

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

### 在庫ロット一覧取得

```http
GET /inventory/batches
```

Query parameters:

| 名前 | 内容 |
| --- | --- |
| `product_id` | 商品で絞り込む場合に指定 |
| `location_id` | 保管場所で絞り込む場合に指定 |
| `status` | `active` / `depleted` / `discarded` |
| `expires_before` | 指定日以前に期限が来るもの |
| `include_zero` | `true` の場合、残量 0 の在庫も含める |

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

消費、廃棄、手動調整を登録します。`batch_id` を指定しない消費・廃棄では、期限が近いロットから順に差し引きます。現在の実装では `movement_type` は `consume`、`dispose`、`adjust` を受け取ります。`adjust` は正の数量なら手動追加、負の数量なら手動減少として扱います。

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

### 在庫増減履歴取得

```http
GET /inventory/movements
```

Query parameters:

| 名前 | 内容 |
| --- | --- |
| `product_id` | 商品で絞り込む場合に指定 |
| `batch_id` | 在庫ロットで絞り込む場合に指定 |
| `operation_id` | 操作単位で絞り込む場合に指定 |
| `movement_type` | 増減種別で絞り込む場合に指定 |
| `from_date` | 発生日の開始日 |
| `to_date` | 発生日の終了日 |
| `limit` | 取得件数。既定値は 100 |
| `offset` | 取得開始位置。既定値は 0 |

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

`unit_price * purchased_quantity == line_total` は必須条件にしません。税込価格、まとめ割、量り売り、小数数量でずれることがあるためです。

在庫APIでは、存在しない `receipt_id`、`product_id`、`batch_id` は `404`、存在しない `location_id`、単位不一致、在庫不足、無効な `status` は `400` として扱います。型や `quantity = 0` などのPydanticで検出できる入力不備は `422` です。

## 料理AI連携で使う主なデータ

料理AIやレシピ提案機能は、このバックエンドの外側で実装します。AI側へ渡す候補データは、在庫APIから取得します。

| 目的 | API | 利用する主な項目 |
| --- | --- | --- |
| 使える食材一覧 | `GET /inventory/balances` | `product_name`, `quantity`, `unit`, `nearest_expires_at` |
| 期限優先の提案 | `GET /inventory/batches` | `expires_at`, `current_quantity`, `location_name` |
| 使用後の在庫反映 | `POST /inventory/movements` | `movement_type=consume`, `quantity`, `unit`, `reason` |

AIに渡す場合も、購入時単位ではなく `base_quantity` / `base_unit` から作られた在庫単位を使います。たとえば「卵 1パック」は、在庫API上では「卵 10.00 個」として扱います。

## セットアップ

```bash
uv sync
```

必要に応じて仮想環境を有効化します。

```bash
source .venv/bin/activate
```

## 起動方法

```bash
uv run uvicorn app.main:app --reload
```

通常は以下で起動します。

```text
http://localhost:8000
```

## テスト

```bash
uv run pytest
```

テストでは通常開発用の `receipts.db` を使わず、テスト用 SQLite DB に差し替えます。

## Codex で実装する場合

Codex に作業させる前に、以下を確認させてください。

```text
AGENTS.md
docs/DATABASE_DESIGN.md
docs/CODEX_IMPLEMENTATION_PLAN.md
```

今回の方針ではテーブル定義を作り直すため、既存 DB の互換性維持は不要です。ただし、実レシートデータが入っている `receipts.db` を勝手に削除しないでください。
