# Receipt OCR API

レシート画像からフロントエンド確認用の仮データを作る OCR API です。

この API は DB 登録を行いません。OCR 結果はユーザー確認前の候補データであり、確定保存、database API 呼び出し、在庫反映、レシピ提案、認証、ユーザー管理はこのプロジェクトの責務ではありません。

## Setup

```bash
uv sync
```

## Configuration

このプロジェクトは `.env` 系ファイルを使いません。API キーなどの秘密情報はプロジェクトファイルに保存せず、ライブ provider を人間が手動確認するときだけ OS 環境変数として一時的に渡してください。

Codex に実 API キーを渡さないでください。Codex に実 Gemini / OpenAI API 呼び出しを実行させないでください。

アプリは `OPENAI_API_KEY` と `GEMINI_API_KEY` が未設定でも起動できます。実 provider の実行経路だけが API キーを要求し、未設定の場合は provider 設定エラーになります。

## Run

```bash
uv run uvicorn app.main:app --reload
```

## Health Check

```bash
curl http://127.0.0.1:8000/health
```

Response:

```json
{
  "status": "ok"
}
```

## Extract Receipt

```bash
curl -X POST "http://127.0.0.1:8000/ocr/receipts/extract" \
  -F "file=@sample_receipt.jpg;type=image/jpeg"
```

Successful responses match `ReceiptOcrResponse` and always use:

```json
{
  "status": "needs_confirmation"
}
```

The returned data is provisional and must be reviewed or corrected by the frontend before any final database registration by another service.

## Test

```bash
uv run python -m compileall app
uv run pytest
```

Unit tests use fake or mocked providers. They do not call real Gemini or OpenAI APIs and do not require real API keys.

## Human-Only Live Verification

Live provider verification is optional and must be performed by a human developer only. Pass API keys through OS environment variables for the current shell or current command only. Do not store keys in project files.

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
