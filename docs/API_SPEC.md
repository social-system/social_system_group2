# API Specification

## 基本方針

この API は、レシート OCR の仮データを返すための API である。

DB 登録は行わない。返却するデータは、フロントエンドでユーザーが確認・修正するための候補データである。

## Base URL

ローカル開発時の例:

```txt
http://localhost:8000
```

## エンドポイント一覧

```txt
GET  /health
POST /ocr/receipts/extract
```

## GET /health

### 目的

アプリケーションが起動しているか確認する。

### 外部 API 接続

この API では Gemini や OpenAI には接続しない。

### レスポンス

```json
{
  "status": "ok",
  "service": "receipt-ocr-api"
}
```

### ステータスコード

```txt
200 OK
```

## POST /ocr/receipts/extract

### 目的

レシート画像を受け取り、フロントエンド確認用の仮レシートデータを返す。

### Request

`multipart/form-data` で画像ファイルを送信する。

| field | type | required | description |
|---|---|---:|---|
| file | file | yes | レシート画像 |

### 対応 MIME type

```txt
image/jpeg
image/png
image/webp
```

### サイズ制限

環境変数 `MAX_IMAGE_BYTES` で指定する。

初期値は 10MB を想定する。

```env
MAX_IMAGE_BYTES=10485760
```

### curl 例

```bash
curl -X POST "http://localhost:8000/ocr/receipts/extract" \
  -F "file=@./samples/receipt.jpg"
```

### 正常レスポンス

```json
{
  "status": "needs_confirmation",
  "store_name": "サンプルスーパー",
  "purchased_at": "2026-05-12",
  "total_amount": 1280,
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
    }
  ],
  "warnings": []
}
```

## レスポンスフィールド

### Receipt

| field | type | required | nullable | description |
|---|---|---:|---:|---|
| status | string | yes | no | 常に `needs_confirmation` |
| store_name | string | yes | yes | 店舗名 |
| purchased_at | string | yes | yes | 購入日。`YYYY-MM-DD` |
| total_amount | integer | yes | yes | レシートの最終支払額 |
| items | array | yes | no | 明細候補 |
| warnings | array[string] | yes | no | レシート全体の警告 |

### Item

| field | type | required | nullable | description |
|---|---|---:|---:|---|
| raw_name | string | yes | yes | レシート上の商品名に近い文字列 |
| normalized_name | string | yes | yes | 正規化された商品名候補 |
| category_name | string | yes | yes | 家計簿カテゴリ名候補 |
| purchased_quantity | number | yes | yes | 購入時数量 |
| purchased_unit | string | yes | yes | 購入時単位 |
| base_quantity | number | yes | yes | 基準単位に変換した数量候補 |
| base_unit | string | yes | yes | 基準単位 |
| unit_price | integer | yes | yes | 単価 |
| line_total | integer | yes | yes | 明細金額 |
| is_inventory_target | boolean | yes | yes | 在庫対象候補 |
| confidence | number | yes | yes | 読み取り信頼度。0以上1以下 |
| warnings | array[string] | yes | no | 明細ごとの警告 |

## status

現時点では、正常レスポンスの `status` は常に次とする。

```txt
needs_confirmation
```

将来、OCR結果の品質に応じて `failed` や `partial` を増やす可能性はあるが、MVPでは増やさない。

## エラーレスポンス

エラー時は、次の形式を基本とする。

```json
{
  "error": {
    "code": "invalid_image_type",
    "message": "Unsupported image MIME type.",
    "details": null
  }
}
```

### エラー形式

| field | type | description |
|---|---|---|
| error.code | string | アプリ内で安定して扱うエラーコード |
| error.message | string | 利用者向けの短い説明 |
| error.details | object/null | 必要な補足。秘密情報は含めない |

## ステータスコード

| status | case |
|---:|---|
| 200 | OCR成功。ユーザー確認用データを返す |
| 400 | MIME type が不正 |
| 413 | ファイルサイズ超過 |
| 422 | 画像として読み取れない、または構造検証に失敗 |
| 502 | Gemini または OpenAI の外部 API 失敗 |
| 500 | 想定外の内部エラー |

## 注意点

合計金額と明細合計が一致しない場合は、原則として `200` を返す。

その場合は、次のように `warnings` に入れる。

```json
{
  "warnings": [
    "明細合計とレシート合計が一致していません。割引・税・読み取り漏れを確認してください。"
  ]
}
```

## DB 連携しない理由

OCR は不確実な処理である。OCR 結果をそのまま DB に登録すると、家計簿、在庫、レシピ提案のすべてに誤データが広がる。

そのため、この API は DB 登録をせず、フロントエンドの確認画面に仮データを返すだけにする。
