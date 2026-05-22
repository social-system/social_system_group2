# MILESTONE08: 結合テストとドキュメント更新

## Codex指示

```text
AGENTS.md、README.md、docs/miles/README.md、docs/miles/MILESTONE08_INTEGRATION_TESTS_AND_DOCS.md を読んでください。
このmileでは、OCR -> prepare -> receipts登録 -> prices/cheapest までの流れを確認するテストとドキュメントを追加してください。
```

## 目的

フロントエンド修正を最小限にした新しい連携フローが、実際に成立することを確認する。

## 対象

原則としてDBリポジトリを対象にする。
OCRリポジトリ側の結合テストが必要な場合は、別作業として扱う。

## 確認する流れ

```text
1. OCR風JSONを作る
2. POST /receipts/prepare に送る
3. product_aliases により product_id が解決される
4. response.receipt を POST /receipts に送る
5. GET /prices/cheapest?product_id=... で store_name が返る
```

## 結合テスト例

準備データ:

```text
Product: 卵, default_base_unit=個
ProductAlias: たまご -> 卵
Store name: サンプルスーパー
```

OCR風入力:

```json
{
  "status": "needs_confirmation",
  "store_name": "サンプルスーパー",
  "purchased_at": "2026-05-12",
  "total_amount": 238,
  "items": [
    {
      "raw_name": "タマゴM 10コ",
      "normalized_name": "たまご",
      "category_name": "食費",
      "purchased_quantity": 1,
      "purchased_unit": "パック",
      "base_quantity": 10,
      "base_unit": "個",
      "unit_price": 238,
      "line_total": 238,
      "is_inventory_target": true,
      "confidence": 0.8,
      "warnings": []
    }
  ],
  "warnings": []
}
```

期待:

```text
prepareで product_id が解決される
prepareの receipt は POST /receipts に送れる
登録後、prices/cheapest が サンプルスーパー を返す
price_per_base_unit は 23.8 になる
```

## 未解決ケースのテスト

OCR風入力で `normalized_name = ミソ` とし、aliasがない場合を確認する。

期待:

```text
prepareは200を返す
receipt.items[0].product_id は null
item_resolutions[0].resolution_status は unresolved
product_candidates が返る、または空配列で返る
POST /receipts はproduct_id nullでも購入履歴として保存できる
ただし prices/cheapest の対象にはならない
```

## alias学習ケースのテスト

```text
1. prepareで未解決になる
2. POST /product-aliases で ミソ -> 味噌 を登録する
3. 再度 prepare すると product_id が解決される
```

## ドキュメント更新

READMEまたはAPIドキュメントに以下を追加する。

```text
OCRとDBの連携フロー
POST /receipts/prepare の役割
OCR normalized_name は正式名ではなく候補であること
product_id はDB側で解決すること
未解決商品の扱い
alias学習の流れ
最安店表示は product_id を基準にすること
```

## テスト

最低限、以下を追加する。

```text
OCR風JSON -> prepare -> receipts登録 が成功する
prepareでaliasからproduct_idが解決される
登録後 prices/cheapest がstore_nameを返す
未解決商品は item_resolutions に unresolved として返る
alias学習後に同じ商品名が解決される
prepareの receipt にOCR専用項目が含まれない
```

## 非ゴール

このmileでは以下を実装しない。

```text
新しいDB設計変更
高度な曖昧検索
フロントエンド実装
OCR実行そのものを含むE2Eテスト
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
追加した結合テスト:
更新したドキュメント:
確認できた連携フロー:
実行したコマンド:
テスト結果:
残TODO:
```
