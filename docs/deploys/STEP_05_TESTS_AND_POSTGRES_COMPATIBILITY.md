# STEP_05_TESTS_AND_POSTGRES_COMPATIBILITY

## 目的

Render PostgreSQL対応で既存APIを壊していないことを確認する。

また、DB URL正規化、CORS設定、本番自動create_all無効化がテストで確認できるようにする。

## Codexへの指示

既存テストを壊さずに、必要なテストを追加する。

## 追加するテスト候補

### DB URL正規化

`tests/test_db_session_config.py` などを作成する。

確認すること:

```text
postgres://user:pass@host:5432/db -> postgresql+psycopg://user:pass@host:5432/db
postgresql://user:pass@host:5432/db -> postgresql+psycopg://user:pass@host:5432/db
postgresql+psycopg://user:pass@host:5432/db -> 変化なし
sqlite:///./receipts.db -> 変化なし
```

### CORS設定

`CORS_ALLOW_ORIGINS` のパース関数を作った場合は、その関数をテストする。

確認すること:

```text
未設定時は ["http://localhost:5173"]
カンマ区切りを配列にできる
空白を除去できる
空要素を無視できる
```

### app/main.py の副作用確認

`app.main` の import だけで `Base.metadata.create_all()` が呼ばれない設計になっていることを確認する。

テストしにくい場合は、コードレビューで確認し、テストはDB URLとCORSを優先する。

## PostgreSQL互換性確認

ローカルでPostgreSQLを立てられない場合でも、次を確認する。

```text
SQLite専用 connect_args が PostgreSQL に渡されない
Renderの postgres:// URL を psycopg用URLへ変換する
Numeric型に float を直接保存する処理がないか確認する
idempotency_key の空文字を unique 制約へ直接入れていないか確認する
```

既存コードに問題が見つかった場合は、最小変更で修正する。

## テスト環境の注意

`tests/conftest.py` はテスト用SQLiteを使い続けてよい。

ただし、アプリ本体の `DATABASE_URL` がテストに干渉しないようにする。

必要なら `monkeypatch` を使って環境変数を制御する。

## 実行するコマンド

```bash
uv run pytest
```

可能なら次も実行する。

```bash
DATABASE_URL=sqlite:///./tmp_alembic_check.db uv run alembic upgrade head
rm -f tmp_alembic_check.db
```

## 完了条件

```text
既存APIテストが通る
DB URL正規化のテストがある
CORS設定のテストがある
PostgreSQL接続時にSQLite専用設定が混入しない
全テストが通る
```
