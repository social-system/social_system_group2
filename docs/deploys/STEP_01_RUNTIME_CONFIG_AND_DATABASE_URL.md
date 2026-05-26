# STEP_01_RUNTIME_CONFIG_AND_DATABASE_URL

## 目的

SQLite固定のDB接続をやめ、環境変数 `DATABASE_URL` によって接続先を切り替えられるようにする。

開発環境ではこれまで通り SQLite を使えるようにする。本番では Render PostgreSQL を使う。

## Codexへの指示

`app/db/session.py` を中心に修正する。

次の方針を守る。

```text
DATABASE_URL 未設定時は sqlite:///./receipts.db を使う
DATABASE_URL 設定時はその値を使う
postgres:// で始まるURLは postgresql+psycopg:// に変換する
postgresql:// で始まるURLは postgresql+psycopg:// に変換する
postgresql+psycopg:// はそのまま使う
SQLite のときだけ connect_args={"check_same_thread": False} を渡す
PostgreSQL のときは connect_args を渡さない
pool_pre_ping=True を設定する
```

## 依存関係の追加

`pyproject.toml` に次を追加する。

```toml
"psycopg[binary]>=3.2.0",
```

可能なら Alembic は STEP_03 で追加する。ただし、このSTEPで一緒に追加してもよい。

## 実装案

`app/db/session.py` に、DB URLを正規化する小さな関数を作る。

例:

```python
DEFAULT_DATABASE_URL = "sqlite:///./receipts.db"


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url
```

`create_engine()` は、SQLite と PostgreSQL で引数を分ける。

## CORS設定の準備

可能なら、このSTEPで `app/main.py` のCORS設定も環境変数化する。

方針:

```text
CORS_ALLOW_ORIGINS 未設定時は http://localhost:5173
CORS_ALLOW_ORIGINS はカンマ区切り
空白は削除
空要素は無視
```

例:

```text
CORS_ALLOW_ORIGINS=https://frontend.example.com,https://another.example.com
```

## テスト追加

可能なら以下の単体テストを追加する。

```text
postgres:// が postgresql+psycopg:// に変換される
postgresql:// が postgresql+psycopg:// に変換される
sqlite:///./receipts.db は変換されない
CORS_ALLOW_ORIGINS がカンマ区切りで配列化される
```

テストしにくい場合は、STEP_05でまとめて追加する。

## 注意点

実際の Render PostgreSQL の `DATABASE_URL` をコードやテストに書かない。

テストではダミーURLだけ使う。

## 実行するコマンド

```bash
uv sync
uv run pytest
```

## 完了条件

```text
app/db/session.py が DATABASE_URL を読む
開発時は DATABASE_URL なしでも SQLite で動く
Render PostgreSQL の postgres:// URL を psycopg 用に正規化できる
既存テストが通る
```
