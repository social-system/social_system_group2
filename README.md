# レシートOCR API

レシート画像を受け取り、フロントエンドの確認画面に表示するためのOCR候補データを返すFastAPIアプリケーションです。

返却データは、ユーザー確認前の一時的な候補です。このリポジトリはデータベース登録、データベースAPI呼び出し、在庫反映、レシピ提案、認証、ユーザー管理、画像保存、バックグラウンドジョブを担当しません。

## 対象範囲

このAPIが担当すること:

- レシート画像の入力検証
- Geminiによる画像読み取り
- OpenAI Structured Outputsによる厳密なJSON正規化
- Pydanticによる最終レスポンス検証
- フロントエンド確認用の候補データ返却

このAPIが担当しないこと:

- レシートや明細のデータベース登録
- データベースAPI / 会計APIの呼び出し
- 在庫テーブルへの反映
- レシピ提案
- ユーザー認証・ユーザー管理
- レシート画像の永続保存

## 処理の流れ

```text
レシート画像
  -> 画像検証
  -> Geminiによる画像読み取り
  -> OpenAI Structured Outputsによる正規化
  -> Pydantic検証
  -> フロントエンド確認用レスポンス
```

外部モデル呼び出しはプロバイダークラスに分離されています。

```text
ルート
  -> ReceiptOcrService
      -> GeminiProvider
      -> OpenAIStructuredProvider
      -> Pydantic検証
```

## 動作要件

- Python 3.12以上
- uv

## セットアップ

```bash
uv sync
```

## 起動

APIキーなしでアプリケーションを起動できます。

```bash
uv run uvicorn app.main:app --reload
```

既定のローカルURL:

```text
http://127.0.0.1:8000
```

FastAPIの自動ドキュメント:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`
- `http://127.0.0.1:8000/openapi.json`

## 設定

設定はOS環境変数から`pydantic-settings`で読み込みます。このプロジェクトは`.env`ファイルを使いません。

アプリケーションの起動に`OPENAI_API_KEY`と`GEMINI_API_KEY`は不要です。実プロバイダーの実行時だけAPIキーが必要です。未設定のまま実プロバイダーが呼ばれた場合、公開APIレスポンスでは不足しているキー名や値を出さず、`provider_not_configured`を返します。

| 名前 | 起動時に必須 | 実プロバイダー呼び出し時に必須 | 既定値 | 説明 |
|---|---:|---:|---|---|
| `GEMINI_API_KEY` | いいえ | はい | なし | Gemini APIキー |
| `GEMINI_MODEL` | いいえ | いいえ | `gemini-2.5-flash` | Geminiモデル |
| `OPENAI_API_KEY` | いいえ | はい | なし | OpenAI APIキー |
| `OPENAI_MODEL` | いいえ | いいえ | `gpt-5.4-mini` | OpenAIモデル |
| `MAX_IMAGE_BYTES` | いいえ | いいえ | `10485760` | アップロード画像の最大バイト数 |
| `ALLOWED_IMAGE_MIME_TYPES` | いいえ | いいえ | `image/jpeg,image/png,image/webp` | 許可する画像MIMEタイプ。カンマ区切り文字列を指定できます |
| `APP_ENV` | いいえ | いいえ | `local` | アプリケーション環境名 |
| `LOG_LEVEL` | いいえ | いいえ | `INFO` | ログレベル名 |

秘密情報の扱い:

- 実APIキーをREADME、テスト、ログ、コミット対象ファイルに書かない
- 環境変数の中身を出力しない
- Codexに実APIキーを渡さない
- Codexに実Gemini / OpenAI API呼び出しを実行させない

## API

このアプリケーションが定義しているAPIは次の2つです。

| メソッド | パス | 用途 |
|---|---|---|
| `GET` | `/health` | ヘルスチェック |
| `POST` | `/ocr/receipts/extract` | レシート画像1枚からOCR候補データを抽出 |

### GET /health

ヘルスチェックです。プロバイダーやAPIキーの状態は確認しません。

リクエスト:

```bash
curl http://127.0.0.1:8000/health
```

`200`レスポンス:

```json
{
  "status": "ok"
}
```

レスポンス項目:

| 項目 | 型 | 説明 |
|---|---|---|
| `status` | 文字列 | 常に`ok` |

### POST /ocr/receipts/extract

レシート画像1枚から、フロントエンド確認用の候補データを抽出します。

このエンドポイントは`multipart/form-data`を受け付けます。成功時のレスポンスは確定データではなく、必ず`status = "needs_confirmation"`の候補データです。

リクエスト:

```bash
curl -X POST "http://127.0.0.1:8000/ocr/receipts/extract" \
  -F "file=@sample_receipt.jpg;type=image/jpeg"
```

リクエスト項目:

| 項目 | 型 | 必須 | 説明 |
|---|---|---:|---|
| `file` | ファイル | はい | レシート画像 |

受け付ける画像MIMEタイプ:

- `image/jpeg`
- `image/png`
- `image/webp`

最大ファイルサイズは`MAX_IMAGE_BYTES`で制御します。既定値は`10485760`バイトです。

`200`レスポンス例:

```json
{
  "status": "needs_confirmation",
  "store_name": "サンプルストア",
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

トップレベルのレスポンス項目:

| 項目 | 型 | 必須 | 説明 |
|---|---|---:|---|
| `status` | 文字列 | はい | 成功時は常に`needs_confirmation` |
| `store_name` | 文字列またはnull | はい | レシート上の店舗名候補。読めない場合は`null` |
| `purchased_at` | 文字列またはnull | はい | 購入日候補。値がある場合は`YYYY-MM-DD` |
| `total_amount` | 整数またはnull | はい | 最終支払金額候補。値がある場合は`0`以上 |
| `items` | 配列 | はい | 明細候補の配列 |
| `warnings` | 文字列の配列 | はい | レシート全体に対する非致命的な警告 |

明細項目:

| 項目 | 型 | 必須 | 説明 |
|---|---|---:|---|
| `raw_name` | 文字列またはnull | はい | レシート上の商品名候補。過度に正規化しない値 |
| `normalized_name` | 文字列またはnull | はい | OCRが推定した商品名候補。データベースの`products.name`と一致する保証はない |
| `category_name` | 文字列またはnull | はい | 会計カテゴリ名候補。カテゴリIDは返さない |
| `purchased_quantity` | 数値またはnull | はい | レシート上の購入単位の数量。値がある場合は`0`より大きい |
| `purchased_unit` | 文字列またはnull | はい | レシート上の購入単位 |
| `base_quantity` | 数値またはnull | はい | アプリ内部基準単位への換算数量。値がある場合は`0`より大きい |
| `base_unit` | 文字列またはnull | はい | アプリ内部基準単位 |
| `unit_price` | 整数またはnull | はい | 単価候補。値がある場合は`0`以上 |
| `line_total` | 整数またはnull | はい | 明細行金額候補。値がある場合は`0`以上 |
| `is_inventory_target` | 真偽値またはnull | はい | 在庫反映対象にするかどうかの候補 |
| `confidence` | 数値またはnull | はい | 明細全体の信頼度候補。値がある場合は`0.0`から`1.0` |
| `warnings` | 文字列の配列 | はい | 明細行ごとの非致命的な警告 |
| `ocr_metadata` | オブジェクト | はい | OCR後処理用のメタデータ |

`ocr_metadata`の項目:

| 項目 | 型 | 必須 | 説明 |
|---|---|---:|---|
| `field_confidence` | オブジェクト | はい | 明細フィールドごとの信頼度候補 |
| `auto_register_candidate` | 真偽値またはnull | はい | 自動登録候補として扱えるかどうかの候補。最終判断ではない |
| `needs_review_reasons` | 文字列の配列 | はい | 自動登録や確定前に確認が必要な理由 |

`field_confidence`の項目:

| 項目 | 型 |
|---|---|
| `raw_name` | 数値またはnull |
| `normalized_name` | 数値またはnull |
| `category_name` | 数値またはnull |
| `purchased_quantity` | 数値またはnull |
| `purchased_unit` | 数値またはnull |
| `base_quantity` | 数値またはnull |
| `base_unit` | 数値またはnull |
| `unit_price` | 数値またはnull |
| `line_total` | 数値またはnull |
| `is_inventory_target` | 数値またはnull |

すべての`field_confidence`値は、値がある場合`0.0`から`1.0`です。

検証ルール:

- 不明な値は推測せず`null`にする
- 未定義のオブジェクトキーは拒否される
- `purchased_at`は、値がある場合`YYYY-MM-DD`であること
- `total_amount`、`unit_price`、`line_total`は、値がある場合`0`以上であること
- `purchased_quantity`と`base_quantity`は、値がある場合`0`より大きいこと
- `confidence`とフィールド別信頼度は、値がある場合`0.0`から`1.0`であること

重要なAPI挙動:

- このAPIはデータベースに登録しない
- このAPIはデータベースAPIまたは会計APIを呼び出さない
- このAPIは`product_id`、`category_id`、`receipt_id`、`receipt_item_id`を返さない
- `normalized_name`はOCRが推定した商品名候補である
- 最終的なID解決、修正、データベース登録はこのサービスの外側の責務である
- 合計金額と明細合計が一致しなくてもリクエストは失敗しない。サービス層が検出できる場合に警告を1つ追加する

## エラーレスポンス

ルート固有のエラーは次の形で返します。

```json
{
  "detail": {
    "code": "unsupported_image_type",
    "message": "Unsupported image type."
  }
}
```

`POST /ocr/receipts/extract`のエラー:

| ステータス | コード | メッセージ | 発生条件 |
|---:|---|---|---|
| 400 | `unsupported_image_type` | `Unsupported image type.` | `file`のMIMEタイプが許可されていない |
| 400 | `empty_file` | `File is empty.` | アップロードファイルが0バイト |
| 413 | `image_too_large` | `Uploaded image is too large.` | アップロードファイルが`MAX_IMAGE_BYTES`を超えている |
| 422 | `structured_output_invalid` | `Structured OCR output is invalid.` | 最終的な構造化データがPydantic検証に失敗した |
| 502 | `provider_not_configured` | `OCR provider is not configured.` | 必要な設定がない状態で実プロバイダー経路が呼ばれた |
| 502 | `gemini_provider_failed` | `Gemini provider failed.` | Geminiによる抽出に失敗した |
| 502 | `openai_provider_failed` | `OpenAI provider failed.` | OpenAIによる正規化に失敗した |
| 502 | `ocr_provider_failed` | `OCR provider failed.` | 汎用的なOCRプロバイダー失敗 |
| 500 | `internal_server_error` | `Internal server error.` | 想定外のサーバーエラー |

`file`項目がない場合など、FastAPIのリクエスト検証エラーはFastAPI標準の検証レスポンスになる場合があります。

公開エラーレスポンスでは、APIキー、環境変数の値、アップロード画像のバイト列、プロバイダーの生レスポンス、スタックトレースを公開しません。

## フロントエンドでの利用

ブラウザから送信する場合は`FormData`に`file`を入れて送ります。

```ts
const formData = new FormData();
formData.append("file", file);

const response = await fetch("http://127.0.0.1:8000/ocr/receipts/extract", {
  method: "POST",
  body: formData,
});

const result = await response.json();
```

フロントエンドはOCRレスポンスを確定データとして扱わず、ユーザーが確認・修正できる画面に表示してください。

確認画面で扱う主な項目:

- 店舗名
- 購入日
- 合計金額
- 明細行
- トップレベルの警告
- 明細行ごとの警告
- OCRメタデータの信頼度と確認理由

データベース登録前にフロントエンドまたはデータベースAPI側で確認すべき項目:

- `purchased_at`
- `total_amount`
- 明細の`raw_name`
- 明細の`line_total`
- 明細の`is_inventory_target`

在庫対象品では、次の項目も確認対象です。

- 明細の`normalized_name`
- 明細の`purchased_quantity`
- 明細の`purchased_unit`
- 明細の`base_quantity`
- 明細の`base_unit`

現在のアプリケーションコードにはCORS設定がありません。別オリジンのフロントエンドから直接呼び出す場合は、バックエンドにCORS設定を追加するか、フロントエンド開発サーバーでプロキシしてください。

## 人間によるライブ検証

実プロバイダーのライブ検証は任意であり、人間の開発者だけが実行してください。APIキーは現在のコマンドまたは現在のシェルのOS環境変数として渡し、プロジェクトファイルには保存しないでください。

例:

```bash
OPENAI_API_KEY="<人間が設定>" \
GEMINI_API_KEY="<人間が設定>" \
uv run uvicorn app.main:app --reload
```

別のターミナルから実行します。

```bash
curl -X POST "http://127.0.0.1:8000/ocr/receipts/extract" \
  -F "file=@sample_receipt.jpg;type=image/jpeg"
```

Codexにこのライブ検証を実行させないでください。

## テスト

```bash
uv run python -m compileall app
uv run pytest
```

テストは実APIキーや実プロバイダー呼び出しを必要としません。

## プロジェクト構成

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

主要ドキュメント:

- `docs/OCR_PROJECT_SPEC.md`
- `docs/API_SPEC.md`
- `docs/STRUCTURED_OUTPUT_SCHEMA.md`
- `docs/PROVIDER_DESIGN.md`
- `docs/ERROR_HANDLING.md`
- `docs/TESTING_STRATEGY.md`
- `docs/FRONTEND_HANDOFF_SPEC.md`
