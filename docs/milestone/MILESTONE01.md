# MILESTONE01: リクエストスキーマのバリデーション強化

## 目的

不正なレシートデータが DB に保存されないようにする。

このマイルストーンでは、リクエストの形式として明らかに不正な値を Pydantic 側で弾き、業務ルールとして不正な値を CRUD 層で弾く。

## 対象範囲

`items` を空配列にできないようにする。

`purchased_at` が `YYYYMMDD` 形式の整数であり、かつ実在する日付であることを検証する。

`purchased_quantity` が 0 より大きいことを検証する。

`line_total` と `total_amount` が 0 以上であることを検証する。

`is_inventory_target = true` の場合は、`normalized_name`、`base_quantity`、`base_unit` を必須にする。

## 想定変更ファイル

`app/schemas/` 配下のレシート関連スキーマ。

`app/crud/` 配下のレシート登録処理。

`app/common/date.py`。

必要に応じて、既存のルーティングファイル。

## 仕様

`items` は 1件以上必須とする。

`purchased_at` は整数として受け取る。値は `YYYYMMDD` として解釈する。

`20260428` は有効とする。

`20260230` は無効とする。

`20261301` は無効とする。

`purchased_quantity <= 0` の場合は `422 Unprocessable Entity` とする。

`line_total < 0` または `total_amount < 0` の場合は `422 Unprocessable Entity` とする。

`is_inventory_target = true` なのに `normalized_name`、`base_quantity`、`base_unit` のいずれかが空の場合は `422 Unprocessable Entity` とする。

`unit_price * purchased_quantity == line_total` は必須条件にしない。

`total_amount == sum(line_total)` は必須条件にしない。

## 受け入れ条件

空の `items` を送ると `422 Unprocessable Entity` になる。

実在しない `purchased_at` を送ると `422 Unprocessable Entity` になる。

`purchased_quantity <= 0` の場合は `422 Unprocessable Entity` になる。

`total_amount` と明細合計が一致しない場合でも登録できる。

正常な登録リクエストは、これまで通り登録できる。

## 実装上の注意

`date` の検証処理は各スキーマに直接散らさず、可能な限り `app/common/date.py` に寄せる。

このマイルストーンでは DB スキーマを変更しない。

このマイルストーンでは取得 API、削除 API、テスト基盤は追加しない。
