# Provider Design

## 目的

このドキュメントは、Gemini と OpenAI Structured Outputs の呼び出し部分をどのように分離するかを定義する。

外部 API 呼び出しはテストで直接実行しない。必ず provider として分離し、テストではモックできるようにする。

## 全体構成

```txt
FastAPI Route
  ↓
ReceiptOcrService
  ↓
GeminiProvider
  ↓
OpenAIStructuredProvider
  ↓
Pydantic Validation
```

## 各層の責務

### Route

Route は HTTP の入出力だけを担当する。

担当すること:

- `UploadFile` を受け取る
- MIME type とサイズの基本検証を呼ぶ
- service を呼ぶ
- service の結果を返す
- 例外を適切な HTTP エラーへ変換する

担当しないこと:

- Gemini への直接接続
- OpenAI への直接接続
- OCR 結果の加工ロジック
- DB 登録

### ReceiptOcrService

OCR の全体処理をまとめる。

担当すること:

- 画像 bytes を受け取る
- Gemini provider を呼ぶ
- Gemini の出力を OpenAI provider に渡す
- OpenAI の出力を Pydantic で検証する
- 合計不一致などの追加 warnings を補う
- `OcrReceiptResponse` を返す

### GeminiProvider

Gemini に画像を渡し、レシート画像から読み取れる情報を抽出する。

返却値は、原則として文字列または JSON 風の候補情報でよい。

Gemini の出力を最終レスポンスとして扱ってはいけない。

### OpenAIStructuredProvider

Gemini の出力を受け取り、OpenAI Structured Outputs で厳密な JSON に変換する。

返却値は、Pydantic model に変換できる dict とする。

## 推奨インターフェース

### GeminiProvider

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class GeminiExtractionResult:
    text: str

class GeminiProvider:
    async def extract_receipt_text(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
    ) -> GeminiExtractionResult:
        ...
```

### OpenAIStructuredProvider

```python
class OpenAIStructuredProvider:
    async def structure_receipt(
        self,
        *,
        gemini_text: str,
    ) -> dict:
        ...
```

### ReceiptOcrService

```python
class ReceiptOcrService:
    async def extract_receipt(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
    ) -> OcrReceiptResponse:
        ...
```

## Gemini Provider 仕様

### 入力

- `image_bytes`
- `mime_type`

### 出力

```python
GeminiExtractionResult(text="...")
```

### Gemini に渡すプロンプト方針

Gemini には、画像から読み取れる情報をできるだけ忠実に抽出させる。

重要な指示:

- レシート画像から読み取れる文字を抽出する
- 店舗名、購入日、合計金額、商品明細を分ける
- 読みにくい箇所は「不明」とする
- 推測で補完しすぎない
- 合計、税、割引、小計なども読み取る
- 出力は後続の構造化処理に渡すための中間情報である

### Gemini 出力例

```txt
店舗名: サンプルスーパー
日付: 2026/05/12
合計: 636円
明細:
- タマゴM 10コ 238円
- センザイ 398円
```

Gemini に完全な JSON を強制しすぎない。最終的な JSON 厳密化は OpenAI Structured Outputs が担当する。

## OpenAI Structured Provider 仕様

### 入力

- Gemini の抽出結果文字列

### 出力

- `dict`
- `OcrReceiptResponse` に変換可能であること

### OpenAI に渡す内容

OpenAI provider は、次を渡す。

- system または developer message: 役割と制約
- user message: Gemini の出力
- response_format または structured outputs 用 schema

### OpenAI に渡す指示内容

```txt
あなたは日本のレシートOCR結果をフロントエンド確認用JSONへ整形する係です。
不明な値は null にしてください。
推測で埋めないでください。
金額は円の整数にしてください。
日付は YYYY-MM-DD にしてください。
商品名は raw_name と normalized_name に分けてください。
在庫対象かどうかの候補を is_inventory_target に入れてください。
基準単位への変換が分からない場合は base_quantity と base_unit を null にしてください。
合計不一致や曖昧な箇所は warnings に入れてください。
```

## 例外設計

provider 層では、外部 API の失敗をそのまま FastAPI の `HTTPException` にしない。

アプリ内例外に変換する。

例:

```python
class ExternalProviderError(Exception):
    pass

class StructuredOutputError(Exception):
    pass
```

Route または exception handler で HTTP ステータスへ変換する。

## テスト方針

外部 API は必ずモックする。

### テストで確認すること

- GeminiProvider の正常結果を service が OpenAI provider に渡す
- OpenAI provider の dict を Pydantic が検証する
- GeminiProvider が例外を出した場合、API は 502 を返す
- OpenAI provider が例外を出した場合、API は 502 を返す
- OpenAI provider が schema 不一致の dict を返した場合、API は 422 または 502 を返す

## ダミー Provider

開発初期やテストでは、固定レスポンスを返す dummy provider を使ってよい。

例:

```python
class DummyGeminiProvider:
    async def extract_receipt_text(self, *, image_bytes: bytes, mime_type: str):
        return GeminiExtractionResult(text="店舗名: サンプルスーパー\n合計: 636円")
```

ただし、本番コードで dummy provider が誤って使われないよう、設定で切り替える場合は `APP_ENV` などを明確に見ること。

## ログ方針

ログに出してよいもの:

- リクエスト処理開始
- 画像 MIME type
- 画像サイズ
- 外部 API 呼び出しの成功/失敗
- エラーコード

ログに出してはいけないもの:

- API キー
- レシート画像 bytes
- 外部 API の生レスポンス全文
- 個人情報を含む可能性があるレシート文字列全文

開発中に必要であっても、レシート全文ログは避ける。

## 実装時の注意

- provider は service へ依存注入しやすい形にする。
- `app.main` で直接 provider の詳細ロジックを書かない。
- Route のテストで外部 API に接続しない。
- provider の API キーは settings から取得する。
- settings は import 時に外部 API 接続を行わない。
