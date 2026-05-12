# Milestone 06: OpenAI Structured Outputs Implementation

## 目的

Gemini の中間出力を、OpenAI Structured Outputs で厳密な JSON に変換する provider を実装する。

## 実装対象

- `app/providers/openai_structured_provider.py` の実 API 呼び出し
- JSON Schema 定義
- Structured Outputs 用プロンプト
- API キーとモデル名の settings 化
- 失敗時の例外変換
- provider テストは外部 API をモック

## 入力

```txt
gemini_text: str
```

## 出力

`OcrReceiptResponse` に変換可能な dict。

## Schema 方針

`docs/STRUCTURED_OUTPUT_SCHEMA.md` に定義された schema を使う。

必須条件:

- `strict: true`
- `additionalProperties: false`
- 全フィールド required
- 任意項目は `null` 許可

## OpenAI への指示方針

```txt
あなたは日本のレシートOCR結果をフロントエンド確認用JSONに整形する係です。
不明な値は null にしてください。
推測で埋めないでください。
スキーマ外のキーを返さないでください。
合計不一致や曖昧な箇所は warnings に入れてください。
このJSONはDB登録用ではなく、ユーザー確認画面用です。
```

## エラー処理

OpenAI API 呼び出しで失敗した場合は、`OpenAIProviderError` を投げる。

OpenAI から返った出力が空、または dict として扱えない場合は、`StructuredOutputError` を投げる。

## テスト

外部 API を直接呼ばない。

追加するテスト:

- OpenAI クライアント成功時に dict を返す
- OpenAI クライアント失敗時に `OpenAIProviderError` を投げる
- 空レスポンスで `StructuredOutputError` を投げる
- schema の key が想定通りである

## 完了条件

```bash
uv run python -m compileall app
uv run pytest
```
