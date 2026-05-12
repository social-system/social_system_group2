# Structured Output Schema

## Purpose

OpenAI Structured Outputs must convert Gemini's intermediate OCR result into a strict frontend response JSON.

The output is provisional and must use `status = "needs_confirmation"`.

## Strictness rules

The JSON schema must:

- Use strict structured output behavior
- Disallow unknown keys with `additionalProperties: false`
- Mark all fields as required
- Use `null` for unknown optional values
- Avoid invented values
- Return warnings for uncertain or inconsistent values

## Top-level schema shape

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

## Field rules

### status

Must always be:

```text
needs_confirmation
```

### store_name

Type: `string | null`

Use the store name visible on the receipt.
If unreadable, return `null`.

### purchased_at

Type: `string | null`

Format must be:

```text
YYYY-MM-DD
```

If only a partial date is visible or the date is ambiguous, return `null` and add a warning.

### total_amount

Type: `integer | null`

Must be zero or greater if present.
Use the final amount paid if visible.
If subtotal and final total differ, prefer final payment amount.

### items

Type: array of item objects.

Each visible purchased line should become one item when possible.
Discount lines, subtotal lines, tax lines, and payment lines should not become normal purchased items unless the receipt clearly treats them as product rows.

### warnings

Type: array of strings.

Use warnings for non-fatal uncertainty, such as:

- Total amount and item sum do not match
- Date is unclear
- Store name is unclear
- Some lines were ignored
- Unit conversion is uncertain

## Item schema

```json
{
  "raw_name": null,
  "normalized_name": null,
  "category_name": null,
  "purchased_quantity": null,
  "purchased_unit": null,
  "base_quantity": null,
  "base_unit": null,
  "unit_price": null,
  "line_total": null,
  "is_inventory_target": null,
  "confidence": null,
  "warnings": []
}
```

## Item field rules

### raw_name

Type: `string | null`

The item name as read from the receipt.
Do not over-normalize this field.

### normalized_name

Type: `string | null`

A simplified item name candidate for later product matching.
Examples:

| raw_name | normalized_name |
|---|---|
| `タマゴM 10コ` | `卵` |
| `牛乳 1000ml` | `牛乳` |
| `コシヒカリ 5kg` | `米` |

If uncertain, return `null` or keep a conservative normalized candidate with a warning.

### category_name

Type: `string | null`

Candidate accounting category name.
Do not return category IDs.

Examples:

```text
食費
日用品
飲料
調味料
その他
```

### purchased_quantity

Type: `number | null`

Quantity in the unit shown or implied by the receipt.
Must be greater than 0 if present.

### purchased_unit

Type: `string | null`

Unit shown or implied by the receipt.
Examples:

```text
個
本
袋
パック
g
kg
ml
L
```

### base_quantity

Type: `number | null`

Quantity converted to the app's internal base unit.
If conversion is uncertain, return `null`.

Examples:

| Item | purchased_quantity | purchased_unit | base_quantity | base_unit |
|---|---:|---|---:|---|
| 卵 1パック | 1 | パック | 10 | 個 |
| 牛乳 1本 | 1 | 本 | 1000 | ml |
| 米 5kg | 5 | kg | 5000 | g |

Only use product-specific conversion when it is clear from the receipt or common package expression.
If not clear, return `null`.

### base_unit

Type: `string | null`

Internal unit used for inventory and recipe matching.
Examples:

```text
個
g
ml
```

### unit_price

Type: `integer | null`

Must be zero or greater if present.
If only line total is visible, return `null`.

### line_total

Type: `integer | null`

Must be zero or greater if present.
Represents the item row amount.

### is_inventory_target

Type: `boolean | null`

Candidate flag indicating whether the item should affect refrigerator/pantry inventory.

Food ingredients are generally `true`.
Daily goods, bags, services, and non-food items are generally `false`.

If uncertain, return `null` and add an item warning.

### confidence

Type: `number | null`

Range is 0.0 to 1.0.
If confidence cannot be estimated, return `null`.

### warnings

Type: array of strings.

Use warnings for item-level uncertainty.

## Validation rules after Structured Outputs

Pydantic validation must check:

- `status` equals `needs_confirmation`
- `purchased_at` is `YYYY-MM-DD` or null
- `total_amount`, `unit_price`, `line_total` are zero or greater if present
- `purchased_quantity`, `base_quantity` are greater than 0 if present
- `confidence` is between 0 and 1 if present
- `warnings` is always a list
- item `warnings` is always a list

If item totals do not match the top-level total, do not reject the response. Add a warning.
