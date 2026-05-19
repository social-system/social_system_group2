# Receipt OCR API

レシート画像を受け取り、フロントエンド確認用の OCR 候補データを返す FastAPI アプリケーションです。

この API が返すデータは、ユーザー確認前の一時的な候補です。このリポジトリは DB 登録、database API 呼び出し、在庫反映、レシピ提案、認証、ユーザー管理、画像保存、バックグラウンドジョブを担当しません。

## Responsibilities

処理の流れは次の通りです。

```text
Receipt image
  -> image validation
  -> Gemini image reading
  -> OpenAI Structured Outputs normalization
  -> Pydantic validation
  -> frontend confirmation response
```

責務の境界は以下です。

| Layer | Responsibility |
|---|---|
| OCR API | レシート画像を読み、候補データを返す |
| Frontend | 候補データを表示し、ユーザーに確認・修正させる |
| Database API | 確定済みのレシートと明細を保存する |
| Inventory API | 確定済みの在庫対象品を在庫へ反映する |
| Recipe API | 確定済み在庫データからレシピを提案する |

## Requirements

- Python 3.12+
- uv

## Setup

```bash
uv sync
```

## Configuration

設定は OS 環境変数から `pydantic-settings` で読み込みます。`.env` 系ファイルは使いません。API キーなどの秘密情報をプロジェクトファイルに保存しないでください。

アプリは `OPENAI_API_KEY` と `GEMINI_API_KEY` が未設定でも起動できます。実 provider の実行時だけ API キーが必要です。未設定のまま実 provider が呼ばれた場合は、公開レスポンスではどのキーが不足しているかを出さず、`provider_not_configured` を返します。

| Name | Required for startup | Required for live provider call | Default |
|---|---:|---:|---|
| `GEMINI_API_KEY` | no | yes | none |
| `GEMINI_MODEL` | no | no | `gemini-2.5-flash` |
| `OPENAI_API_KEY` | no | yes | none |
| `OPENAI_MODEL` | no | no | `gpt-5.4-mini` |
| `MAX_IMAGE_BYTES` | no | no | `10485760` |
| `ALLOWED_IMAGE_MIME_TYPES` | no | no | `image/jpeg,image/png,image/webp` |

秘密情報の扱い:

- 実 API キーを README、テスト、ログ、コミット対象ファイルに書かない
- `.env`、`.env.local`、`.env.*` を作らない
- 環境変数の中身を出力しない
- Codex に実 API キーを渡さない
- Codex に実 Gemini / OpenAI API 呼び出しを実行させない

## Run

API キーなしで起動できます。

```bash
uv run uvicorn app.main:app --reload
```

実 provider を使って動作確認する場合は、API キーを OS 環境変数として現在のコマンドだけに渡して起動します。実 API キーは README、`.env`、ログ、コミット対象ファイルに保存しないでください。

```bash
OPENAI_API_KEY="<set-by-human>" \
GEMINI_API_KEY="<set-by-human>" \
uv run uvicorn app.main:app --reload
```

モデルを明示する場合も同じコマンド内で指定できます。

```bash
OPENAI_API_KEY="<set-by-human>" \
GEMINI_API_KEY="<set-by-human>" \
OPENAI_MODEL="gpt-5.4-mini" \
GEMINI_MODEL="gemini-2.5-flash" \
uv run uvicorn app.main:app --reload
```

起動後の既定 URL:

```text
http://127.0.0.1:8000
```

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

Allowed MIME types:

- `image/jpeg`
- `image/png`
- `image/webp`

Successful response example:

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

成功時の `status` は常に `needs_confirmation` です。読み取れない値は推測せず `null` にします。合計金額と明細合計の不一致など、致命的でない不確実性はエラーではなく `warnings` に入ります。

`product_id` や `category_id` は返しません。この API は database master data を所有しないため、確定登録や ID への変換は別サービスの責務です。

## Response Shape

Top-level fields:

| Field | Type |
|---|---|
| `status` | `needs_confirmation` |
| `store_name` | `string \| null` |
| `purchased_at` | `YYYY-MM-DD string \| null` |
| `total_amount` | `integer \| null` |
| `items` | `array` |
| `warnings` | `array<string>` |

Item fields:

| Field | Type |
|---|---|
| `raw_name` | `string \| null` |
| `normalized_name` | `string \| null` |
| `category_name` | `string \| null` |
| `purchased_quantity` | `number \| null` |
| `purchased_unit` | `string \| null` |
| `base_quantity` | `number \| null` |
| `base_unit` | `string \| null` |
| `unit_price` | `integer \| null` |
| `line_total` | `integer \| null` |
| `is_inventory_target` | `boolean \| null` |
| `confidence` | `number \| null` |
| `warnings` | `array<string>` |

Validation rules include:

- `purchased_at` must be `YYYY-MM-DD` when present
- amounts must be `0` or greater when present
- quantities must be greater than `0` when present
- `confidence` must be between `0.0` and `1.0` when present
- unknown object keys are rejected

## Error Responses

Route-specific errors use a stable shape.

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
| 422 | `structured_output_invalid` | Final structured data failed validation |
| 502 | `provider_not_configured` | Live provider was called without required configuration |
| 502 | `ocr_provider_failed` | Gemini or OpenAI provider failed |
| 500 | `internal_server_error` | Unexpected server error |

Public error responses must not expose API keys, environment variable values, uploaded image bytes, provider raw responses, or stack traces.

## Test

```bash
uv run python -m compileall app
uv run pytest
```

Unit tests use fake or mocked providers. They do not call real Gemini or OpenAI APIs and do not require real API keys.

## Human-Only Live Verification

Live provider verification is optional and must be performed by a human developer only. Pass API keys through OS environment variables for the current command or current shell only. Do not store keys in project files.

Example:

```bash
OPENAI_API_KEY="<set-by-human>" \
GEMINI_API_KEY="<set-by-human>" \
uv run uvicorn app.main:app --reload
```

Then, from another terminal, send a receipt image:

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
