# AGENTS.md

## 目的

このリポジトリは、ユーザー確認済みのレシート購入履歴を保存する FastAPI バックエンドである。

OCR API ではない。画像アップロードや OCR 処理は実装しない。

この DB は、家計簿、在庫管理、AI レシピ提案が共通で使える購入履歴を保存する。

## 最重要方針

OCR 結果をそのまま DB に登録しない。

```text
OCR 結果 = 仮データ
DB 登録データ = ユーザー確認済みデータ
```

DB API は、フロントエンドでユーザー確認が終わったデータだけを受け取る。

## 今回の大方針

今回は既存テーブル定義を作り直す。

既存の `receipt_total`、`item`、`num`、`amount`、`total`、`date`、`ingredients` を前提にした設計は廃止する。

新しい設計は `docs/DATABASE_DESIGN.md` に従う。

## 作業前に読む文書

Codex は作業前に必ず以下を読む。

```text
README.md
AGENTS.md
docs/DATABASE_DESIGN.md
docs/API_SPEC.md
docs/OCR_DB_INTERFACE.md
docs/CODEX_IMPLEMENTATION_PLAN.md
```

仕様に矛盾がある場合は、次の優先順位で判断する。

```text
docs/DATABASE_DESIGN.md
AGENTS.md
README.md
既存コード
```

## 実装するもの

```text
SQLAlchemy モデル
Pydantic request / response schema
レシート登録 API
レシート一覧 API
レシート詳細 API
レシート削除 API
テスト
```

## 実装しないもの

```text
認証
ユーザー管理
世帯管理
user_id によるデータ分離
OCR API
画像保存
OCR 仮データ保存
レシート更新 API
月別・カテゴリ別集計 API
在庫テーブル
レシピ提案 API
Alembic 導入
本番 DB 対応
外部 API 連携
```

## DB 設計方針

作成する主なテーブルは次の通り。

```text
receipts
receipt_items
accounting_categories
products
product_aliases
product_unit_conversions
```

`receipt_items` では、購入時の数量・単位と、在庫・レシピ用の共通数量・単位を分ける。

```text
purchased_quantity / purchased_unit
base_quantity / base_unit
```

`raw_name` はレシート上の商品名、`normalized_name` はアプリ内で扱う商品名である。

同じ商品名でも単位が違う場合は、別々の `receipt_items` として保存し、`base_quantity` と `base_unit` で集計できるようにする。

例:

```text
卵 1パック -> base_quantity 10, base_unit 個
卵 6個     -> base_quantity 6,  base_unit 個
```

## API 方針

既存 API パスは維持する。

```text
POST /receipts
GET /receipts
GET /receipts/{receipt_id}
DELETE /receipts/{receipt_id}
```

`POST /receipts` は確認済みデータだけを登録する。

`items_total` と `adjustment_amount` はサーバー側で計算する。

```text
items_total = sum(line_total)
adjustment_amount = total_amount - items_total
```

`total_amount == items_total` は必須にしない。

理由は、実レシートには割引、ポイント、税、レジ袋、OCR 漏れなどがあるためである。

## バリデーション方針

型や形式の誤りは `422 Unprocessable Entity` とする。

形式は正しいが、業務ルールとして不正な場合は `400 Bad Request` とする。

存在しない ID は `404 Not Found` とする。

主なルール:

```text
items は 1 件以上
purchased_at は実在する日付
total_amount は 0 以上
raw_name は空文字不可
purchased_quantity は 0 より大きい
line_total は 0 以上
is_inventory_target true の場合 normalized_name は必須
is_inventory_target true の場合 base_quantity は必須
is_inventory_target true の場合 base_unit は必須
```

`unit_price * purchased_quantity == line_total` は必須にしない。

`total_amount == sum(line_total)` も必須にしない。

## レイヤー責務

ルーターでは以下を行う。

```text
リクエスト受け取り
DB セッション取得
CRUD 関数呼び出し
HTTPException への変換
```

CRUD では以下を行う。

```text
DB 操作
存在確認
業務ルール検証
items_total / adjustment_amount の計算
```

Pydantic スキーマでは以下を行う。

```text
型検証
基本的な値検証
日付形式検証
```

SQLAlchemy モデルでは以下を行う。

```text
テーブル定義
リレーション定義
外部キー定義
```

## テスト方針

最低限、以下をテストする。

```text
登録成功
一覧取得成功
詳細取得成功
削除成功
items 空配列は 422
不正日付は 422
在庫対象なのに normalized_name が空なら 422
在庫対象なのに base_quantity が空なら 422
total_amount と items_total が違っても登録できる
存在しない receipt_id は 404
```

テストでは通常開発用の `receipts.db` を使わない。

一時 DB またはテスト専用 SQLite DB を使う。

## 実行コマンド

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

設定されていないツールは無理に導入しない。

## git 運用

作業開始時に確認する。

```bash
git status --short
git branch --show-current
```

ユーザーの未コミット変更を勝手に戻さない。

GitHub への push は行わない。

禁止:

```bash
git push
git push --force
git push --force-with-lease
```

ローカル commit は、利用者から明示された場合のみ行う。

## 完了報告

作業後は次を報告する。

```text
変更したファイル
実装したテーブル
実装した API
実行したテスト
失敗したテストがある場合は原因
残した TODO
```
