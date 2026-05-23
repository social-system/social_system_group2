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
MILESTONE00  全体方針確認                              done
MILESTONE01  商品名キーとaliasテーブル強化              done
MILESTONE02  商品名正規化関数とproduct_id解決ロジック   done
MILESTONE03  POST /receipts/prepare API                 done
MILESTONE04  商品検索APIとalias学習API                  done
MILESTONE05  POST /receiptsとの整合性強化               done
MILESTONE06  最安店APIとの整合性確認                    done
MILESTONE07  OCR側契約の最小修正                        done
MILESTONE08  結合テストとドキュメント更新               done
```

## MILESTONE08 完了メモ

DB リポジトリ側で、OCR 風 JSON から `POST /receipts/prepare`、`POST /receipts`、`GET /prices/cheapest` までの結合テストを追加した。

確認済みの流れ:

```text
OCR は product_id / category_id を決めない
DB の prepare API が product_aliases / products を使って product_id を解決する
product_aliases が OCR 名の表記揺れを吸収する
prepare 結果の receipt を POST /receipts に渡して保存できる
最安店表示は product_id と line_total / base_quantity を使う
product_id 未解決の商品は最安店検索対象にならない
```

`normalized_name` は OCR 候補であり、DB 正式名とは限らない。`product_id` が解決できた場合、prepare 結果では DB 正式名である `products.name` に寄せる。

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
