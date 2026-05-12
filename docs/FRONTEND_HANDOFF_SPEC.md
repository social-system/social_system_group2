# Frontend Handoff Specification

## 目的

このドキュメントは、OCR API がフロントエンドへ返すデータの考え方を定義する。

OCR API のレスポンスは、DB 登録前の確認画面で使う仮データである。

## フロントエンドでの想定画面

フロントエンドでは、次のような確認画面を想定する。

```txt
レシート画像アップロード
  ↓
OCR API 実行
  ↓
読み取り結果確認画面
  ↓
ユーザーが修正
  ↓
ユーザーが登録ボタンを押す
  ↓
database API へ送信
```

## OCR API の責務

OCR API は、フロントエンドが確認画面を作れるだけの情報を返す。

返すべきもの:

- 店舗名候補
- 購入日候補
- 合計金額候補
- 商品明細候補
- 在庫対象候補
- 基準単位変換候補
- 警告
- 読み取り信頼度候補

返さないもの:

- `product_id`
- `category_id`
- `receipt_id`
- `receipt_item_id`
- DB 登録済みフラグ

## なぜ ID を返さないか

OCR API は DB を見ない設計にするため、`product_id` や `category_id` を確定できない。

OCR 側で返すのは、あくまで次のような名前候補である。

```json
{
  "normalized_name": "卵",
  "category_name": "食費"
}
```

ID への変換は、フロントエンドまたは database API 側で行う。

## フロントエンドで編集可能にする項目

確認画面では、最低限次の項目を編集可能にする。

| field | 編集 | 理由 |
|---|---:|---|
| store_name | yes | 店舗名誤読があるため |
| purchased_at | yes | 日付誤読があるため |
| total_amount | yes | 合計金額誤読があるため |
| raw_name | yes | 商品名誤読があるため |
| normalized_name | yes | 在庫・レシピで使うため |
| category_name | yes | 家計簿集計で使うため |
| purchased_quantity | yes | 数量誤読があるため |
| purchased_unit | yes | 単位誤読があるため |
| base_quantity | yes | 単位変換に確認が必要なため |
| base_unit | yes | 在庫管理の単位に関わるため |
| unit_price | yes | 単価誤読があるため |
| line_total | yes | 明細金額誤読があるため |
| is_inventory_target | yes | 在庫に入れるか確認が必要なため |

## UI で警告すべきケース

OCR API の `warnings` や item の `warnings` に値が入っている場合、フロントエンドはユーザーに確認を促す。

主なケース:

- 購入日が読み取れない
- 合計金額が読み取れない
- 商品名が読み取りにくい
- 明細合計と合計金額が一致しない
- 単位変換ができない
- 在庫対象か判断できない

## confidence の使い方

`confidence` は OCR の読み取り候補の信頼度である。

厳密な確率ではないため、処理の判断に使いすぎない。

フロントエンドでは、次のような表示補助に使う。

```txt
confidence >= 0.8   通常表示
0.5 <= confidence < 0.8   要確認
confidence < 0.5   強く確認
confidence = null  判定不可
```

## base_quantity / base_unit の扱い

在庫管理に使うため、可能なら `base_quantity` と `base_unit` を入れる。

例:

```json
{
  "raw_name": "卵 1パック",
  "purchased_quantity": 1,
  "purchased_unit": "パック",
  "base_quantity": 10,
  "base_unit": "個"
}
```

ただし、推測できない場合は `null` にする。

例:

```json
{
  "raw_name": "玉ねぎ 1袋",
  "purchased_quantity": 1,
  "purchased_unit": "袋",
  "base_quantity": null,
  "base_unit": null,
  "warnings": ["1袋を基準単位へ変換できませんでした"]
}
```

フロントエンドは、この場合ユーザーに数量変換を確認する。

## DB API へ渡す前の変換

OCR API のレスポンスは、そのまま DB API に送らない。

フロントエンドでユーザー確認後、database API の仕様に合わせて変換する。

主な変換:

```txt
category_name       → category_id
normalized_name     → product_id 候補または product 作成候補
status              → DB へは送らない
confidence          → DB へは原則送らない
warnings            → DB へは原則送らない
```

## 確認後 DB 登録用の考え方

フロントエンド確認後は、database API に次のような形で送る想定である。

```json
{
  "purchased_at": "2026-05-12",
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
    }
  ]
}
```

OCR API はこの DB 登録形式を直接返さない。

## フロントエンド向け正常レスポンス例

```json
{
  "status": "needs_confirmation",
  "store_name": "サンプルスーパー",
  "purchased_at": "2026-05-12",
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
      "confidence": 0.86,
      "warnings": []
    }
  ],
  "warnings": []
}
```

## フロントエンド向け警告レスポンス例

```json
{
  "status": "needs_confirmation",
  "store_name": null,
  "purchased_at": null,
  "total_amount": 1200,
  "items": [
    {
      "raw_name": "ジャガイモ 1袋",
      "normalized_name": "じゃがいも",
      "category_name": "食費",
      "purchased_quantity": 1,
      "purchased_unit": "袋",
      "base_quantity": null,
      "base_unit": null,
      "unit_price": null,
      "line_total": 298,
      "is_inventory_target": true,
      "confidence": 0.71,
      "warnings": [
        "1袋を基準単位へ変換できませんでした"
      ]
    }
  ],
  "warnings": [
    "購入日が読み取れませんでした",
    "明細合計と合計金額が一致していません"
  ]
}
```
