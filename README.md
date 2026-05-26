# Receipt OCR API

レシート画像を受け取り、フロントエンドの確認画面に表示するための OCR 候補データを返す FastAPI アプリケーションです。

返却データは、ユーザー確認前の一時的な候補です。このリポジトリは DB 登録、database API 呼び出し、在庫反映、レシピ提案、認証、ユーザー管理、画像保存、バックグラウンドジョブを担当しません。

## Scope

この API が担当すること:

- レシート画像の入力検証
- Gemini による画像読み取り
- OpenAI Structured Outputs による厳密な JSON 正規化
- Pydantic による最終レスポンス検証
- フロントエンド確認用の候補データ返却

この API が担当しないこと:

- レシートや明細のデータベース登録
- database API / accounting API の呼び出し
- 在庫テーブルへの反映
- レシピ提案
- ユーザー認証・ユーザー管理
- レシート画像の永続保存

## Processing Flow

```text
Receipt image
  -> image validation
  -> Gemini image reading
  -> OpenAI Structured Outputs normalization
  -> Pydantic validation
  -> frontend confirmation response
```

外部モデル呼び出しは provider に分離されています。

```text
Route
  -> ReceiptOcrService
      -> GeminiProvider
      -> OpenAIStructuredProvider
      -> Pydantic validation
```

## Requirements

- Python 3.12+
- uv

## Setup

```bash
uv sync
```

## Run

API キーなしでアプリケーションを起動できます。

```bash
uv run uvicorn app.main:app --reload
```

既定のローカル URL:

```text
http://127.0.0.1:8000
```

FastAPI の自動ドキュメント:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`
- `http://127.0.0.1:8000/openapi.json`

## Configuration

設定は OS 環境変数から `pydantic-settings` で読み込みます。このプロジェクトは `.env` ファイルを使いません。

アプリケーションの起動に `OPENAI_API_KEY` と `GEMINI_API_KEY` は不要です。実 provider の実行時だけ API キーが必要です。未設定のまま実 provider が呼ばれた場合、公開 API レスポンスでは不足しているキー名や値を出さず、`provider_not_configured` を返します。

| Name | Startup required | Live provider required | Default | Description |
|---|---:|---:|---|---|
| `GEMINI_API_KEY` | no | yes | none | Gemini API key |
| `GEMINI_MODEL` | no | no | `gemini-2.5-flash` | Gemini model |
| `OPENAI_API_KEY` | no | yes | none | OpenAI API key |
| `OPENAI_MODEL` | no | no | `gpt-5.4-mini` | OpenAI model |
| `MAX_IMAGE_BYTES` | no | no | `10485760` | Maximum image upload size |
| `ALLOWED_IMAGE_MIME_TYPES` | no | no | `image/jpeg,image/png,image/webp` | Allowed upload MIME types. Comma-separated string is accepted |
| `APP_ENV` | no | no | `local` | Application environment label |
| `LOG_LEVEL` | no | no | `INFO` | Log level label |

秘密情報の扱い:

- 実 API キーを README、テスト、ログ、コミット対象ファイルに書かない
- 環境変数の中身を出力しない
- Codex に実 API キーを渡さない
- Codex に実 Gemini / OpenAI API 呼び出しを実行させない

## API

このアプリケーションが定義している API は次の 2 つです。

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | ヘルスチェック |
| `POST` | `/ocr/receipts/extract` | レシート画像 1 枚から OCR 候補データを抽出 |

### GET /health

ヘルスチェックです。provider や API キーの状態は確認しません。

Request:

```bash
curl http://127.0.0.1:8000/health
```

Response `200`:

```json
{
  "status": "ok"
}
```

Response fields:

| Field | Type | Description |
|---|---|---|
| `status` | string | 常に `ok` |

### POST /ocr/receipts/extract

レシート画像 1 枚から、フロントエンド確認用の候補データを抽出します。

この endpoint は `multipart/form-data` を受け付けます。成功時のレスポンスは確定データではなく、必ず `status = "needs_confirmation"` の候補データです。

Request:

```bash
curl -X POST "http://127.0.0.1:8000/ocr/receipts/extract" \
  -F "file=@sample_receipt.jpg;type=image/jpeg"
```

Request fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| `file` | file | yes | レシート画像 |

Accepted image MIME types:

- `image/jpeg`
- `image/png`
- `image/webp`

Maximum file size is controlled by `MAX_IMAGE_BYTES`. The default is `10485760` bytes.

Response `200` example:

```json
{
  "status": "needs_confirmation",
  "store_name": "Sample Store",
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
      "warnings": [],
      "ocr_metadata": {
        "field_confidence": {
          "raw_name": 0.95,
          "normalized_name": 0.88,
          "category_name": 0.7,
          "purchased_quantity": 0.9,
          "purchased_unit": 0.9,
          "base_quantity": 0.8,
          "base_unit": 0.8,
          "unit_price": 0.92,
          "line_total": 0.92,
          "is_inventory_target": 0.75
        },
        "auto_register_candidate": false,
        "needs_review_reasons": []
      }
    }
  ],
  "warnings": [
    "合計金額と明細合計が一致しない可能性があります"
  ]
}
```

Top-level response fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| `status` | string | yes | 成功時は常に `needs_confirmation` |
| `store_name` | string or null | yes | レシート上の店舗名候補。読めない場合は `null` |
| `purchased_at` | string or null | yes | 購入日候補。値がある場合は `YYYY-MM-DD` |
| `total_amount` | integer or null | yes | 最終支払金額候補。値がある場合は `0` 以上 |
| `items` | array | yes | 明細候補の配列 |
| `warnings` | array of string | yes | レシート全体に対する非致命的な警告 |

Item fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| `raw_name` | string or null | yes | レシート上の商品名候補。過度に正規化しない値 |
| `normalized_name` | string or null | yes | OCR が推定した商品名候補。DB の `products.name` と一致する保証はない |
| `category_name` | string or null | yes | 会計カテゴリ名候補。カテゴリ ID は返さない |
| `purchased_quantity` | number or null | yes | レシート上の購入単位の数量。値がある場合は `0` より大きい |
| `purchased_unit` | string or null | yes | レシート上の購入単位 |
| `base_quantity` | number or null | yes | アプリ内部基準単位への換算数量。値がある場合は `0` より大きい |
| `base_unit` | string or null | yes | アプリ内部基準単位 |
| `unit_price` | integer or null | yes | 単価候補。値がある場合は `0` 以上 |
| `line_total` | integer or null | yes | 明細行金額候補。値がある場合は `0` 以上 |
| `is_inventory_target` | boolean or null | yes | 在庫反映対象にするかどうかの候補 |
| `confidence` | number or null | yes | 明細全体の信頼度候補。値がある場合は `0.0` から `1.0` |
| `warnings` | array of string | yes | 明細行ごとの非致命的な警告 |
| `ocr_metadata` | object | yes | OCR 後処理用のメタデータ |

`ocr_metadata` fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| `field_confidence` | object | yes | 明細フィールドごとの信頼度候補 |
| `auto_register_candidate` | boolean or null | yes | 自動登録候補として扱えるかどうかの候補。最終判断ではない |
| `needs_review_reasons` | array of string | yes | 自動登録や確定前に確認が必要な理由 |

`field_confidence` fields:

| Field | Type |
|---|---|
| `raw_name` | number or null |
| `normalized_name` | number or null |
| `category_name` | number or null |
| `purchased_quantity` | number or null |
| `purchased_unit` | number or null |
| `base_quantity` | number or null |
| `base_unit` | number or null |
| `unit_price` | number or null |
| `line_total` | number or null |
| `is_inventory_target` | number or null |

All `field_confidence` values must be `0.0` to `1.0` when present.

Validation rules:

- Unknown values should be returned as `null`, not guessed values
- Unknown object keys are rejected
- `purchased_at` must be `YYYY-MM-DD` when present
- `total_amount`, `unit_price`, and `line_total` must be `0` or greater when present
- `purchased_quantity` and `base_quantity` must be greater than `0` when present
- `confidence` and field-level confidence values must be between `0.0` and `1.0` when present

Important API behavior:

- This API does not register data in a database
- This API does not call the database API or accounting API
- This API does not return `product_id`, `category_id`, `receipt_id`, or `receipt_item_id`
- `normalized_name` is only an OCR-estimated product-name candidate
- Final ID resolution, correction, and database registration belong outside this service
- Total amount and item sum mismatch does not fail the request; the service adds one warning when it can detect the mismatch

## Error Responses

Route-specific errors use this response shape:

```json
{
  "detail": {
    "code": "unsupported_image_type",
    "message": "Unsupported image type."
  }
}
```

`POST /ocr/receipts/extract` errors:

| Status | Code | Message | When |
|---:|---|---|---|
| 400 | `unsupported_image_type` | `Unsupported image type.` | `file` MIME type is not allowed |
| 400 | `empty_file` | `File is empty.` | Uploaded file has zero bytes |
| 413 | `image_too_large` | `Uploaded image is too large.` | Uploaded file exceeds `MAX_IMAGE_BYTES` |
| 422 | `structured_output_invalid` | `Structured OCR output is invalid.` | Final structured data failed Pydantic validation |
| 502 | `provider_not_configured` | `OCR provider is not configured.` | A real provider path was called without required configuration |
| 502 | `gemini_provider_failed` | `Gemini provider failed.` | Gemini extraction failed |
| 502 | `openai_provider_failed` | `OpenAI provider failed.` | OpenAI normalization failed |
| 502 | `ocr_provider_failed` | `OCR provider failed.` | Generic provider failure |
| 500 | `internal_server_error` | `Internal server error.` | Unexpected server error |

FastAPI request validation errors, such as a missing `file` field, may use FastAPI's standard validation response.

Public error responses must not expose API keys, environment variable values, uploaded image bytes, provider raw responses, or stack traces.

## Frontend Usage

ブラウザから送信する場合は `FormData` に `file` を入れて送ります。

```ts
const formData = new FormData();
formData.append("file", file);

const response = await fetch("http://127.0.0.1:8000/ocr/receipts/extract", {
  method: "POST",
  body: formData,
});

const result = await response.json();
```

フロントエンドは OCR レスポンスを確定データとして扱わず、ユーザーが確認・修正できる画面に表示してください。

確認画面で扱う主な項目:

- 店舗名
- 購入日
- 合計金額
- 明細行
- トップレベルの警告
- 明細行ごとの警告
- OCR metadata の信頼度と確認理由

DB 登録前にフロントエンドまたは database API 側で確認すべき項目:

- `purchased_at`
- `total_amount`
- item `raw_name`
- item `line_total`
- item `is_inventory_target`

在庫対象品では、次の項目も確認対象です。

- item `normalized_name`
- item `purchased_quantity`
- item `purchased_unit`
- item `base_quantity`
- item `base_unit`

現在のアプリケーションコードには CORS 設定がありません。別オリジンのフロントエンドから直接呼び出す場合は、バックエンドに CORS 設定を追加するか、フロントエンド開発サーバーでプロキシしてください。

## Human-Only Live Verification

Live provider verification is optional and must be performed by a human developer only. Pass API keys through OS environment variables for the current command or current shell only. Do not store keys in project files.

Example:

```bash
OPENAI_API_KEY="<set-by-human>" \
GEMINI_API_KEY="<set-by-human>" \
uv run uvicorn app.main:app --reload
```

Then, from another terminal:

```bash
curl -X POST "http://127.0.0.1:8000/ocr/receipts/extract" \
  -F "file=@sample_receipt.jpg;type=image/jpeg"
```

Do not ask Codex to run this live verification.

## Test

```bash
uv run python -m compileall app
uv run pytest
```

Tests must not require real API keys or real provider calls.

## Project Layout

```text
app/
  config.py
  main.py
  providers/
  routes/
  schemas/
  services/
  utils/
docs/
tests/
```

Key documents:

- `docs/OCR_PROJECT_SPEC.md`
- `docs/API_SPEC.md`
- `docs/STRUCTURED_OUTPUT_SCHEMA.md`
- `docs/PROVIDER_DESIGN.md`
- `docs/ERROR_HANDLING.md`
- `docs/TESTING_STRATEGY.md`
- `docs/FRONTEND_HANDOFF_SPEC.md`
