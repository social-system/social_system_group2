# MILESTONE05: POST /receiptsとの整合性強化

## Codex指示

```text
AGENTS.md、README.md、docs/miles/README.md、docs/miles/MILESTONE05_RECEIPT_CREATE_ALIGNMENT.md を読んでください。
このmileでは、POST /receipts が prepare API の receipt オブジェクトを安全に受け取れるように整合性を強化してください。
```

## 目的

フロントエンドが以下の流れで最小修正で動くようにする。

```text
OCR API response
  -> POST /receipts/prepare
  -> response.receipt を確認画面で編集
  -> POST /receipts に送信
```

## 実装対象

DBリポジトリのみを変更する。
OCRリポジトリは変更しない。

## 方針

`POST /receipts` は確認済みデータの登録APIである。
そのため、OCR専用項目を受け取らない。

一方で、prepare APIの `receipt` はそのまま送れる形にする。
このmileでは、`POST /receipts` のschemaとprepare APIの出力が一致しているかを確認・修正する。

## 確認する項目

`POST /receipts` が受け取るトップレベル項目:

```text
purchased_at
store_name
total_amount
items
```

`items` が受け取る項目:

```text
raw_name
normalized_name
product_id
category_id
purchased_quantity
purchased_unit
base_quantity
base_unit
unit_price
line_total
is_inventory_target
```

`POST /receipts` に送ってはいけない項目:

```text
status
warnings
confidence
category_name
resolution_status
resolution_source
product_candidates
validation_issues
```

## schema方針

DB登録用schemaでは、可能なら `extra="forbid"` を設定する。

理由は、OCR専用項目が誤ってDBへ流れ込むのを早期に検出するためである。

ただし、既存テストやFastAPIの挙動と大きく衝突する場合は、無理に入れずTODOに残す。

## product_idの扱い

`POST /receipts` では、`product_id` が指定されている場合は存在確認する。

`product_id` が null の場合も、MVPでは登録を許可する。
理由は、未解決でも購入履歴としては保存したい場合があるためである。

ただし、以下の注意点をテストまたはコメントで明示する。

```text
product_id が null の明細は、最安店APIや在庫反映APIの対象にならない場合がある
```

## normalized_nameの扱い

`product_id` が指定され、`normalized_name` が空の場合は、DB側で `products.name` を補完してよい。

`product_id` が null の場合は、OCRまたはユーザー入力の `normalized_name` をそのまま保存する。

## category_idの扱い

`category_id` が指定されている場合は存在確認する。

`category_id` が null の場合は登録を許可する。

`product_id` が指定され、`category_id` が空で、productに `default_category_id` がある場合は補完してよい。

## base_unit / base_quantityの扱い

`is_inventory_target = true` の場合、以下を必須にする現在方針を維持する。

```text
normalized_name
base_quantity
base_unit
```

`product_id` はMVPでは必須にしない。

## テスト

最低限、以下を追加または更新する。

```text
prepare APIの receipt を POST /receipts に送れる
status/warnings/confidence を POST /receipts に送ると弾く、または無視方針が明確になっている
product_id が存在する場合は登録できる
product_id が存在しない場合は400または404になる
product_id がnullでも購入履歴として登録できる
product_id 指定かつ normalized_name 空なら products.name で補完される
product_id 指定かつ category_id 空なら default_category_id で補完される
is_inventory_target true かつ base_quantity null は422
is_inventory_target true かつ base_unit null は422
```

## 非ゴール

このmileでは以下を実装しない。

```text
POST /receipts/prepare の大幅変更
商品検索APIの変更
OCR側修正
在庫API変更
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
POST /receipts schemaの最終形:
prepare APIとの整合性:
追加・更新したテスト:
実行したコマンド:
テスト結果:
残TODO:
```
