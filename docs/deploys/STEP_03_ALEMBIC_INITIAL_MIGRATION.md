# STEP_03_ALEMBIC_INITIAL_MIGRATION

## 目的

本番DBのスキーマを Alembic で管理できるようにする。

初期migrationを作成し、現在のSQLAlchemyモデルから Render PostgreSQL に必要なテーブルを作れる状態にする。

## Codexへの指示

Alembicを導入する。

## 依存関係の追加

`pyproject.toml` に次を追加する。

```toml
"alembic>=1.13.0",
```

すでに追加済みなら重複させない。

## 作成・修正するファイル

```text
alembic.ini
alembic/env.py
alembic/versions/*.py
```

`alembic/env.py` では、必ず `app.db.session.Base.metadata` を `target_metadata` に設定する。

また、metadataに全モデルが登録されるように、少なくとも次を import する。

```python
from app.receipts import models as receipt_models
from app.inventory import models as inventory_models
```

未使用警告が出る場合は `# noqa: F401` を使ってよい。

## DB URLの扱い

Alembicもアプリ本体と同じ `DATABASE_URL` を使う。

`alembic.ini` に本番URLを直接書かない。

`env.py` で `app.db.session.DATABASE_URL` または同等の正規化済みURLを使う。

## 初期migration

初期migrationは、現在のSQLAlchemyモデルをそのまま反映する。

migration名の例:

```text
initial_schema
```

作成コマンド例:

```bash
uv run alembic revision --autogenerate -m "initial_schema"
```

自動生成後、migrationファイルを必ず読み、次を確認する。

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
inventory_locations
inventory_batches
inventory_operations
inventory_movements
```

## SQLiteテストとの関係

既存テストは SQLite の `Base.metadata.create_all()` でよい。

このSTEPでテストをすべてAlembicに寄せる必要はない。

## PostgreSQL互換性の確認

migration内にSQLite専用の型やSQLが入っていないか確認する。

特に次を確認する。

```text
Boolean
Date
DateTime
Integer
Numeric
String
ForeignKey
UniqueConstraint
CheckConstraint
Index
```

## 実行するコマンド

```bash
uv sync
uv run alembic upgrade head
uv run pytest
```

ローカルSQLiteに migration を当てると既存の `receipts.db` と衝突する可能性がある。
衝突する場合は、検証用に一時DBを使う。

例:

```bash
DATABASE_URL=sqlite:///./tmp_alembic_check.db uv run alembic upgrade head
rm -f tmp_alembic_check.db
```

## 完了条件

```text
Alembicが導入されている
初期migrationがある
DATABASE_URLからmigration先を決められる
本番URLがリポジトリに書かれていない
既存テストが通る
```
