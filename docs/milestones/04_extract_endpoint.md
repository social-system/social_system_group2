# Milestone 04: Extract Endpoint

## 目的

`POST /ocr/receipts/extract` を実装し、画像アップロードから OCR service 実行までをつなぐ。

この段階では、provider は fake または実 provider のどちらでもよいが、テストでは必ずモックする。

## 実装対象

- `POST /ocr/receipts/extract`
- multipart file 受け取り
- MIME type 検証
- サイズ検証
- service 呼び出し
- エラーを HTTP レスポンスに変換
- API テスト

## Request

```txt
multipart/form-data
field: file
```

## Response

正常時:

```json
{
  "status": "needs_confirmation",
  "store_name": null,
  "purchased_at": null,
  "total_amount": null,
  "items": [],
  "warnings": []
}
```

## 処理手順

```txt
1. UploadFile を受け取る
2. file が存在するか確認する
3. content_type を確認する
4. bytes を読み込む
5. サイズを確認する
6. ReceiptOcrService.extract_receipt を呼ぶ
7. OcrReceiptResponse を返す
```

## エラー変換

| app error | HTTP status | code |
|---|---:|---|
| Missing file | 400 | `missing_file` |
| InvalidImageTypeError | 400 | `invalid_image_type` |
| ImageTooLargeError | 413 | `image_too_large` |
| InvalidImageError | 422 | `invalid_image` |
| GeminiProviderError | 502 | `gemini_provider_failed` |
| OpenAIProviderError | 502 | `openai_provider_failed` |
| StructuredOutputError | 422 | `structured_validation_failed` |

## テスト

追加するテスト:

- 正常な画像で `200`
- `status = needs_confirmation`
- 不正 MIME type で `400`
- サイズ超過で `413`
- Gemini provider 失敗で `502`
- OpenAI provider 失敗で `502`
- Structured validation 失敗で `422`

## 実装上の注意

- `UploadFile.content_type` だけを完全に信用しすぎない。ただし MVP では content_type 検証を最優先にする。
- 画像 bytes をログに出さない。
- 読み込んだ bytes をファイル保存しない。
- service を route 内で直接 new してもよいが、テストしづらい場合は dependency にする。

## 完了条件

```bash
uv run python -m compileall app
uv run pytest
```
