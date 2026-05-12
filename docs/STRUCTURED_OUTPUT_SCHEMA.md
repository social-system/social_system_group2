# Structured Output Schema Specification

## 目的

このドキュメントは、OpenAI Structured Outputs で返すレシート OCR 結果の JSON Schema を定義する。

Gemini の出力は信頼しない。OpenAI Structured Outputs で、フロントエンドが扱いやすい JSON に厳密化する。

## 基本ルール

Structured Outputs のスキーマは次の方針で作る。

- `strict: true` を使う。
- すべての object に `additionalProperties: false` を指定する。
- すべてのフィールドを `required` にする。
- 任意項目は `null` を許可する。
- 不明な値を推測で埋めない。
- スキーマ外のキーを返さない。

## 返却形式

```json
{
  "status": "needs_confirmation",
  "store_name": "サンプルスーパー",
  "purchased_at": "2026-05-12",
  "total_amount": 1280,
  "items": [],
  "warnings": []
}
```

## JSON Schema

実装では、次の schema を基準にする。

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "status",
    "store_name",
    "purchased_at",
    "total_amount",
    "items",
    "warnings"
  ],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["needs_confirmation"]
    },
    "store_name": {
      "type": ["string", "null"]
    },
    "purchased_at": {
      "type": ["string", "null"],
      "description": "YYYY-MM-DD format. Use null if unreadable."
    },
    "total_amount": {
      "type": ["integer", "null"],
      "minimum": 0
    },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "raw_name",
          "normalized_name",
          "category_name",
          "purchased_quantity",
          "purchased_unit",
          "base_quantity",
          "base_unit",
          "unit_price",
          "line_total",
          "is_inventory_target",
          "confidence",
          "warnings"
        ],
        "properties": {
          "raw_name": {
            "type": ["string", "null"]
          },
          "normalized_name": {
            "type": ["string", "null"]
          },
          "category_name": {
            "type": ["string", "null"]
          },
          "purchased_quantity": {
            "type": ["number", "null"],
            "exclusiveMinimum": 0
          },
          "purchased_unit": {
            "type": ["string", "null"]
          },
          "base_quantity": {
            "type": ["number", "null"],
            "exclusiveMinimum": 0
          },
          "base_unit": {
            "type": ["string", "null"]
          },
          "unit_price": {
            "type": ["integer", "null"],
            "minimum": 0
          },
          "line_total": {
            "type": ["integer", "null"],
            "minimum": 0
          },
          "is_inventory_target": {
            "type": ["boolean", "null"]
          },
          "confidence": {
            "type": ["number", "null"],
            "minimum": 0,
            "maximum": 1
          },
          "warnings": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        }
      }
    },
    "warnings": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

## Pydantic モデル方針

Structured Outputs の schema と Pydantic model は一致させる。

実装例の方向性:

```python
from pydantic import BaseModel, Field, field_validator

class OcrReceiptItem(BaseModel):
    raw_name: str | None
    normalized_name: str | None
    category_name: str | None
    purchased_quantity: float | None
    purchased_unit: str | None
    base_quantity: float | None
    base_unit: str | None
    unit_price: int | None
    line_total: int | None
    is_inventory_target: bool | None
    confidence: float | None
    warnings: list[str] = Field(default_factory=list)

class OcrReceiptResponse(BaseModel):
    status: str
    store_name: str | None
    purchased_at: str | None
    total_amount: int | None
    items: list[OcrReceiptItem]
    warnings: list[str] = Field(default_factory=list)
```

実装時は、`status` を `Literal["needs_confirmation"]` にすることが望ましい。

## 日付検証

`purchased_at` は `YYYY-MM-DD` のみ許可する。

読めない場合は `null`。

次のような曖昧な値は、無理に変換しない。

```txt
5/12
R6.5.12
12-05-26
```

ただし、Gemini または OpenAI が画像文脈から明確に判断できる場合は `YYYY-MM-DD` に変換してよい。

判断できない場合は `null` にし、`warnings` に入れる。

## 金額検証

金額は 0 以上の整数とする。

対象:

- `total_amount`
- `unit_price`
- `line_total`

負の値は原則として受け付けない。

割引行を明細として扱うかは MVP では固定しない。割引が読み取れた場合、`warnings` に「割引行があります」と入れる。

## 数量検証

数量は `null` または 0 より大きい数値とする。

対象:

- `purchased_quantity`
- `base_quantity`

数量が 0 の場合は不自然なので、`null` にするか、警告対象にする。

## confidence

`confidence` は 0 以上 1 以下の数値、または `null` とする。

これはモデルが出した候補値であり、厳密な確率ではない。

フロントエンドでは、低い場合にユーザーへ確認を促す用途で使う。

## warnings

警告はエラーではない。

例:

```json
{
  "warnings": [
    "購入日が読み取れませんでした",
    "明細合計と合計金額が一致しません",
    "単位変換が不明な商品があります"
  ]
}
```

各 item にも `warnings` を持たせる。

例:

```json
{
  "raw_name": "ジャガイモ 1袋",
  "base_quantity": null,
  "base_unit": null,
  "warnings": [
    "1袋を基準単位へ変換できませんでした"
  ]
}
```

## Structured Outputs に渡すプロンプト方針

OpenAI に渡す入力には、Gemini の出力を含める。

プロンプトでは次を明示する。

- これはレシート OCR の構造化処理である
- 不明な値は `null` にする
- 推測で埋めない
- 日本のレシートを想定する
- 金額は円の整数にする
- 日付は `YYYY-MM-DD` にする
- DB 登録用ではなくフロント確認用である
- スキーマ外のキーを出さない
- 合計不一致は `warnings` に入れる

## 正常例

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
    },
    {
      "raw_name": "センザイ",
      "normalized_name": "洗剤",
      "category_name": "日用品",
      "purchased_quantity": 1,
      "purchased_unit": "個",
      "base_quantity": 1,
      "base_unit": "個",
      "unit_price": 398,
      "line_total": 398,
      "is_inventory_target": false,
      "confidence": 0.8,
      "warnings": []
    }
  ],
  "warnings": []
}
```

## 不明値を含む例

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
    "購入日が読み取れませんでした"
  ]
}
```
