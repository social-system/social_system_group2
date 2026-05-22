# MILESTONE01: 商品名キーとaliasテーブル強化

## Codex指示

```text
AGENTS.md、README.md、docs/miles/README.md、docs/miles/MILESTONE01_PRODUCT_KEYS_AND_ALIASES.md を読んでください。
このmileでは、DB側の商品名表記揺れを吸収するため、products と product_aliases のテーブル定義を強化してください。
POST /receipts/prepare はまだ実装しないでください。
```

## 目的

OCRの `normalized_name` が揺れても、DB側で `product_id` に解決できるようにする。

## 実装対象

DBリポジトリのみを変更する。
OCRリポジトリは変更しない。

## 追加・変更する設計

### products

`products` に `name_key` を追加する。

```text
name: ユーザー表示用の商品名
name_key: 検索・照合用に正規化したキー
```

例:

```text
name = 卵
name_key = 卵
```

既存の `products` がある場合は、現在の設計を壊さずに `name_key` を追加する。
`name_key` は unique にする。

### product_aliases

`product_aliases` を以下の意味で使う。

```text
alias_name: OCRやユーザー入力で出現した商品名
alias_key: alias_name を正規化した照合用キー
product_id: 紐づく正式商品
source: alias が作られた理由
is_active: 無効化用
```

推奨カラム:

```text
id
product_id
alias_name
alias_key
source
is_active
created_at
updated_at
```

`alias_key` は unique にする。

`source` の初期候補:

```text
manual
seed
user_confirmed
ocr
```

MVPでは文字列でよい。enumテーブルは不要。

## SQLAlchemyモデル例

既存コードの書き方に合わせて調整してよい。

```python
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    default_base_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    default_category_id: Mapped[int | None] = mapped_column(ForeignKey("accounting_categories.id"), nullable=True)
    is_inventory_target: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

```python
class ProductAlias(Base):
    __tablename__ = "product_aliases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    alias_name: Mapped[str] = mapped_column(String(255), nullable=False)
    alias_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

## 既存データへの対応

migration管理がある場合はmigrationを追加する。

migration管理がない場合は、モデルとテストDB作成処理を更新する。
実データが入っている開発用DBを勝手に削除しない。

既存の `products.name` から `name_key` を作る必要がある場合は、次mileで作る `normalize_product_key()` を使う想定でよい。
このmileでは空のDBまたはテストDBで動く状態を優先する。

## テスト

最低限、以下を追加または更新する。

```text
Product を name_key 付きで作成できる
Product.name_key が unique である
ProductAlias を alias_key 付きで作成できる
ProductAlias.alias_key が unique である
ProductAlias が Product に紐づく
```

## 非ゴール

このmileでは以下を実装しない。

```text
normalize_product_key()
resolve_product()
POST /receipts/prepare
GET /products/search
POST /product-aliases
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
追加・変更したカラム:
追加・更新したテスト:
実行したコマンド:
テスト結果:
残TODO:
```
