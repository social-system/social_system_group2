# OCR_DB_INTERFACE.md

## 目的

OCR API と DB API の境界を明確にする。

OCR API は仮データを返し、DB API はユーザー確認済みデータだけを保存する。

## 基本フロー

```text
レシート画像
  -> OCR API
  -> OCR 仮データ
  -> DB API POST /receipts/prepare
  -> DB 側で product_id 解決、日付変換、OCR 専用項目除去
  -> フロントエンド確認画面
  -> ユーザー修正
  -> DB API POST /receipts
  -> 確定データ保存
  -> GET /prices/cheapest で最安店表示
```

OCR API は `product_id`、`category_id`、`product_aliases` を扱わない。OCR の `normalized_name` は AI が推定した商品名候補であり、DB が管理する正式名 `products.name` と一致する保証はない。

DB API の `POST /receipts/prepare` は、OCR 仮データを登録前の確認画面で扱いやすい形に整える。`raw_name` / `normalized_name` を `products.name_key` と `product_aliases.alias_key` に照合し、解決できた場合だけ `product_id` を入れる。解決できない場合は `product_id = null` として `unresolved_items` に含める。

## OCR API が返す仮データ

OCR API は、不明な値を `null` として返してよい。

例:

```json
{
  "status": "needs_confirmation",
  "purchased_at": "2026-05-12",
  "store_name": "サンプルスーパー",
  "total_amount": 636,
  "items": [
    {
      "raw_name": "タマゴM 10コ",
      "normalized_name": "卵",
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
    },
    {
      "raw_name": "センザイ",
      "normalized_name": null,
      "category_name": null,
      "purchased_quantity": 1,
      "purchased_unit": "個",
      "base_quantity": null,
      "base_unit": null,
      "unit_price": 398,
      "line_total": 398,
      "is_inventory_target": false,
      "confidence": 0.76,
      "warnings": ["商品カテゴリが不明です"]
    }
  ],
  "warnings": [
    "一部の項目は確認が必要です"
  ]
}
```

## DB API に送る確定データ

通常は OCR 仮データを直接変換せず、`POST /receipts/prepare` の `receipt` をユーザー確認後に `POST /receipts` へ渡す。

DB API に送る時点では、在庫対象データに必要な項目を埋める。

`POST /receipts` は、`product_id = null` の明細について保存前にもう一度商品解決を試みる。ただし使うのは `POST /receipts/prepare` と同じ安全な完全一致だけである。信頼済み alias または商品名キーに一致しない場合、候補が存在しても `product_id = null` のまま保存する。

例:

```json
{
  "purchased_at": 20260512,
  "store_name": "サンプルスーパー",
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
    },
    {
      "raw_name": "センザイ",
      "normalized_name": "洗剤",
      "product_id": null,
      "category_id": 2,
      "purchased_quantity": 1,
      "purchased_unit": "個",
      "base_quantity": null,
      "base_unit": null,
      "unit_price": 398,
      "line_total": 398,
      "is_inventory_target": false
    }
  ]
}
```

## 重要な境界

DB API は OCR の信頼度や警告を保存しない。

理由は、この DB の責務が「確認済み購入履歴の保存」だからである。

将来、OCR 結果の再編集や監査が必要になった場合は、別途 `receipt_ocr_drafts` テーブルを追加する。

## product_aliases による表記揺れ吸収

`product_aliases` は OCR 名やユーザー入力名を商品マスタへ対応させる。

例:

```text
タマゴM 10コ -> 卵
ミソ -> 味噌
```

未解決商品に対してユーザーが商品を選択したら、フロントエンドは `POST /product-aliases` で alias を登録する。次回以降の `POST /receipts/prepare` では、同じ `alias_key` から `product_id` が解決される。

## 自動登録ゲート

人間の確認を最小化する場合でも、OCR 仮データを無条件に `POST /receipts` へ送らない。

代わりに `POST /receipts/auto-create` を使う。この API は `POST /receipts/prepare` と同じ整形を行い、次のような安全条件を満たした場合だけ保存する。

```text
未解決商品がない
validation_issues がない
OCR warnings がない
各明細の confidence が閾値以上
在庫対象明細の product_id / base_quantity / base_unit が揃っている
OCR metadata が review を要求していない
total_amount と line_total 合計が一致する
```

条件を満たさない場合は保存せず、`auto_registration.reasons` に理由を返す。

OCR API が `ocr_metadata` を返す場合、DB API はそれを確定データとして保存しない。自動登録可否の判断材料としてのみ使う。

## 最安店表示との接続

`GET /prices/cheapest` は `receipt_items.product_id` が一致する購入履歴だけを対象にする。

比較には以下を使う。

```text
price_per_base_unit = line_total / base_quantity
```

そのため、最安店表示に使うには `product_id`、`store_name`、`base_quantity`、`base_unit` が必要である。`product_id` 未解決の商品は購入履歴として保存できるが、最安店検索の対象にはならない。

## フロントエンド確認画面で必要な処理

フロントエンドは、OCR API の仮データをそのまま登録ボタンに渡してはいけない。`POST /receipts/prepare` を挟むことで、日付形式、OCR 専用項目、商品名解決、カテゴリ補完の変換量を DB 側に寄せられる。

確認画面で最低限、次を確認する。

```text
購入日
店舗名
合計金額
商品名
数量
単位
行合計
カテゴリ
在庫対象かどうか
在庫対象の場合の base_quantity / base_unit
```

在庫対象の商品で `base_quantity` または `base_unit` が空なら、登録前にユーザーへ確認する。
