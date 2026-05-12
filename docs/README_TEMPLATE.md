# README Template

このファイルは、最終的な `README.md` を作るときのテンプレートである。

Codex は実装時に、リポジトリ直下の `README.md` をこの内容に沿って更新すること。

---

# Receipt OCR API

## 概要

レシート画像を受け取り、Gemini で画像読解し、OpenAI Structured Outputs でフロントエンド確認用 JSON に整形する OCR API です。

この API は DB 登録を行いません。OCR 結果はユーザー確認前の仮データとして返します。

## 処理フロー

```txt
レシート画像
  ↓
Gemini で画像読解
  ↓
OpenAI Structured Outputs で JSON 厳密化
  ↓
Pydantic で検証
  ↓
フロントエンド確認画面へ返却
```

## セットアップ

```bash
uv sync
cp .env.example .env
```

`.env` に API キーを設定します。

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
MAX_IMAGE_BYTES=10485760
ALLOWED_IMAGE_MIME_TYPES=image/jpeg,image/png,image/webp
APP_ENV=local
LOG_LEVEL=INFO
```

## 起動

```bash
uv run uvicorn app.main:app --reload
```

## API

### GET /health

```bash
curl http://localhost:8000/health
```

### POST /ocr/receipts/extract

```bash
curl -X POST "http://localhost:8000/ocr/receipts/extract" \
  -F "file=@./samples/receipt.jpg"
```

## レスポンス例

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

## 注意

この API は OCR 結果を DB に登録しません。

フロントエンドでユーザーが確認・修正したあと、database API に登録する想定です。

## テスト

```bash
uv run python -m compileall app
uv run pytest
```

外部 API を直接呼ぶテストはありません。Gemini provider と OpenAI provider はモックします。
