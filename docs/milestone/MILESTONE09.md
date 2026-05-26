# MILESTONE09: 登録、取得、削除、異常系のテストを追加

## 目的

主要 API の正常系と異常系を自動テストで確認できる状態にする。

## 対象範囲

`POST /receipts` の正常系と異常系をテストする。

`GET /receipts/{receipt_id}` の正常系と異常系をテストする。

`GET /receipts` の正常系と絞り込みをテストする。

`DELETE /receipts/{receipt_id}` の正常系と異常系をテストする。

## 想定変更ファイル

`tests/test_receipts.py`

必要に応じて `tests/conftest.py`

## テストケース

正常なレシートを登録できる。

`total_amount` と明細合計が違っても登録できる。

`unit_price * purchased_quantity` と `line_total` が違っても登録できる。

`items` が空の場合は `422 Unprocessable Entity` になる。

`purchased_at` が `20260230` の場合は `422 Unprocessable Entity` になる。

登録済みレシートを詳細取得できる。

存在しない ID を詳細取得すると `404 Not Found` になる。

レシート一覧を取得できる。

`skip` と `limit` が効く。

`date_from` と `date_to` が効く。

登録済みレシートを削除できる。

削除後に詳細取得すると `404 Not Found` になる。

存在しない ID を削除すると `404 Not Found` になる。

## 受け入れ条件

`uv run pytest` が成功する。

主要 API の正常系が確認されている。

主要 API の異常系が確認されている。

テスト実行で開発用 `receipts.db` が変更されない。

## 実装上の注意

テストは API 経由で確認することを優先する。

DB の内部状態を確認するテストを追加してもよいが、API の期待動作が主である。

テストデータは各テストで独立させる。

このマイルストーンでは、新機能を追加しない。既存機能の確認を目的とする。
