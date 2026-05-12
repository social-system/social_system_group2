# AGENTS.md

## 目的

このリポジトリは、レシート画像からフロントエンド確認用の仮データを作る OCR API プロジェクトである。

OCR API は、レシート画像を受け取り、Gemini で画像読解を行い、OpenAI Structured Outputs で JSON を厳密化し、Pydantic で検証した結果を返す。

このプロジェクトは DB 登録を担当しない。OCR 結果は必ずユーザー確認前の仮データとして扱う。

## 最重要ルール

次の処理は実装しないこと。

- DB 登録
- database API の直接呼び出し
- 在庫反映
- レシピ提案
- ユーザー認証
- ユーザー管理
- 画像の永続保存
- API キーや秘密情報の直書き

OCR API の責務は、画像から読み取った候補を、フロントエンドが確認・修正できる JSON として返すことだけである。

## 実装前に必ず読むファイル

実装前に、次の順番で読むこと。

1. `docs/OCR_PROJECT_SPEC.md`
2. `docs/API_SPEC.md`
3. `docs/STRUCTURED_OUTPUT_SCHEMA.md`
4. `docs/PROVIDER_DESIGN.md`
5. `docs/FRONTEND_HANDOFF_SPEC.md`
6. `docs/ERROR_HANDLING.md`
7. `docs/TESTING_STRATEGY.md`
8. 作業対象の `docs/milestones/*.md`

## 推奨ディレクトリ構成

```txt
app/
  main.py
  config.py
  schemas/
    ocr.py
  services/
    receipt_ocr_service.py
  providers/
    gemini_provider.py
    openai_structured_provider.py
  utils/
    image_validation.py
    errors.py
  logging_config.py
tests/
  test_health.py
  test_extract_receipt.py
  test_image_validation.py
  test_structured_schema.py
  test_receipt_ocr_service.py
README.md
.env.example
pyproject.toml
```

既存プロトタイプの構成に合わせる必要はない。1から作り直してよい。

## 技術方針

- API は FastAPI で実装する。
- スキーマ検証は Pydantic を使う。
- 設定管理は `pydantic-settings` を使う。
- HTTP クライアントが必要な場合は `httpx` を使う。
- テストは `pytest` を使う。
- 外部 API を呼ぶ処理は provider に分離し、テストでは必ずモックできるようにする。
- 型注釈を付け、責務が分かる関数名にする。

## 環境変数

`.env` はコミットしない。`.env.example` を用意する。

必要な環境変数は次の通り。

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

モデル名は環境変数で変更可能にする。コード内に固定しない。

## API 仕様の原則

### `GET /health`

- アプリの起動確認用。
- 外部 API には接続しない。
- 正常時は `200` を返す。

### `POST /ocr/receipts/extract`

- `multipart/form-data` で `file` を受け取る。
- 画像形式とサイズを検証する。
- Gemini で画像読解を行う。
- Gemini の出力を OpenAI Structured Outputs に渡す。
- OpenAI の出力を Pydantic で検証する。
- `status = "needs_confirmation"` の JSON を返す。
- DB には保存しない。

## レスポンス方針

OCR 結果は確定データではない。必ず次のステータスで返す。

```json
{
  "status": "needs_confirmation"
}
```

読み取れない値を推測で埋めてはいけない。不明な場合は `null` にする。

合計金額と明細合計が一致しない場合でもエラーにしない。`warnings` に警告を入れて返す。

## Structured Outputs 方針

OpenAI Structured Outputs に渡す JSON Schema は、次の方針で作る。

- `strict: true` を使う。
- 各 object に `additionalProperties: false` を指定する。
- 全フィールドを `required` にする。
- 任意項目は `null` を許す型にする。
- スキーマにないキーを返さない。
- 金額は円を想定し、整数で扱う。
- 日付は `YYYY-MM-DD` 文字列に統一する。

## 画像検証方針

対応 MIME type は次のみ。

- `image/jpeg`
- `image/png`
- `image/webp`

不正な MIME type は `400`。
サイズ超過は `413`。
画像ファイルとして読み取れない場合は `422`。

## エラー方針

- クライアント入力の問題は `4xx`。
- 外部 API の失敗は `502`。
- 想定外の内部エラーは `500`。
- エラー時も、可能な限り同じ形式で返す。

エラーの詳細に API キー、内部スタックトレース、外部 API の生レスポンス全体を含めてはいけない。

## テスト方針

外部 API を直接呼ぶテストを書いてはいけない。Gemini provider と OpenAI provider はモックする。

最低限、次を確認する。

- `GET /health` が `200` を返す。
- 正常な画像アップロードで `status = needs_confirmation` を返す。
- 不正な MIME type で `400` を返す。
- サイズ超過で `413` を返す。
- Gemini provider の失敗で `502` を返す。
- OpenAI provider の失敗で `502` を返す。
- 不正な構造化 JSON で `422` または `502` を返す。
- `null` を含むレスポンスが Pydantic 検証を通る。
- 合計金額と明細合計の不一致はエラーにせず `warnings` に入る。

## 実装完了条件

作業後に必ず次を実行する。

```bash
uv run python -m compileall app
uv run pytest
```

どちらかが失敗した場合は、原因を確認し、修正する。

最後の報告では、次を記載する。

- 変更したファイル
- 追加した API
- 追加した主なスキーマ
- 実行したテストコマンド
- テスト結果
- 残 TODO

## 迷ったときの判断基準

このプロジェクトでは、OCR の完全自動化よりも、ユーザー確認画面へ安全に渡せる仮データを作ることを優先する。

判断に迷った場合は、次の優先順位に従う。

1. 誤った確定データを作らない
2. 不明な値は `null` にする
3. フロントエンドが確認しやすい形にする
4. DB との結合を避ける
5. 外部 API をモックしやすい構成にする
