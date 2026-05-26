# DATABASE_DESIGN.md

## 目的

この DB は、レシート OCR の生データを保存するためのものではない。

目的は、ユーザーが確認した購入履歴を保存し、家計簿、在庫管理、AI レシピ提案が共通で使える形にすることである。

```text
OCR 結果 = 仮データ
DB 登録データ = ユーザー確認済みデータ
```

## 非ゴール

現段階では以下を実装しない。

- 認証
- ユーザー管理
- 世帯管理
- `user_id` によるデータ分離
- OCR 実行
- レシート画像保存
- OCR の中間出力保存
- 外部サービス連携

本番デプロイ構成はこの設計書では定義しない。Render + Render PostgreSQL へのデプロイ方針と migration 管理は `docs/deploys/` を参照する。

## 全体の考え方

レシート明細は、レシートに書かれた内容を保存するだけでは不十分である。

在庫管理やレシピ提案では、同じ商品を同じ単位で扱う必要がある。

そのため、DB では次の 2 種類の情報を分けて保存する。

```text
購入時の情報       レシートに書かれていた情報
アプリ内の共通情報 在庫管理・レシピ提案で使う情報
```

例:

```json
{
  "raw_name": "卵 1パック",
  "normalized_name": "卵",
  "purchased_quantity": 1,
  "purchased_unit": "パック",
  "base_quantity": 10,
  "base_unit": "個"
}
```

別のレシートで `卵 6個` が登録されても、在庫では `卵 16個` として集計できる。

## テーブル一覧

```text
receipts
receipt_items
accounting_categories
products
product_aliases
product_unit_conversions
receipt_prepare_metrics
receipt_prepare_unresolved_names
product_alias_conflict_events
```

## ER 概要

```text
receipts 1 --- * receipt_items

accounting_categories 1 --- * receipt_items
accounting_categories 1 --- * products

products 1 --- * receipt_items
products 1 --- * product_aliases
products 1 --- * product_unit_conversions
```

`receipt_items.product_id` は MVP では nullable とする。

理由は、OCR・フロント確認時点で商品マスタに未登録の商品が出るためである。ただし、在庫管理やレシピ提案を安定させるには、将来的に `product_id` を埋める運用が望ましい。

## receipts

レシート全体を表す。

| カラム | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | Integer | yes | 主キー |
| `purchased_at` | Date | yes | 購入日 |
| `store_name` | String(255) | no | 店舗名 |
| `total_amount` | Integer | yes | レシートの最終支払額 |
| `items_total` | Integer | yes | 明細行合計。サーバー側で計算 |
| `adjustment_amount` | Integer | yes | `total_amount - items_total` |
| `source` | String(50) | yes | 登録元。既定値は `manual_confirmed` |
| `created_at` | DateTime | yes | 作成日時 |
| `updated_at` | DateTime | yes | 更新日時 |

### 注意点

`total_amount == items_total` を必須にしない。

実レシートでは、割引、ポイント、税、レジ袋、OCR 漏れなどにより、明細行合計と最終支払額が一致しないことがある。

差額は `adjustment_amount` に保存する。

## receipt_items

レシート明細を表す。

| カラム | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | Integer | yes | 主キー |
| `receipt_id` | Integer | yes | `receipts.id` |
| `product_id` | Integer | no | `products.id` |
| `category_id` | Integer | no | `accounting_categories.id` |
| `raw_name` | String(255) | yes | レシート上の商品名 |
| `normalized_name` | String(255) | no | アプリ内で扱う商品名 |
| `purchased_quantity` | Numeric(10, 2) | yes | 購入時の数量 |
| `purchased_unit` | String(50) | no | 購入時の単位 |
| `base_quantity` | Numeric(10, 2) | no | 共通単位に変換した数量 |
| `base_unit` | String(50) | no | 共通単位 |
| `unit_price` | Integer | no | 単価 |
| `line_total` | Integer | yes | 明細行合計 |
| `is_inventory_target` | Boolean | yes | 在庫管理対象かどうか |
| `created_at` | DateTime | yes | 作成日時 |
| `updated_at` | DateTime | yes | 更新日時 |

### purchased と base の違い

`purchased_quantity` と `purchased_unit` は、購入時の表記を残す。

`base_quantity` と `base_unit` は、在庫管理とレシピ提案で使う共通単位である。

| raw_name | purchased_quantity | purchased_unit | base_quantity | base_unit |
| --- | ---: | --- | ---: | --- |
| 卵 1パック | 1 | パック | 10 | 個 |
| 卵 6個 | 6 | 個 | 6 | 個 |
| 牛乳 1本 | 1 | 本 | 1000 | ml |
| 米 5kg | 5 | kg | 5000 | g |

### 在庫対象の場合のルール

`is_inventory_target = true` の場合、次を必須にする。

```text
normalized_name
base_quantity
base_unit
```

理由は、在庫管理側がこの 3 項目を使って数量を集計するためである。

`product_id` は MVP では必須にしない。ただし、商品マスタが整ってきたら必須に近づける。

## accounting_categories

家計簿集計用のカテゴリを表す。

| カラム | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | Integer | yes | 主キー |
| `name` | String(100) | yes | カテゴリ名。unique |
| `sort_order` | Integer | yes | 表示順 |
| `created_at` | DateTime | yes | 作成日時 |
| `updated_at` | DateTime | yes | 更新日時 |

初期カテゴリ例:

```text
食費
日用品
外食
飲料
調味料
その他
```

## products

アプリ内で扱う商品マスタを表す。

| カラム | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | Integer | yes | 主キー |
| `name` | String(255) | yes | 正規化後の商品名。unique |
| `name_key` | String(255) | yes | 検索・照合用に正規化した商品名。unique |
| `default_base_unit` | String(50) | yes | 在庫・レシピで使う標準単位 |
| `default_category_id` | Integer | no | 既定カテゴリ |
| `is_inventory_target` | Boolean | yes | 通常在庫対象かどうか |
| `created_at` | DateTime | yes | 作成日時 |
| `updated_at` | DateTime | yes | 更新日時 |

例:

| name | name_key | default_base_unit | is_inventory_target |
| --- | --- | --- | --- |
| 卵 | 卵 | 個 | true |
| 牛乳 | 牛乳 | ml | true |
| 米 | 米 | g | true |
| 洗剤 | 洗剤 | 個 | false |

## product_aliases

レシート上の商品名と商品マスタを対応させる。

| カラム | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | Integer | yes | 主キー |
| `product_id` | Integer | yes | `products.id` |
| `alias_name` | String(255) | yes | OCR やユーザー入力で出現した商品名 |
| `alias_key` | String(255) | yes | 検索・照合用に正規化した別名。unique |
| `source` | String(50) | yes | alias が作られた理由。許可値は `user_confirmed`, `seed`, `admin`, `ocr_suggested` |
| `is_active` | Boolean | yes | 無効化用フラグ |
| `created_at` | DateTime | yes | 作成日時 |
| `updated_at` | DateTime | yes | 更新日時 |

### source の運用ルール

| source | 意味 | 自動解決 | 候補検索 |
| --- | --- | --- | --- |
| `user_confirmed` | ユーザーが確認画面で選択したalias | 可 | 可 |
| `seed` | 初期データ・テストデータとして安全に登録したalias | 可 | 可 |
| `admin` | 管理者が確認して登録したalias | 可 | 可 |
| `ocr_suggested` | OCRやAIが候補として推定しただけのalias | 不可 | 可 |

`POST /receipts/prepare` の自動解決では、`alias_key` が完全一致し、`is_active = true` で、`source` が `user_confirmed`, `seed`, `admin` の alias だけを使う。

`ocr_suggested` は候補検索にだけ使い、自動で `resolved` にしない。`is_active = false` の alias は、自動解決にも候補検索にも使わない。

例:

| alias_name | alias_key | source | product |
| --- | --- | --- | --- |
| タマゴM 10コ | たまごm10こ | user_confirmed | 卵 |
| 白たまご | 白たまご | seed | 卵 |
| 牛乳1000ml | 牛乳1000ml | admin | 牛乳 |
| OCR候補名 | ocr候補名 | ocr_suggested | 候補検索のみ |

## product_unit_conversions

商品ごとの単位変換を表す。

| カラム | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | Integer | yes | 主キー |
| `product_id` | Integer | yes | `products.id` |
| `from_unit` | String(50) | yes | 変換前単位 |
| `to_unit` | String(50) | yes | 変換後単位 |
| `multiplier` | Numeric(10, 3) | yes | 変換倍率 |
| `created_at` | DateTime | yes | 作成日時 |
| `updated_at` | DateTime | yes | 更新日時 |

unique 制約:

```text
product_id, from_unit, to_unit
```

例:

| product | from_unit | to_unit | multiplier |
| --- | --- | --- | ---: |
| 卵 | パック | 個 | 10 |
| 牛乳 | 本 | ml | 1000 |
| 米 | kg | g | 1000 |

### 重要な注意

`パック -> 個` や `本 -> ml` の変換は、商品ごとに違う。

そのため、単位だけで変換してはいけない。

誤り:

```text
パック = 10個
```

正しい考え方:

```text
卵 1パック = 10個
納豆 1パック = 3個
ヨーグルト 1パック = 400g
```

## receipt_prepare_metrics

`POST /receipts/prepare` の運用指標を集約して保存する。

このテーブルはレシート保存ではない。OCR 生 JSON、価格、店舗名、購入日、全明細は保存せず、効果測定に必要な件数だけを保存する。

| カラム | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | Integer | yes | 主キー |
| `prepare_count` | Integer | yes | `POST /receipts/prepare` 実行回数 |
| `total_item_count` | Integer | yes | prepare で処理した明細数 |
| `unresolved_item_count` | Integer | yes | `product_id` が解決できなかった明細数 |
| `inventory_base_quantity_missing_count` | Integer | yes | 在庫対象で `base_quantity` が空の明細数 |
| `created_at` | DateTime | yes | 作成日時 |
| `updated_at` | DateTime | yes | 更新日時 |

## receipt_prepare_unresolved_names

`POST /receipts/prepare` で未解決だった `raw_name` を、正規化キー単位で集約する。

| カラム | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | Integer | yes | 主キー |
| `raw_name` | String(255) | yes | 未解決だった商品名の代表値 |
| `raw_name_key` | String(255) | yes | 正規化したキー。unique |
| `count` | Integer | yes | 出現回数 |
| `last_seen_at` | DateTime | yes | 最終出現日時 |

保存対象は未解決明細の `raw_name` だけであり、解決済み明細やレシート全体は保存しない。

## product_alias_conflict_events

alias 登録時に衝突した組み合わせを集約する。

| カラム | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | Integer | yes | 主キー |
| `alias_key` | String(255) | yes | 衝突した alias key |
| `requested_product_id` | Integer | yes | 登録しようとした商品 ID |
| `existing_product_id` | Integer | yes | 既に紐づいていた商品 ID |
| `count` | Integer | yes | 衝突回数 |
| `last_seen_at` | DateTime | yes | 最終発生日時 |

unique 制約:

```text
alias_key, requested_product_id, existing_product_id
```

## SQLAlchemy モデル例

実装時は既存の命名規則に合わせてよいが、意味は以下に合わせる。

```python
class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    purchased_at: Mapped[date] = mapped_column(Date, nullable=False)
    store_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    items_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    adjustment_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual_confirmed")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    items: Mapped[list["ReceiptItem"]] = relationship(
        back_populates="receipt",
        cascade="all, delete-orphan",
    )
```

```python
class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipts.id"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("accounting_categories.id"), nullable=True)
    raw_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    purchased_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    purchased_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    base_quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    base_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unit_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_total: Mapped[int] = mapped_column(Integer, nullable=False)
    is_inventory_target: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    receipt: Mapped["Receipt"] = relationship(back_populates="items")
```

## 旧カラムから新カラムへの対応

既存コードを修正する際の対応表は以下。

| 旧 | 新 |
| --- | --- |
| `receipt_total` | `total_amount` |
| `item` | `raw_name` |
| `num` | `purchased_quantity` |
| `amount` | `unit_price` |
| `total` | `line_total` |
| `date` | `receipts.purchased_at` |
| `ingredients` | `is_inventory_target` |

## 登録時の計算

`POST /receipts` では、サーバー側で次を計算する。

```text
items_total = sum(line_total)
adjustment_amount = total_amount - items_total
```

フロントエンドから `items_total` と `adjustment_amount` が送られてきても信用しない。

## 登録時のバリデーション

| 条件 | 結果 |
| --- | --- |
| `items` が空 | 422 |
| `purchased_at` が実在しない日付でない | 422 |
| `total_amount < 0` | 422 |
| `raw_name` が空 | 422 |
| `purchased_quantity <= 0` | 422 |
| `line_total < 0` | 422 |
| `is_inventory_target = true` かつ `normalized_name` が空 | 422 |
| `is_inventory_target = true` かつ `base_quantity` が空 | 422 |
| `is_inventory_target = true` かつ `base_unit` が空 | 422 |
| `product_id` が存在しない | 400 |
| `category_id` が存在しない | 400 |

## 削除

レシートを削除した場合、関連する `receipt_items` も削除する。

`products`、`product_aliases`、`product_unit_conversions`、`accounting_categories` は削除しない。

## 初期データ

MVP では、カテゴリと代表的な商品だけを seed してよい。

カテゴリ例:

```text
食費
日用品
外食
飲料
調味料
その他
```

商品例:

```text
卵: 個
牛乳: ml
米: g
玉ねぎ: 個
じゃがいも: 個
にんじん: 本
```

ただし、seed がなくても API が動くようにする。

## 今後追加してよいもの

以下は今回の実装範囲外だが、後から追加してよい。

- OCR 仮データ保存用の `receipt_ocr_drafts`
- レシート更新 API
- 月別・カテゴリ別集計 API
- 在庫テーブル
- レシピ提案用の食材使用履歴
- 認証とユーザー管理
