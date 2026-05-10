# MILESTONE07: `DELETE /receipts/{receipt_id}` を追加

## 目的

誤登録したレシートを削除できる API を追加する。

## 対象範囲

`DELETE /receipts/{receipt_id}` を追加する。

MILESTONE06 で追加した CRUD 関数を使う。

存在しない ID の場合は `404 Not Found` を返す。

## 想定変更ファイル

`app/routes/` 配下のレシートルート。

`app/schemas/` 配下の削除レスポンススキーマ。

必要に応じて、`app/crud/` 配下のレシート関連ファイル。

## レスポンス仕様

削除成功時は、次のようなレスポンスを返す。

```json
{
  "deleted": true,
  "id": 1
}
```

## エラー仕様

存在しない `receipt_id` の場合は `404 Not Found` を返す。

## 受け入れ条件

登録済みレシートを `DELETE /receipts/{receipt_id}` で削除できる。

削除後に `GET /receipts/{receipt_id}` を呼ぶと `404 Not Found` になる。

存在しない ID を削除しようとした場合は `404 Not Found` になる。

既存の登録 API、詳細取得 API、一覧取得 API の動作を壊さない。

## 実装上の注意

API 層に DB の削除処理を直接書かない。

CRUD 層の関数を呼び出す。

このマイルストーンではテスト基盤は追加しない。
