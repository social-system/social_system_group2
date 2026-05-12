# Milestone 03: Receipt OCR Service

## 目的

Gemini provider と OpenAI provider をつなぐ service 層を実装する。

この段階では、provider は fake でもよい。重要なのは、処理フローと Pydantic 検証が正しく動くことである。

## 実装対象

- `app/services/receipt_ocr_service.py`
- provider の依存注入
- OpenAI provider の dict を Pydantic model に変換
- warnings 補助処理
- service 単体テスト

## 処理フロー

```txt
ReceiptOcrService.extract_receipt
  ↓
GeminiProvider.extract_receipt_text
  ↓
OpenAIStructuredProvider.structure_receipt
  ↓
OcrReceiptResponse.model_validate
  ↓
追加 warnings の補正
  ↓
OcrReceiptResponse を返す
```

## 追加 warnings

service 側で、可能なら次を確認する。

### 明細合計不一致

`total_amount` があり、`items.line_total` がすべて読めている場合、合計が一致しなければ warning を追加する。

文言例:

```txt
明細合計と合計金額が一致していません。割引・税・読み取り漏れを確認してください。
```

### base_quantity 不明

在庫対象候補が `true` で、`base_quantity` または `base_unit` が `null` の場合、item warnings に追加する。

文言例:

```txt
在庫管理用の基準数量または基準単位が不明です。
```

## 例外変換

service は provider 例外を上位へ投げてよい。

ただし、Pydantic validation error は、アプリ内の `StructuredOutputError` などに変換してもよい。

## テスト

追加するテスト:

- fake providers を使って正常な `OcrReceiptResponse` が返る
- Gemini provider が呼ばれる
- OpenAI provider に Gemini の出力が渡る
- OpenAI provider が返した dict が Pydantic 検証される
- 合計不一致時に warning が追加される
- 在庫対象で base_quantity 不明なら item warning が追加される
- OpenAI provider が不正 dict を返すと例外になる

## 完了条件

```bash
uv run python -m compileall app
uv run pytest
```

## 非対象

- 本物の Gemini API 呼び出し
- 本物の OpenAI API 呼び出し
- 画像アップロード route の完成
