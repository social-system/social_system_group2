# Receipt OCR API

レシート画像からフロントエンド確認用の仮データを作る OCR API プロジェクトです。

この API は DB 登録を行いません。OCR 結果はユーザー確認前の候補データとして扱い、確定保存や database API 呼び出し、在庫反映、レシピ提案、認証、ユーザー管理は担当しません。

## Setup

```bash
uv sync
cp .env.example .env
```

`.env` はローカル環境用です。API キーなどの秘密情報はコードに直書きしないでください。

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
