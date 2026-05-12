# Milestone 01: Schema and Image Validation

## 目的

OCR API のレスポンス schema と、画像アップロード検証を実装する。

この段階では、外部 API 呼び出しはまだ実装しない。

## 実装対象

- `app/schemas/ocr.py`
- `app/utils/image_validation.py`
- 画像 MIME type 検証
- 画像サイズ検証
- OCR レスポンス Pydantic model
- schema の単体テスト
- image validation の単体テスト

## OCR Response Schema

`OcrReceiptResponse` を実装する。

フィールド:

```txt
status: Literal["needs_confirmation"]
store_name: str | None
purchased_at: str | None
total_amount: int | None
items: list[OcrReceiptItem]
warnings: list[str]
```

`OcrReceiptItem` を実装する。

フィールド:

```txt
raw_name: str | None
normalized_name: str | None
category_name: str | None
purchased_quantity: float | None
purchased_unit: str | None
base_quantity: float | None
base_unit: str | None
unit_price: int | None
line_total: int | None
is_inventory_target: bool | None
confidence: float | None
warnings: list[str]
```

## バリデーション

### 金額

次は `null` または 0 以上。

- `total_amount`
- `unit_price`
- `line_total`

### 数量

次は `null` または 0 より大きい。

- `purchased_quantity`
- `base_quantity`

### confidence

`null` または 0 以上 1 以下。

### purchased_at

`null` または `YYYY-MM-DD`。

## image_validation

関数例:

```python
def validate_image_upload(
    *,
    content_type: str | None,
    content_length: int,
    allowed_mime_types: set[str],
    max_image_bytes: int,
) -> None:
    ...
```

または、実装上扱いやすい形にしてよい。

## エラー

次のアプリ内例外を定義して使う。

```txt
InvalidImageTypeError
ImageTooLargeError
InvalidImageError
```

HTTPException を utility 内で直接作るより、route 側で HTTP に変換しやすい形を推奨する。

## テスト

追加するテスト:

- 正常な `OcrReceiptResponse` が作れる
- `null` を含む `OcrReceiptResponse` が作れる
- 負の金額は validation error
- 0 以下の数量は validation error
- confidence が 1 を超えると validation error
- 不正な日付形式は validation error
- 許可 MIME type は通る
- 不正 MIME type はエラー
- サイズ超過はエラー

## 完了条件

```bash
uv run python -m compileall app
uv run pytest
```

## 非対象

- Gemini 呼び出し
- OpenAI 呼び出し
- extract API の本実装
