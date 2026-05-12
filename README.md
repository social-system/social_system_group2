# レシート・家計簿データベース API

このリポジトリは、レシート OCR の結果を直接保存するためのものではなく、ユーザーが確認した購入履歴を保存するバックエンドです。

OCR は誤読や欠損を含む可能性があるため、OCR 結果は一度フロントエンドに返し、ユーザーが修正・確認した後で、この API に登録します。

```text
レシート画像
  -> OCR API
  -> Gemini で画像読解
  -> OpenAI Structured Outputs で仮 JSON 化
  -> フロントエンドでユーザー確認
  -> この DB API に確定データとして登録
  -> 家計簿・在庫管理・AI レシピ提案で利用
```

## この API の責務

この API の責務は、確認済みの購入履歴を保存し、次の機能から使える形にすることです。

| 利用先 | 必要なデータ |
| --- | --- |
| 家計簿 | 購入日、店舗名、カテゴリ、金額 |
| 在庫管理 | 商品名、数量、単位、在庫対象かどうか |
| AI レシピ提案 | 正規化された商品名、共通単位の数量 |

この API は OCR を実行しません。画像ファイルも保存しません。

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

詳細は `docs/DATABASE_DESIGN.md` を参照してください。

```text
receipts
receipt_items
accounting_categories
products
product_aliases
product_unit_conversions
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
