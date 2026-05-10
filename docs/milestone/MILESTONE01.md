# MILESTONE01: リクエストスキーマのバリデーション強化

## 目的

不正なレシートデータが DB に保存されないようにする。

このマイルストーンでは、リクエストの形式として明らかに不正な値を Pydantic 側で弾き、レシートとして矛盾している値を CRUD 層で弾く。

## 対象範囲

`items` を空配列にできないようにする。

`date` が `YYYYMMDD` 形式の整数であり、かつ実在する日付であることを検証する。

`num * amount == total` を検証する。

既存の `receipt_total == sum(items.total)` の検証は維持する。

## 想定変更ファイル

`app/schemas/` 配下のレシート関連スキーマ。

`app/crud/` 配下のレシート登録処理。

`app/common/date.py`。

必要に応じて、既存のルーティングファイル。

## 仕様

`items` は 1件以上必須とする。

`date` は整数として受け取る。値は `YYYYMMDD` として解釈する。

`20260428` は有効とする。

`20260230` は無効とする。

`20261301` は無効とする。

`num * amount != total` の場合は `400 Bad Request` とする。

`receipt_total != sum(items.total)` の場合は `400 Bad Request` とする。

## 受け入れ条件

空の `items` を送ると `422 Unprocessable Entity` になる。

実在しない `date` を送ると `422 Unprocessable Entity` になる。

`num * amount` と `total` が一致しない場合は `400 Bad Request` になる。

`receipt_total` と明細合計が一致しない場合は、これまで通り `400 Bad Request` になる。

正常な登録リクエストは、これまで通り登録できる。

## 実装上の注意

`date` の検証処理は各スキーマに直接散らさず、可能な限り `app/common/date.py` に寄せる。

このマイルストーンでは DB スキーマを変更しない。

このマイルストーンでは取得 API、削除 API、テスト基盤は追加しない。
