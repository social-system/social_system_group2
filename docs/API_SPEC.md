# API Specification

## Base purpose

The API returns candidate receipt data for frontend confirmation.
All returned data is provisional.

## Endpoints

### GET /health

Health check endpoint.

#### Response 200

```json
{
  "status": "ok"
}
```

---

### POST /ocr/receipts/extract

Extract candidate receipt data from one uploaded receipt image.

The endpoint must accept `multipart/form-data`.

#### Request

| Field | Type | Required | Description |
|---|---|---:|---|
| `file` | file | yes | Receipt image |

Allowed MIME types:

```text
image/jpeg
image/png
image/webp
```

Maximum file size is controlled by `MAX_IMAGE_BYTES`.
Default is `10485760` bytes.

#### Response 200

```json
{
  "status": "needs_confirmation",
  "store_name": "Sample Store",
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
      "warnings": []
    }
  ],
  "warnings": [
    "合計金額と明細合計が一致しない可能性があります"
  ]
}
```

#### Response fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `status` | string | yes | Always `needs_confirmation` on success |
| `store_name` | string or null | yes | Store name candidate |
| `purchased_at` | string or null | yes | Purchase date in `YYYY-MM-DD` |
| `total_amount` | integer or null | yes | Final receipt total amount |
| `items` | array | yes | Candidate item rows |
| `warnings` | array of string | yes | Non-fatal warnings |

#### Item fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `raw_name` | string or null | yes | Name as read from receipt |
| `normalized_name` | string or null | yes | Normalized candidate name |
| `category_name` | string or null | yes | Accounting category candidate |
| `purchased_quantity` | number or null | yes | Quantity in receipt unit |
| `purchased_unit` | string or null | yes | Unit as purchased |
| `base_quantity` | number or null | yes | Quantity converted to app base unit |
| `base_unit` | string or null | yes | App base unit |
| `unit_price` | integer or null | yes | Unit price candidate |
| `line_total` | integer or null | yes | Item line total |
| `is_inventory_target` | boolean or null | yes | Candidate for inventory tracking |
| `confidence` | number or null | yes | 0.0 to 1.0 confidence candidate |
| `warnings` | array of string | yes | Item-level warnings |

## HTTP status rules

| Status | When |
|---:|---|
| 200 | Extraction succeeded and candidate data is returned |
| 400 | Invalid request or unsupported MIME type |
| 413 | Uploaded file exceeds `MAX_IMAGE_BYTES` |
| 422 | Image is valid but cannot be interpreted as a receipt, or final data fails validation |
| 502 | Gemini or OpenAI provider fails |
| 500 | Unexpected server error |

## Important behavior

`POST /ocr/receipts/extract` must not register data in a database.

`product_id` and `category_id` must not be returned by the OCR API because this service does not own database master data.

The response must be suitable for frontend correction before final database registration.

## Manual live test example

A human developer may run live testing by setting environment variables only for the current shell command.
Do not store these values in files.

```bash
OPENAI_API_KEY="..." \
GEMINI_API_KEY="..." \
uv run uvicorn app.main:app --reload
```

Then, in another terminal:

```bash
curl -X POST "http://127.0.0.1:8000/ocr/receipts/extract" \
  -F "file=@sample_receipt.jpg;type=image/jpeg"
```

Do not ask Codex to run this live test.
