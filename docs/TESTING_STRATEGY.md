# Testing Strategy

## 目的

このドキュメントは、OCR API のテスト方針を定義する。

外部 API を実際に呼ばず、安定して実行できるテストを作る。

## 基本方針

- pytest を使う。
- FastAPI の TestClient または httpx AsyncClient を使う。
- Gemini provider と OpenAI provider はモックする。
- テストで実際の Gemini API / OpenAI API を呼ばない。
- テスト用画像は小さなダミー画像を使う。
- API キーがなくてもテストが通るようにする。

## テスト対象

```txt
GET /health
POST /ocr/receipts/extract
image validation
Pydantic schema validation
ReceiptOcrService
error handling
```

## 必須テスト

### 1. health check

`GET /health` が `200` を返す。

期待レスポンス例:

```json
{
  "status": "ok",
  "service": "receipt-ocr-api"
}
```

### 2. 正常な画像アップロード

正常な画像をアップロードしたとき、`status = needs_confirmation` を返す。

外部 provider はモックする。

確認項目:

- HTTP status が `200`
- `status` が `needs_confirmation`
- `items` が配列
- `warnings` が配列

### 3. 不正 MIME type

`text/plain` などをアップロードすると `400` を返す。

期待:

```json
{
  "error": {
    "code": "invalid_image_type"
  }
}
```

### 4. サイズ超過

`MAX_IMAGE_BYTES` を超えるファイルで `413` を返す。

### 5. Gemini provider 失敗

Gemini provider が例外を投げる場合、API は `502` を返す。

期待 code:

```txt
gemini_provider_failed
```

### 6. OpenAI provider 失敗

OpenAI provider が例外を投げる場合、API は `502` を返す。

期待 code:

```txt
openai_provider_failed
```

### 7. Structured Outputs 検証失敗

OpenAI provider が Pydantic に合わない dict を返した場合、`422` または `502` を返す。

このプロジェクトでは `422` を推奨する。

期待 code:

```txt
structured_validation_failed
```

### 8. null を含むレスポンス

次のような `null` を含むデータでも Pydantic 検証が通ることを確認する。

```json
{
  "status": "needs_confirmation",
  "store_name": null,
  "purchased_at": null,
  "total_amount": null,
  "items": [],
  "warnings": []
}
```

### 9. 合計金額不一致

`total_amount` と `items.line_total` の合計が一致しない場合、エラーではなく `warnings` を返す。

### 10. base_quantity 不明

単位変換が不明な商品について、`base_quantity = null` と `base_unit = null` を許容する。

## テスト用 provider

テストでは、次のような fake provider を使う。

```python
class FakeGeminiProvider:
    async def extract_receipt_text(self, *, image_bytes: bytes, mime_type: str):
        return GeminiExtractionResult(
            text="店舗名: サンプルスーパー\n合計: 636円\nタマゴM 10コ 238円"
        )

class FakeOpenAIStructuredProvider:
    async def structure_receipt(self, *, gemini_text: str):
        return {
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
                    "is_inventory_target": True,
                    "confidence": 0.86,
                    "warnings": [],
                }
            ],
            "warnings": [],
        }
```

## ダミー画像生成

テスト用には、Pillow が使えるなら小さな画像を生成する。

```python
from io import BytesIO
from PIL import Image

def make_test_png() -> bytes:
    image = Image.new("RGB", (10, 10), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
```

Pillow を依存に入れない方針なら、最小の PNG bytes を fixture として持つ。

## 実行コマンド

```bash
uv run python -m compileall app
uv run pytest
```

## CI で必要なこと

CI では外部 API キーなしでテストが通るようにする。

そのため、settings 読み込み時に `GEMINI_API_KEY` や `OPENAI_API_KEY` が必須で落ちないようにするか、テスト時は dummy 値を設定する。

## テストで避けること

- 実際のレシート画像を使う
- 外部 API に接続する
- API キーを必要とする
- 実行順序に依存する
- ローカル環境の `.env` に依存する
- 外部 API の応答文言に依存する
