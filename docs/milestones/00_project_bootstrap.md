# Milestone 00: Project Bootstrap

## 目的

OCR API を 1 から実装できる最小構成を作る。

この段階では、Gemini や OpenAI への実接続は実装しなくてよい。まずは FastAPI アプリ、設定管理、テスト基盤、基本ディレクトリを整える。

## 実装対象

- FastAPI アプリ作成
- `GET /health` 実装
- `pydantic-settings` による設定管理
- `.env.example` 作成
- テスト基盤作成
- README 初期化

## 推奨ディレクトリ

```txt
app/
  __init__.py
  main.py
  config.py
  logging_config.py
  utils/
    __init__.py
    errors.py
tests/
  test_health.py
README.md
.env.example
pyproject.toml
```

## 設定項目

`app/config.py` に settings を作る。

必要な設定:

```txt
GEMINI_API_KEY
GEMINI_MODEL
OPENAI_API_KEY
OPENAI_MODEL
MAX_IMAGE_BYTES
ALLOWED_IMAGE_MIME_TYPES
APP_ENV
LOG_LEVEL
```

テスト時に API キー未設定で落ちないようにする。実際に外部 API を呼ぶ時点で、必要なキーがなければ provider 側でエラーにする。

## .env.example

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

## GET /health

レスポンス:

```json
{
  "status": "ok",
  "service": "receipt-ocr-api"
}
```

外部 API 接続はしない。

## テスト

追加するテスト:

- `GET /health` が `200` を返す
- レスポンスに `status = ok` が含まれる

## 完了条件

次が成功すること。

```bash
uv run python -m compileall app
uv run pytest
```

## 非対象

このマイルストーンでは次を実装しない。

- OCR 処理
- Gemini provider
- OpenAI provider
- 画像アップロード
- DB 登録
