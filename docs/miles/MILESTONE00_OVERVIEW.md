# MILESTONE00: 全体方針確認

## Codex指示

```text
AGENTS.md、README.md、docs/miles/README.md を読んでください。
このmileでは実装を行わず、現在のコード構成と今回の実装方針の差分だけを確認してください。
```

## 背景

現在、OCRは `raw_name` と `normalized_name` を返す。
ただし、OCRの `normalized_name` はAIが推定した商品名候補であり、DBが管理する正式な商品名ではない。

そのため、以下のような揺れが起きる。

```text
卵
たまご
タマゴ
白たまご
タマゴM
卵10個
```

この揺れをOCR側で吸収しようとすると、OCR機能が商品マスタを保持する必要が出る。
これは責務が不適切である。

## 方針

`product_id` の決定はDB側で行う。

```text
OCR:
  レシートから読める情報を抽出する
  raw_name と normalized_name 候補を返す
  product_id は決めない

DB:
  products と product_aliases を持つ
  raw_name / normalized_name 候補から product_id を解決する
  解決できない場合は候補を返す

Frontend:
  prepare API の結果を表示する
  未解決の商品だけユーザーに確認させる
```

## 最終的に追加する主な機能

```text
products.name_key
product_aliases.alias_name
product_aliases.alias_key
product_aliases.source
product_aliases.is_active
normalize_product_key()
resolve_product()
POST /receipts/prepare
GET /products/search
POST /product-aliases
```

## このmileで確認すること

Codexは以下を確認して報告する。

```text
現在の products モデルの有無
現在の product_aliases モデルの有無
現在の POST /receipts のrequest schema
現在の OCR response と DB request の差分
現在のテスト構成
Alembicなどmigration管理の有無
```

## このmileでは変更しないこと

```text
コード変更
テーブル変更
テスト変更
API追加
```

## 完了報告

以下の形式で報告する。

```text
確認したファイル:
現状のproducts/product_aliases構成:
現状のReceiptCreate構成:
実装時に注意すべき点:
次のmileで変更すべきファイル候補:
```
