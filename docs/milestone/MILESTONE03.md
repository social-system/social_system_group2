# MILESTONE03: `GET /receipts/{receipt_id}` を追加

## 目的

1件のレシートを明細付きで取得できる API を追加する。

## 対象範囲

`GET /receipts/{receipt_id}` を追加する。

MILESTONE02 で追加した CRUD 関数を使う。

存在しない ID の場合は `404 Not Found` を返す。

## 想定変更ファイル

`app/routes/` 配下のレシートルート。

`app/schemas/` 配下のレスポンススキーマ。

必要に応じて、`app/crud/` 配下のレシート関連ファイル。

## レスポンス仕様

登録時のレスポンスと同じ形を返す。

```json
{
  "id": 1,
  "receipt_total": 500,
  "items": [
    {
      "id": 1,
      "item": "milk",
      "num": 1,
      "amount": 200,
      "total": 200,
      "date": 20260428,
      "ingredients": 1
    }
  ]
}
```

## エラー仕様

存在しない `receipt_id` の場合は `404 Not Found` を返す。

エラーメッセージは簡潔でよい。

## 受け入れ条件

登録済みレシートを `GET /receipts/{receipt_id}` で取得できる。

レスポンスに親レシートと明細が含まれる。

存在しない ID では `404 Not Found` になる。

既存の `POST /receipts` の動作を壊さない。

## 実装上の注意

API 層に DB の問い合わせ処理を直接書かない。

CRUD 層の関数を呼び出す。

このマイルストーンでは一覧取得、削除、テスト基盤は追加しない。
