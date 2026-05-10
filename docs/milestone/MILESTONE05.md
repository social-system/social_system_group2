# MILESTONE05: `GET /receipts` を追加

## 目的

登録済みレシートの一覧を取得できる API を追加する。

## 対象範囲

`GET /receipts` を追加する。

MILESTONE04 で追加した CRUD 関数を使う。

`skip`、`limit`、`date_from`、`date_to` をクエリパラメータとして受け取る。

## 想定変更ファイル

`app/routes/` 配下のレシートルート。

`app/schemas/` 配下の一覧レスポンススキーマ。

必要に応じて、`app/crud/` 配下のレシート関連ファイル。

## リクエスト仕様

基本形は次の通り。

```http
GET /receipts?skip=0&limit=50
```

日付絞り込みは次の通り。

```http
GET /receipts?date_from=20260401&date_to=20260430
```

`skip` の既定値は `0` とする。

`limit` の既定値は `50` とする。

`limit` の最大値は `100` 程度に制限する。

`date_from` と `date_to` は任意とする。

## レスポンス仕様

一覧では明細全件を返さない。

```json
[
  {
    "id": 1,
    "receipt_total": 500,
    "item_count": 2,
    "date_min": 20260428,
    "date_max": 20260428
  }
]
```

## エラー仕様

`skip` が 0 未満の場合は `422 Unprocessable Entity` とする。

`limit` が 1 未満、または最大値を超える場合は `422 Unprocessable Entity` とする。

`date_from` または `date_to` が実在しない日付の場合は `422 Unprocessable Entity` とする。

## 受け入れ条件

`GET /receipts` で一覧を取得できる。

一覧レスポンスに明細全件は含まれない。

`skip` と `limit` が有効に動作する。

`date_from` と `date_to` が有効に動作する。

不正なクエリパラメータは `422 Unprocessable Entity` になる。

既存の登録 API と詳細取得 API の動作を壊さない。

## 実装上の注意

API 層に DB の問い合わせ処理を直接書かない。

CRUD 層の関数を呼び出す。

このマイルストーンでは削除、テスト基盤は追加しない。
