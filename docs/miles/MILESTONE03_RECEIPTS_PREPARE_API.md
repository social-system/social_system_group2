# MILESTONE03: POST /receipts/prepare API

## Codex指示

```text
AGENTS.md、README.md、docs/miles/README.md、docs/miles/MILESTONE03_RECEIPTS_PREPARE_API.md を読んでください。
このmileでは、OCRレスポンスを受け取り、DB登録に近い形へ変換する POST /receipts/prepare をDB側に実装してください。
```

## 目的

フロントエンド修正を最小限にする。

フロントエンドが `normalized_name -> product_id` の対応表を持たなくてよいように、DB側で商品解決を行う。

## API

```http
POST /receipts/prepare
```

## 入力

OCR API のレスポンスをできるだけそのまま受け取る。

例:

```json
{
  "status": "needs_confirmation",
  "store_name": "サンプルスーパー",
  "purchased_at": "2026-05-12",
  "total_amount": 636,
  "items": [
    {
      "raw_name": "タマゴM 10コ",
      "normalized_name": "たまご",
      "category_name": "食費",
      "purchased_quantity": 1,
      "purchased_unit": "パック",
      "base_quantity": 10,
      "base_unit": "個",
      "unit_price": 238,
      "line_total": 238,
      "is_inventory_target": true,
      "confidence": 0.82,
      "warnings": []
    }
  ],
  "warnings": []
}
```

## 入力schema方針

prepare用schemaはOCR寄りにする。

```text
status は受け取るがDB登録データには含めない
warnings は受け取るがDB登録データには含めない
confidence は受け取るがDB登録データには含めない
category_name は受け取るが、可能なら category_id に変換する
purchased_at は string と int の両方を受け付ける
```

`extra="ignore"` を使ってよい。
ただし、DB登録用schemaでは `extra="forbid"` を検討する。

## purchased_at変換

以下を受け付ける。

```text
"2026-05-12"
20260512
null
```

変換後はDB登録用の `YYYYMMDD` 整数にする。

```text
"2026-05-12" -> 20260512
20260512 -> 20260512
null -> null
```

不正日付の場合は、prepare API自体を失敗させるより、`validation_issues` に入れて返す。

理由は、prepare APIは確認画面用であり、ユーザー修正に回すためである。

## 出力

重要: `receipt` はできる限りそのまま `POST /receipts` に送れる形にする。

そのため、`receipt.items` の中には `resolution_status` や `product_candidates` を入れない。
解決状況は `item_resolutions` に分ける。

Response例:

```json
{
  "receipt": {
    "store_name": "サンプルスーパー",
    "purchased_at": 20260512,
    "total_amount": 636,
    "items": [
      {
        "raw_name": "タマゴM 10コ",
        "normalized_name": "卵",
        "product_id": 1,
        "category_id": 1,
        "purchased_quantity": 1,
        "purchased_unit": "パック",
        "base_quantity": 10,
        "base_unit": "個",
        "unit_price": 238,
        "line_total": 238,
        "is_inventory_target": true
      }
    ]
  },
  "item_resolutions": [
    {
      "index": 0,
      "resolution_status": "resolved",
      "resolution_source": "normalized_name_alias",
      "product_id": 1,
      "product_name": "卵",
      "product_candidates": [],
      "issues": []
    }
  ],
  "warnings": [],
  "validation_issues": []
}
```

未解決の場合:

```json
{
  "receipt": {
    "store_name": "サンプルスーパー",
    "purchased_at": 20260512,
    "total_amount": 636,
    "items": [
      {
        "raw_name": "ミソ",
        "normalized_name": "ミソ",
        "product_id": null,
        "category_id": null,
        "purchased_quantity": 1,
        "purchased_unit": "個",
        "base_quantity": null,
        "base_unit": null,
        "unit_price": 198,
        "line_total": 198,
        "is_inventory_target": true
      }
    ]
  },
  "item_resolutions": [
    {
      "index": 0,
      "resolution_status": "unresolved",
      "resolution_source": "candidate_only",
      "product_id": null,
      "product_name": null,
      "product_candidates": [
        {
          "product_id": 12,
          "name": "味噌",
          "default_base_unit": "g"
        },
        {
          "product_id": 45,
          "name": "即席味噌汁",
          "default_base_unit": "個"
        }
      ],
      "issues": ["product_not_resolved"]
    }
  ],
  "warnings": [],
  "validation_issues": []
}
```

## 処理内容

```text
1. OCRレスポンスを受け取る
2. purchased_at をDB用YYYYMMDDへ変換する
3. status, warnings, confidence などDB登録不要項目を分離する
4. 各itemについて resolve_product() を呼ぶ
5. 解決できた場合は product_id、products.name、default_category_id、default_base_unit を反映する
6. category_name があれば accounting_categories.name と照合して category_id に変換する
7. receipt オブジェクトと item_resolutions を返す
```

## normalized_nameの扱い

商品が解決できた場合、`receipt.items[].normalized_name` は `products.name` に置き換える。

商品が解決できなかった場合、OCR由来の `normalized_name` を残す。

## base_unit / base_quantityの扱い

prepare APIでは、勝手に数量変換を行わない。

ただし、商品が解決でき、`base_unit` が空で、`products.default_base_unit` がある場合は、`base_unit` に既定単位を補完してよい。

`base_quantity` は、換算ルールなしに推測しない。

## validation_issues

prepare APIでは、DB登録時に問題になりそうな項目を `validation_issues` として返す。

例:

```text
purchased_at_missing
total_amount_missing
items_empty
raw_name_missing
purchased_quantity_missing
line_total_missing
inventory_target_missing
inventory_target_without_base_quantity
inventory_target_without_base_unit
```

prepare APIでは原則として 200 を返し、ユーザー修正に回す。
ただし、JSONとして壊れている場合や型が極端に不正な場合は 422 でよい。

## テスト

最低限、以下を追加する。

```text
OCR形式のJSONを受け取れる
status/warnings/confidence が receipt から除外される
purchased_at "YYYY-MM-DD" が YYYYMMDD int に変換される
product_aliases によって product_id が解決される
products.name_key によって product_id が解決される
解決済みの場合 normalized_name が products.name に置き換わる
解決不能の場合 product_candidates が返る
receipt は POST /receipts に近い形で返る
不正日付は validation_issues に入る
```

## 非ゴール

このmileでは以下を実装しない。

```text
GET /products/search
POST /product-aliases
POST /receipts の大幅変更
OCRリポジトリ修正
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
prepare APIの入出力例:
追加・更新したテスト:
実行したコマンド:
テスト結果:
残TODO:
```
