# OCR_DB_INTERFACE.md

## 目的

OCR API と DB API の境界を明確にする。

OCR API は仮データを返し、DB API はユーザー確認済みデータだけを保存する。

## 基本フロー

```text
レシート画像
  -> OCR API
  -> OCR 仮データ
  -> フロントエンド確認画面
  -> ユーザー修正
  -> DB API POST /receipts
  -> 確定データ保存
```

## OCR API が返す仮データ

OCR API は、不明な値を `null` として返してよい。

例:

```json
{
  "status": "needs_confirmation",
  "purchased_at": 20260512,
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

DB API に送る時点では、在庫対象データに必要な項目を埋める。

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

## フロントエンド確認画面で必要な処理

フロントエンドは、OCR API の仮データをそのまま登録ボタンに渡してはいけない。

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
