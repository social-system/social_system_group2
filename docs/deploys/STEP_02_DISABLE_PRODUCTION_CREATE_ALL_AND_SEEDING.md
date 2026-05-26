# STEP_02_DISABLE_PRODUCTION_CREATE_ALL_AND_SEEDING

## 目的

本番起動時に `Base.metadata.create_all()` で自動的にテーブル作成する挙動を削除する。

本番のスキーマ管理は Alembic に移す。

## Codexへの指示

`app/main.py` を修正する。

現在のように FastAPI アプリの import 時または起動時に次を実行してはいけない。

```python
Base.metadata.create_all(bind=engine)
```

本番ではテーブル作成を Alembic に任せる。

## seed処理の扱い

現在、`seed_inventory_locations(db)` が `app/main.py` の起動時に実行されている。

この処理は、在庫保管場所の最小マスタを入れるために必要な可能性がある。ただし、本番起動時にテーブルが未作成だと失敗する。

次の方針に変更する。

```text
app/main.py ではDBスキーマ作成を行わない
seed処理は独立したスクリプトに移す
Renderの起動スクリプトで alembic upgrade head の後に seed を実行する
seed は何度実行しても重複しないようにする
```

## 作成するファイル案

次のようなスクリプトを作成する。

```text
scripts/seed_master_data.py
```

役割:

```text
SessionLocal を開く
seed_inventory_locations(db) を呼ぶ
commit する
例外時は rollback する
finally で close する
```

`seed_inventory_locations` が既に冪等ならそのまま使う。
冪等でない場合は、重複作成しないように修正する。

## app/main.py の方針

`app/main.py` は次だけを行う。

```text
FastAPI app作成
CORS設定
router登録
health check定義
```

モデル import は、SQLAlchemy relationship や Alembic の都合で必要な範囲に留める。
未使用 import は削除する。

## APP_ENV の扱い

`APP_ENV=test` のときだけ特別に `create_all()` を実行する、という実装にはしない。

テストでは `tests/conftest.py` 側で `Base.metadata.create_all(bind=test_engine)` を実行しているため、アプリ本体でテスト用処理を持つ必要はない。

## 実行するコマンド

```bash
uv run pytest
```

## 完了条件

```text
app/main.py から Base.metadata.create_all() が消えている
app/main.py から本番起動時のDB書き込みが消えている
seed処理が独立スクリプト化されている
既存テストが通る
```
