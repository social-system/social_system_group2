# Milestone 05: Gemini Provider Implementation

## 目的

Gemini を使ってレシート画像から中間情報を抽出する provider を実装する。

Gemini の出力は最終レスポンスではない。必ず OpenAI Structured Outputs に渡す中間情報として扱う。

## 実装対象

- `app/providers/gemini_provider.py` の実 API 呼び出し
- API キーとモデル名の settings 化
- Gemini 用プロンプト
- 失敗時の例外変換
- provider 単体テストは外部 API をモック

## 入力

```txt
image_bytes: bytes
mime_type: str
```

## 出力

```python
GeminiExtractionResult(text="...")
```

## プロンプト方針

Gemini には次を指示する。

```txt
日本のレシート画像から読み取れる情報を抽出してください。
店舗名、購入日、合計金額、商品明細、数量、単位、単価、明細金額、割引、税、小計を分けてください。
読めない値は不明と書いてください。
推測で補完しすぎないでください。
この出力は後続の構造化処理に渡されます。
```

## 出力形式

Gemini の出力は、厳密 JSON でなくてもよい。

ただし、後続処理が扱いやすいように、見出し付きテキストまたは JSON 風テキストを推奨する。

例:

```txt
店舗名: サンプルスーパー
購入日: 2026/05/12
合計金額: 636円
明細:
- タマゴM 10コ / 238円
- センザイ / 398円
警告:
- なし
```

## エラー処理

Gemini API 呼び出しで失敗した場合は、`GeminiProviderError` を投げる。

API レスポンス本文全体を例外 message に入れない。

## テスト

外部 API を直接呼ばない。

追加するテスト:

- Gemini クライアント成功時に `GeminiExtractionResult` を返す
- Gemini クライアント失敗時に `GeminiProviderError` を投げる
- API キー未設定時の挙動が明確である

## 完了条件

```bash
uv run python -m compileall app
uv run pytest
```

## 注意

このマイルストーン後も、Gemini 出力を API レスポンスとして直接返してはいけない。
