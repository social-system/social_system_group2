# MILESTONE07: OCR側契約の最小修正

## Codex指示

```text
AGENTS.md、README.md、OCR設計書、docs/miles/MILESTONE07_OCR_CONTRACT_MINIMAL_UPDATE.md を読んでください。
このmileでは、OCR側のレスポンス契約をDB側 prepare API に合わせて確認・最小修正してください。
DBリポジトリは変更しないでください。
```

## 目的

OCR側は `product_id` を持たず、DB側が `product_id` を解決できる情報だけを返す。

## 重要方針

OCR側は商品マスタを保持しない。

OCR側は `normalized_name -> product_id` の対応を持たない。

OCR側の `normalized_name` は正式名称ではなく、AIが推定した商品名候補である。

## OCRレスポンスの期待形

```json
{
  "status": "needs_confirmation",
  "store_name": "サンプルスーパー",
  "purchased_at": "2026-05-12",
  "total_amount": 636,
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
      "confidence": 0.82,
      "warnings": []
    }
  ],
  "warnings": []
}
```

## OCR側で返してはいけないもの

```text
product_id
category_id
resolution_status
resolution_source
product_candidates
```

これらはDB側の責務である。

## normalized_nameの指示

Gemini/OpenAIに対する指示では、`normalized_name` について以下を明確にする。

```text
normalized_name は、商品マスタ上の正式名ではなく、商品を短く表す候補名である。
不明な場合は null にする。
product_id を推定しない。
商品マスタとの照合はDB側で行う。
```

## warningsの扱い

合計金額と明細合計の不一致警告は、AIに重複して出させない。
決定的な計算で出せる警告はサービス層で1回だけ追加する。

## テスト

最低限、以下を追加または更新する。

```text
OCRレスポンスに product_id が含まれない
OCRレスポンスに category_id が含まれない
OCRレスポンスに raw_name が含まれる
OCRレスポンスに normalized_name が含まれる
normalized_name が null でも検証に通る
store_name が null でも検証に通る
warnings がレスポンスに含まれる
DB APIを呼び出していない
```

## 非ゴール

このmileでは以下を実装しない。

```text
DB API変更
product_id解決
商品検索
alias学習
フロントエンド変更
```

## 実行コマンド

OCRリポジトリの `README.md` または `pyproject.toml` に従う。
一般形は以下。

```bash
uv run python -m compileall .
uv run pytest
```

## 完了報告

以下を報告する。

```text
変更したファイル:
OCR response schemaの最終形:
Structured Outputs schemaの変更:
Gemini/OpenAI promptの変更:
追加・更新したテスト:
実行したコマンド:
テスト結果:
残TODO:
```
