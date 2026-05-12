# Error Handling Specification

## 目的

このドキュメントは、OCR API のエラー設計を定義する。

利用者にとって分かりやすく、かつ内部情報を漏らさないエラー形式を採用する。

## 基本形式

エラーレスポンスは次の形式を基本とする。

```json
{
  "error": {
    "code": "invalid_image_type",
    "message": "Unsupported image MIME type.",
    "details": null
  }
}
```

## フィールド

| field | type | description |
|---|---|---|
| error.code | string | 安定したエラーコード |
| error.message | string | 利用者向けの短い説明 |
| error.details | object/null | 補足情報。秘密情報は含めない |

## ステータスコード一覧

| status | code | case |
|---:|---|---|
| 400 | `invalid_image_type` | MIME type が未対応 |
| 400 | `missing_file` | file がない |
| 413 | `image_too_large` | ファイルサイズ超過 |
| 422 | `invalid_image` | 画像として読み取れない |
| 422 | `structured_validation_failed` | Structured Outputs 結果の検証失敗 |
| 502 | `gemini_provider_failed` | Gemini 呼び出し失敗 |
| 502 | `openai_provider_failed` | OpenAI 呼び出し失敗 |
| 500 | `internal_server_error` | 想定外の内部エラー |

## MIME type 不正

### 条件

`content_type` が次以外の場合。

```txt
image/jpeg
image/png
image/webp
```

### レスポンス

```json
{
  "error": {
    "code": "invalid_image_type",
    "message": "Unsupported image MIME type.",
    "details": {
      "allowed": ["image/jpeg", "image/png", "image/webp"]
    }
  }
}
```

### status

```txt
400 Bad Request
```

## サイズ超過

### 条件

画像ファイルが `MAX_IMAGE_BYTES` を超える場合。

### レスポンス

```json
{
  "error": {
    "code": "image_too_large",
    "message": "Image file is too large.",
    "details": {
      "max_image_bytes": 10485760
    }
  }
}
```

### status

```txt
413 Payload Too Large
```

## 画像として不正

### 条件

MIME type は正しいが、画像として処理できない場合。

### レスポンス

```json
{
  "error": {
    "code": "invalid_image",
    "message": "Uploaded file could not be processed as an image.",
    "details": null
  }
}
```

### status

```txt
422 Unprocessable Entity
```

## Gemini provider 失敗

### 条件

Gemini API 呼び出しで失敗した場合。

### レスポンス

```json
{
  "error": {
    "code": "gemini_provider_failed",
    "message": "Receipt image extraction failed.",
    "details": null
  }
}
```

### status

```txt
502 Bad Gateway
```

## OpenAI provider 失敗

### 条件

OpenAI Structured Outputs 呼び出しで失敗した場合。

### レスポンス

```json
{
  "error": {
    "code": "openai_provider_failed",
    "message": "Receipt result structuring failed.",
    "details": null
  }
}
```

### status

```txt
502 Bad Gateway
```

## Structured Outputs 検証失敗

### 条件

OpenAI から返った結果が Pydantic schema を満たさない場合。

### レスポンス

```json
{
  "error": {
    "code": "structured_validation_failed",
    "message": "Structured OCR result did not match expected schema.",
    "details": null
  }
}
```

### status

```txt
422 Unprocessable Entity
```

または、外部 API 由来の壊れた出力とみなす場合は `502` でもよい。

このプロジェクトでは、まずは `422` を推奨する。

## 想定外エラー

### レスポンス

```json
{
  "error": {
    "code": "internal_server_error",
    "message": "Internal server error.",
    "details": null
  }
}
```

### status

```txt
500 Internal Server Error
```

## ログに出してはいけないもの

- API キー
- `.env` の値
- 画像 bytes
- レシート全文
- 外部 API の生レスポンス全文
- 内部スタックトレースを API レスポンスに含めること

## 警告とエラーの違い

次はエラーではなく `warnings` として返す。

- 合計金額と明細合計が一致しない
- 購入日が読めない
- 店舗名が読めない
- 1袋を何個・何gに換算できない
- 商品が在庫対象か判断できない
- 一部の商品名が不明瞭

OCR API は、可能な限りユーザー確認画面に進める。完全に処理不能な場合だけエラーにする。
