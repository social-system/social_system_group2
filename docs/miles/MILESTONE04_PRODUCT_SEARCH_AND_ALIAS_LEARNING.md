# MILESTONE04: 商品検索APIとalias学習API

## Codex指示

```text
AGENTS.md、README.md、docs/miles/README.md、docs/miles/MILESTONE04_PRODUCT_SEARCH_AND_ALIAS_LEARNING.md を読んでください。
このmileでは、未解決商品をユーザーが選べるようにする商品検索APIと、ユーザー選択結果を product_aliases に保存するAPIをDB側に実装してください。
```

## 目的

`POST /receipts/prepare` で `product_id` を解決できなかった場合に、フロントエンドがユーザーへ候補選択UIを出せるようにする。

さらに、ユーザーが選んだ対応を `product_aliases` に保存し、次回以降は自動解決できるようにする。

## 実装対象

DBリポジトリのみを変更する。
OCRリポジトリは変更しない。

## API 1: 商品検索

```http
GET /products/search?query=ミソ&limit=10
```

### Query parameters

```text
query: 必須
limit: 任意。既定値10、最大50
```

### 処理

```text
query を normalize_product_key する
products.name_key と部分一致検索する
product_aliases.alias_key と部分一致検索して product へたどる
重複 product_id を除外する
候補を返す
```

高度な曖昧検索ライブラリは追加しない。
MVPではLIKE検索でよい。

### Response example

```json
{
  "query": "ミソ",
  "query_key": "みそ",
  "items": [
    {
      "product_id": 12,
      "name": "味噌",
      "default_base_unit": "g",
      "default_category_id": 1,
      "is_inventory_target": true
    },
    {
      "product_id": 45,
      "name": "即席味噌汁",
      "default_base_unit": "個",
      "default_category_id": 1,
      "is_inventory_target": true
    }
  ]
}
```

## API 2: alias学習

```http
POST /product-aliases
```

### Request example

```json
{
  "alias_name": "タマゴM 10コ",
  "product_id": 1,
  "source": "user_confirmed"
}
```

### 処理

```text
alias_name を normalize_product_key して alias_key を作る
product_id の存在確認をする
同じ alias_key が未登録なら product_aliases に登録する
同じ alias_key が同じ product_id に登録済みなら既存データを返す
同じ alias_key が別 product_id に登録済みなら 409 conflict を返す
```

### Response example

```json
{
  "id": 10,
  "alias_name": "タマゴM 10コ",
  "alias_key": "たまごm10こ",
  "product_id": 1,
  "product_name": "卵",
  "source": "user_confirmed",
  "created": true
}
```

既存の場合:

```json
{
  "id": 10,
  "alias_name": "タマゴM 10コ",
  "alias_key": "たまごm10こ",
  "product_id": 1,
  "product_name": "卵",
  "source": "user_confirmed",
  "created": false
}
```

競合の場合:

```json
{
  "detail": {
    "code": "alias_conflict",
    "message": "alias_key is already linked to another product"
  }
}
```

## フロントエンドの想定

フロントエンドは、prepare結果で未解決の商品があった場合だけ次を行う。

```text
1. product_candidates を表示する
2. 足りなければ GET /products/search を呼ぶ
3. ユーザーが商品を選ぶ
4. POST /product-aliases で alias を学習する
5. receipt.items[index].product_id と normalized_name を更新する
6. POST /receipts に送る
```

## テスト

最低限、以下を追加する。

```text
GET /products/search で商品名から検索できる
GET /products/search でaliasから商品を検索できる
GET /products/search は重複productを返さない
POST /product-aliases でaliasを登録できる
POST /product-aliases は alias_key を正規化する
同じalias_keyと同じproduct_idなら既存を返す
同じalias_keyと別product_idなら409になる
存在しないproduct_idなら404になる
登録後に resolve_product がaliasで解決できる
```

## 非ゴール

このmileでは以下を実装しない。

```text
商品新規作成API
alias上書きAPI
alias削除API
高度な曖昧検索
OCR側修正
```

## 実行コマンド

```bash
uv run python -m compileall app
uv run pytest
```

## 完了報告

以下を報告する。

```text
変更したファイル:
追加したAPI:
alias競合時の挙動:
追加・更新したテスト:
実行したコマンド:
テスト結果:
残TODO:
```
