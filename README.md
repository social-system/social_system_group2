# Receipt OCR API

レシート画像を受け取り、フロントエンドの確認画面に表示するための OCR 候補データを返す FastAPI アプリケーションです。

返却データはユーザー確認前の一時的な候補です。このリポジトリは DB 登録、database API 呼び出し、在庫反映、レシピ提案、認証、ユーザー管理、画像保存、バックグラウンドジョブを担当しません。

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

責務の境界:

| Layer | Responsibility |
|---|---|
| OCR API | レシート画像を読み、候補データを返す |
| Frontend | 候補データを表示し、ユーザーに確認・修正させる |
| Database API | 確定済みレシートと明細を保存する |
| Inventory API | 確定済みの在庫対象品を在庫へ反映する |
| Recipe API | 確定済み在庫データからレシピを提案する |

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

## Configuration

設定は OS 環境変数から `pydantic-settings` で読み込みます。プロジェクトファイルに実 API キーなどの秘密情報を保存しないでください。

アプリケーションの起動に `OPENAI_API_KEY` と `GEMINI_API_KEY` は不要です。実 provider の実行時だけ API キーが必要です。未設定のまま実 provider が呼ばれた場合、公開 API レスポンスでは不足しているキー名や値を出さず、`provider_not_configured` を返します。

| Name | Startup required | Live provider required | Default |
|---|---:|---:|---|
| `GEMINI_API_KEY` | no | yes | none |
| `GEMINI_MODEL` | no | no | `gemini-2.5-flash` |
| `OPENAI_API_KEY` | no | yes | none |
| `OPENAI_MODEL` | no | no | `gpt-5.4-mini` |
| `MAX_IMAGE_BYTES` | no | no | `10485760` |
| `ALLOWED_IMAGE_MIME_TYPES` | no | no | `image/jpeg,image/png,image/webp` |
| `APP_ENV` | no | no | `local` |
| `LOG_LEVEL` | no | no | `INFO` |

秘密情報の扱い:

- 実 API キーを README、テスト、ログ、コミット対象ファイルに書かない
- 環境変数の中身を出力しない
- Codex に実 API キーを渡さない
- Codex に実 Gemini / OpenAI API 呼び出しを実行させない

## API

### GET /health

ヘルスチェックです。

```bash
curl http://127.0.0.1:8000/health
```

Response:

```json
{
  "status": "ok"
}
```

### POST /ocr/receipts/extract

レシート画像 1 枚から候補データを抽出します。リクエストは `multipart/form-data` です。

```bash
curl -X POST "http://127.0.0.1:8000/ocr/receipts/extract" \
  -F "file=@sample_receipt.jpg;type=image/jpeg"
```

Request field:

| Field | Type | Required | Description |
|---|---|---:|---|
| `file` | file | yes | レシート画像 |

Allowed MIME types:

- `image/jpeg`
- `image/png`
- `image/webp`

Maximum file size is controlled by `MAX_IMAGE_BYTES`. The default is `10485760` bytes.

Successful response:

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
      "warnings": []
    }
  ],
  "warnings": [
    "合計金額と明細合計が一致しない可能性があります"
  ]
}
```

成功時の `status` は常に `needs_confirmation` です。読み取れない値は推測せず `null` にします。合計金額と明細合計の不一致など、致命的でない不確実性はエラーではなく `warnings` に入ります。合計不一致の決定的な判定はサービス層で一度だけ行い、AI 側には積極的に同じ警告を出させません。

この API は `product_id`、`category_id`、`receipt_id`、`receipt_item_id` を返しません。ID 解決と確定登録は database API 側の責務です。
`normalized_name` は OCR が推定した商品名候補であり、database API の `products.name` と一致する保証はありません。

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

DB 登録前にフロントエンドまたは database API 側で確認すべき項目:

- `purchased_at`
- `total_amount`
- item `raw_name`
- item `line_total`
- item `is_inventory_target`

在庫対象品では、次の項目も確認対象です。

- `normalized_name`
- `purchased_quantity`
- `purchased_unit`
- `base_quantity`
- `base_unit`

現在のアプリケーションコードには CORS 設定がありません。別オリジンのフロントエンドから直接呼び出す場合は、バックエンドに CORS 設定を追加するか、フロントエンド開発サーバーでプロキシしてください。

## Response Shape

Top-level fields:

| Field | Type | Notes |
|---|---|---|
| `status` | `needs_confirmation` | 成功時は固定 |
| `store_name` | `string \| null` | 店舗名候補 |
| `purchased_at` | `YYYY-MM-DD string \| null` | 購入日候補 |
| `total_amount` | `integer \| null` | 最終支払金額候補 |
| `items` | `array` | 明細候補 |
| `warnings` | `array<string>` | 非致命的な警告 |

Item fields:

| Field | Type | Notes |
|---|---|---|
| `raw_name` | `string \| null` | レシート上の商品名 |
| `normalized_name` | `string \| null` | OCR が推定した商品名候補。DB 正式商品名とは限らない |
| `category_name` | `string \| null` | 会計カテゴリ名候補 |
| `purchased_quantity` | `number \| null` | レシート上の購入単位の数量 |
| `purchased_unit` | `string \| null` | レシート上の購入単位 |
| `base_quantity` | `number \| null` | アプリ内部基準単位への換算数量 |
| `base_unit` | `string \| null` | アプリ内部基準単位 |
| `unit_price` | `integer \| null` | 単価候補 |
| `line_total` | `integer \| null` | 明細行金額候補 |
| `is_inventory_target` | `boolean \| null` | 在庫対象候補 |
| `confidence` | `number \| null` | `0.0` から `1.0` |
| `warnings` | `array<string>` | 明細行ごとの警告 |

Validation rules:

- `purchased_at` must be `YYYY-MM-DD` when present
- amounts must be `0` or greater when present
- quantities must be greater than `0` when present
- `confidence` must be between `0.0` and `1.0` when present
- unknown object keys are rejected

## Error Responses

Route-specific errors use a stable response shape.

```json
{
  "detail": {
    "code": "unsupported_image_type",
    "message": "Unsupported image type."
  }
}
```

Common status mapping:

| Status | Code | Meaning |
|---:|---|---|
| 400 | `unsupported_image_type` | MIME type is not allowed |
| 400 | `empty_file` | File is empty |
| 413 | `image_too_large` | Uploaded image exceeds `MAX_IMAGE_BYTES` |
| 422 | `receipt_not_readable` | Image could not be interpreted as a receipt |
| 422 | `structured_output_invalid` | Final structured data failed validation |
| 502 | `provider_not_configured` | Live provider was called without required configuration |
| 502 | `gemini_provider_failed` | Gemini provider failed |
| 502 | `openai_provider_failed` | OpenAI provider failed |
| 502 | `ocr_provider_failed` | OCR provider failed |
| 500 | `internal_server_error` | Unexpected server error |

Public error responses must not expose API keys, environment variable values, uploaded image bytes, provider raw responses, or stack traces.

## Provider Boundary

External model calls are isolated behind provider classes.

```text
Route
  -> ReceiptOcrService
      -> GeminiProvider
      -> OpenAIStructuredProvider
      -> Pydantic validation
```

Routes must not directly call Gemini or OpenAI SDKs. Unit tests use fake or mocked providers and must not call real Gemini or OpenAI APIs.

## Test

```bash
uv run python -m compileall app
uv run pytest
```

Tests must not require real API keys or real provider calls.

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
