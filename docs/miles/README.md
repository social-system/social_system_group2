# OCR・DB連携改善 milestones

## 目的

OCRの `normalized_name` はAIが推定した商品名候補であり、DBが管理する正式な商品名ではない。
そのため、`product_id` の決定はOCRではなくDB側で行う。

このmilestonesでは、フロントエンド修正を最小限にするため、DB側に `POST /receipts/prepare` を追加し、OCRレスポンスをDB登録に近い形へ変換する。

## 最終的な流れ

```text
OCR API
  -> OCR仮JSON
  -> DB API POST /receipts/prepare
  -> DB側で商品名解決、日付変換、不要項目除去
  -> フロントエンド確認画面
  -> 必要ならユーザーが商品を選択
  -> DB API POST /receipts
```

## 実装順

```text
MILESTONE00  全体方針確認
MILESTONE01  商品名キーとaliasテーブル強化
MILESTONE02  商品名正規化関数とproduct_id解決ロジック
MILESTONE03  POST /receipts/prepare API
MILESTONE04  商品検索APIとalias学習API
MILESTONE05  POST /receiptsとの整合性強化
MILESTONE06  最安店APIとの整合性確認
MILESTONE07  OCR側契約の最小修正
MILESTONE08  結合テストとドキュメント更新
```

## Codexへの渡し方

各stepでは、対象の `MILESTONExx_*.md` を1つずつ渡す。
一度にすべてを実装させない。

作業前に必ず以下を読ませる。

```text
AGENTS.md
README.md
docs/miles/README.md
対象の MILESTONExx_*.md
```

## 共通の非ゴール

以下はこのmilestonesでは実装しない。

```text
認証
ユーザー管理
OCR結果のDB直接保存
画像保存
レシピ提案API
在庫増減APIの仕様変更
外部AI API呼び出し追加
高度な曖昧検索ライブラリの導入
```

## 共通の実行コマンド

DBリポジトリでは原則として以下を実行する。

```bash
uv run python -m compileall app
uv run pytest
```

OCRリポジトリでは、そのリポジトリの `README.md` または `pyproject.toml` に従う。一般形は以下。

```bash
uv run python -m compileall .
uv run pytest
```
