# BASELINE_NOTES

## STEP_00_SCOPE_AND_BASELINE

- 現在のDB接続は `app/db/session.py` で `sqlite:///./receipts.db` に固定されている。
- `app/main.py` は `APP_ENV != "test"` のとき `Base.metadata.create_all(bind=engine)` を実行し、その後 `seed_inventory_locations()` を実行している。
- CORS許可オリジンは `app/main.py` で `http://localhost:5173` に固定されている。
- `pyproject.toml` には `psycopg` などのPostgreSQLドライバと `alembic` はまだない。
- テストは `tests/conftest.py` で `sqlite://` + `StaticPool` のSQLite in-memory DBを使い、fixture内で `Base.metadata.create_all()` / `drop_all()` を実行している。

次STEPでは、`DATABASE_URL` による接続先切替、PostgreSQL URL正規化、SQLite専用 `connect_args` の分岐、CORS許可オリジンの環境変数化を行う。
