# CODEX_IMPLEMENTATION_PLAN.md

## 目的

既存の単純な `receipts` / `receipt_items` 構成を捨て、家計簿・在庫管理・AI レシピ提案に使える DB 構成へ作り直す。

今回は開発初期のため、既存テーブルとの互換性を維持しない。

この文書は初期 DB / API 実装の計画である。Render + Render PostgreSQL へのデプロイ対応は `docs/deploys/` の STEP 文書を優先する。

## Codex への前提指示

作業前に必ず次を読む。

```text
README.md
AGENTS.md
docs/DATABASE_DESIGN.md
docs/API_SPEC.md
docs/OCR_DB_INTERFACE.md
```

実装では、既存コードの責務分離をできるだけ維持する。

```text
app/receipts/models.py       SQLAlchemy モデル
app/schemas/                 Pydantic スキーマ
app/crud/                    DB 操作と業務ルール
app/routes/                  FastAPI ルーター
tests/                       API テスト
```

## 実装範囲

今回実装するもの:

```text
新テーブル定義
新リクエスト・レスポンススキーマ
POST /receipts
GET /receipts
GET /receipts/{receipt_id}
DELETE /receipts/{receipt_id}
テスト
```

今回実装しないもの:

```text
OCR API
画像アップロード
OCR 仮データ保存
レシート更新 API
月別集計 API
在庫テーブル
レシピ提案 API
認証
ユーザー管理
Alembic 導入（初期実装時は対象外。Render対応では `docs/deploys/` で扱う）
本番 DB 対応（初期実装時は対象外。Render対応では `docs/deploys/` で扱う）
```

## 作業単位

### STEP 1: モデルを作り直す

対象:

```text
app/receipts/models.py
```

作成するモデル:

```text
Receipt
ReceiptItem
AccountingCategory
Product
ProductAlias
ProductUnitConversion
```

古いカラムは使わない。

古いカラム:

```text
receipt_total
item
num
amount
total
date
ingredients
```

新しいカラムに置き換える。

### STEP 2: Pydantic スキーマを作り直す

対象:

```text
app/schemas/receipts_requests.py
app/schemas/receipts_responses.py
```

作成する主なスキーマ:

```text
ReceiptItemCreate
ReceiptCreate
ReceiptItemResponse
ReceiptSummaryResponse
ReceiptDetailResponse
DeleteReceiptResponse
```

`purchased_at` は API では `YYYYMMDD` の整数で扱い、DB 保存時に `date` へ変換する。

Decimal の JSON 表現は、プロジェクト内で統一する。推奨は文字列。

### STEP 3: バリデーションを実装する

主なルール:

```text
items は 1 件以上
purchased_at は実在する日付
total_amount は 0 以上
raw_name は空文字不可
purchased_quantity は 0 より大きい
line_total は 0 以上
is_inventory_target true の場合、normalized_name / base_quantity / base_unit が必須
product_id が指定された場合、存在確認する
category_id が指定された場合、存在確認する
```

`unit_price * purchased_quantity == line_total` は必須条件にしない。

`total_amount == sum(line_total)` も必須条件にしない。

### STEP 4: 登録 CRUD を作り直す

対象:

```text
app/crud/receipts_create.py
```

処理:

```text
ReceiptCreate を受け取る
category_id / product_id の存在を確認する
items_total を計算する
adjustment_amount を計算する
Receipt を作成する
ReceiptItem を作成する
commit する
summary response を返す
```

フロントから送られた `items_total` や `adjustment_amount` は使わない。

### STEP 5: 取得・削除 CRUD を作り直す

対象:

```text
app/crud/receipts.py
```

実装:

```text
get_receipt_detail
list_receipts
delete_receipt
```

一覧では、最低限次の絞り込みに対応する。

```text
date_from
date_to
skip
limit
```

`category_id` と `inventory_only` は余裕があれば実装する。難しければ TODO として残してよい。

### STEP 6: ルーターを更新する

対象:

```text
app/routes/receipts_create.py
app/routes/receipts.py
```

既存 API パスは維持する。

```text
POST /receipts
GET /receipts
GET /receipts/{receipt_id}
DELETE /receipts/{receipt_id}
```

### STEP 7: テストを更新する

対象:

```text
tests/
```

最低限のテスト:

```text
POST /receipts が登録できる
GET /receipts が一覧を返す
GET /receipts/{id} が詳細を返す
DELETE /receipts/{id} が削除できる
items が空なら 422
不正な purchased_at は 422
在庫対象なのに normalized_name が空なら 422
在庫対象なのに base_quantity が空なら 422
明細合計と total_amount が違っても登録できる
存在しない receipt_id は 404
```

## 完了条件

次が通ること。

```bash
uv run python -m compileall app
uv run pytest
```

## 作業時の注意

開発用 `receipts.db` に実データが入っている可能性があるため、勝手に削除しない。

ただし、テストでは一時 DB またはテスト専用 DB を使う。

既存 DB を新スキーマで作り直す必要がある場合は、利用者に確認するか、README に手順を書く。

## 最終報告に含める内容

Codex は作業後、次を報告する。

```text
変更したファイル
実装したテーブル
実装した API
実行したテスト
残した TODO
```
