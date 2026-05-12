# Receipt OCR API

レシート画像からフロントエンド確認用の仮データを作る OCR API プロジェクトです。

この API は DB 登録を行いません。OCR 結果はユーザー確認前の候補データとして扱い、確定保存や database API 呼び出し、在庫反映、レシピ提案、認証、ユーザー管理は担当しません。

## Setup

```bash
uv sync
```

API キーなどの秘密情報はプロジェクトファイルに保存しないでください。このプロジェクトは `.env` ファイルを使いません。

## Run

```bash
uv run uvicorn app.main:app --reload
```

## Test

```bash
uv run python -m compileall app
uv run pytest
```

## Health Check

```bash
curl http://localhost:8000/health
```

レスポンス:

```json
{
  "status": "ok"
}
```

この段階では、OCR処理、画像アップロード、Gemini/OpenAI provider、DB登録は未実装です。
