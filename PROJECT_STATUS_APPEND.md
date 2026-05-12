# PROJECT STATUS.md 追記案

以下を既存の `PROJECT STATUS.md` の末尾に追記する。

```md
## DB 再設計方針

現在の DB は、レシート OCR 結果を直接保存する場所ではなく、ユーザー確認済みの購入履歴を保存する場所として再設計する。

OCR 結果は誤読や欠損を含む可能性があるため、OCR API は一度フロントエンドに仮データを返す。ユーザーが内容を確認・修正した後、DB API に確定データとして登録する。

```text
レシート画像
  -> OCR API
  -> 仮データ
  -> フロントエンド確認
  -> DB API
  -> 確定データ保存
```

## テーブル作り直し

開発初期のため、既存テーブルとの互換性は維持しない。

既存の `receipt_total`、`item`、`num`、`amount`、`total`、`date`、`ingredients` を中心にした設計は廃止する。

新しい主なテーブルは以下とする。

| テーブル | 目的 |
| --- | --- |
| `receipts` | レシート全体 |
| `receipt_items` | レシート明細 |
| `accounting_categories` | 家計簿カテゴリ |
| `products` | 商品マスタ |
| `product_aliases` | レシート表記と商品マスタの対応 |
| `product_unit_conversions` | 商品ごとの単位変換 |

## 重要な設計判断

商品名は、レシート上の名前とアプリ内の名前を分ける。

```text
raw_name: レシート上の商品名
normalized_name: アプリ内で扱う商品名
```

数量と単位は、購入時の表記と在庫・レシピ用の共通単位を分ける。

```text
purchased_quantity / purchased_unit
base_quantity / base_unit
```

同じ商品でも単位が異なる場合は、レシート明細としては別々に保存し、在庫管理では `base_quantity` と `base_unit` で集計する。

例:

```text
卵 1パック -> 10個
卵 6個     -> 6個
在庫合計   -> 16個
```

## Codex による実装方針

Codex に実装を依頼する場合は、以下を最初に読ませる。

```text
AGENTS.md
docs/DATABASE_DESIGN.md
docs/API_SPEC.md
docs/OCR_DB_INTERFACE.md
docs/CODEX_IMPLEMENTATION_PLAN.md
```

今回の実装では、OCR API、画像保存、OCR 仮データ保存、在庫テーブル、レシピ提案 API、認証、ユーザー管理は実装しない。
```
