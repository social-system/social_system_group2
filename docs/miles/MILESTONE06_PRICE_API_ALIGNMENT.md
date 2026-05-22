# MILESTONE06: 最安店APIとの整合性確認

## Codex指示

```text
AGENTS.md、README.md、docs/miles/README.md、docs/miles/MILESTONE06_PRICE_API_ALIGNMENT.md を読んでください。
このmileでは、商品名解決後の product_id を使って、最安店APIが正しく動くかをDB側で確認・修正してください。
```

## 目的

UIで食材検索したときに、過去の購入履歴から最も安く購入できた店名を表示できるようにする。

## 前提

最安店APIは、商品名ではなく `product_id` を基準に検索する。

理由は、OCRの `normalized_name` には表記揺れがあるためである。

## API

既に存在する場合は仕様に合っているか確認する。
存在しない場合は実装する。

```http
GET /prices/cheapest?product_id=1&period_days=90
```

## 比較ルール

単純に `line_total` が最小の明細を返してはいけない。
必ず共通単位あたり価格で比較する。

```text
price_per_base_unit = line_total / base_quantity
```

例:

```text
卵 1パック 238円 base_quantity=10 -> 1個あたり23.8円
卵 6個 180円 base_quantity=6 -> 1個あたり30円
```

この場合、最安は238円の1パックである。

## 対象外にするデータ

以下は価格比較対象外にする。

```text
product_id が一致しない
base_quantity が null
base_quantity <= 0
base_unit が null
store_name が null
purchased_at が period_days の範囲外
```

## Response

該当あり:

```json
{
  "product_id": 1,
  "product_name": "卵",
  "period_days": 90,
  "cheapest": {
    "store_name": "サンプルスーパー",
    "price_per_base_unit": 23.8,
    "line_total": 238,
    "base_quantity": "10.00",
    "base_unit": "個",
    "purchased_at": 20260512,
    "receipt_item_id": 31
  }
}
```

該当なし:

```json
{
  "product_id": 1,
  "product_name": "卵",
  "period_days": 90,
  "cheapest": null
}
```

## product_id解決との関係

`POST /receipts/prepare` と `POST /product-aliases` により、表記揺れがあっても登録時に `product_id` へ寄せる。

最安店APIは、その結果として保存された `receipt_items.product_id` のみを見る。

`normalized_name` で検索しない。

## テスト

最低限、以下を追加または更新する。

```text
同じproduct_idの購入履歴から最安店を返す
line_totalではなく line_total / base_quantity で比較する
store_nameがnullの履歴は除外する
base_quantityがnullの履歴は除外する
base_quantityが0の履歴は除外する
base_unitがnullの履歴は除外する
period_days範囲外は除外する
該当なしなら cheapest null を返す
別product_idは混ざらない
product_idが存在しない場合は404またはcheapest null方針が明確である
```

## 非ゴール

このmileでは以下を実装しない。

```text
商品名queryからproduct_idを探すUI用API
複数店舗ランキング
価格推移API
実質価格の割引按分
OCR側修正
```

## 実行コマンド

```bash
uv run python -m compileall app
uv run pytest
```

## 完了報告

以下を報告する。

```text
変更したファイル:
最安店APIの仕様:
価格比較式:
追加・更新したテスト:
実行したコマンド:
テスト結果:
残TODO:
```
