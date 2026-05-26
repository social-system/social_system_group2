# STEP_04_RENDER_DEPLOYMENT_FILES

## 目的

Render Web Service + Render PostgreSQL で動かすための起動ファイルと設定ファイルを追加する。

## Codexへの指示

Render用に次を作成する。

```text
scripts/start_render.sh
render.yaml
```

`render.yaml` を使わず、Renderダッシュボードで手動設定する運用も可能だが、リポジトリには設定例として `render.yaml` を置く。

## scripts/start_render.sh

起動スクリプトは次の順番で実行する。

```text
alembic upgrade head
python -m scripts.seed_master_data
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

例:

```bash
#!/usr/bin/env bash
set -euo pipefail

alembic upgrade head
python -m scripts.seed_master_data
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

`exec` を使って、uvicorn がメインプロセスになるようにする。

## scripts パッケージ化

`python -m scripts.seed_master_data` で実行できるように、必要なら次を作成する。

```text
scripts/__init__.py
```

## render.yaml

Render Blueprintの例を作成する。

最低限、次を含める。

```text
PostgreSQL database
FastAPI web service
DATABASE_URL
APP_ENV=production
CORS_ALLOW_ORIGINS
buildCommand
startCommand
```

`DATABASE_URL` はRender PostgreSQLの内部接続URLを参照する形にする。

例の方向性:

```yaml
databases:
  - name: receipt-db
    databaseName: receipt_db
    user: receipt_user

services:
  - type: web
    name: receipt-api
    runtime: python
    buildCommand: pip install -e .
    startCommand: bash scripts/start_render.sh
    envVars:
      - key: APP_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: receipt-db
          property: connectionString
      - key: CORS_ALLOW_ORIGINS
        value: https://your-frontend.example.com
```

実際のRender仕様で `runtime` が使えない場合は、Renderの現在のBlueprint仕様に合わせて `env: python` に修正する。

## Pythonバージョン

`.python-version` がある場合は、Python 3.12系であることを確認する。

Render側に明示が必要な場合は、`PYTHON_VERSION` 環境変数を `3.12` 系にする。

## 注意点

`render.yaml` には実際の秘密情報を書かない。

`CORS_ALLOW_ORIGINS` は仮値でよい。READMEで実際のフロントエンドURLに差し替えるよう説明する。

## 実行するコマンド

ローカルで起動スクリプトを検証する場合は、一時SQLiteを使う。

```bash
DATABASE_URL=sqlite:///./tmp_render_start_check.db PORT=8000 bash scripts/start_render.sh
```

このコマンドはサーバーが起動し続ける。確認後に停止する。

通常のテストは次でよい。

```bash
uv run pytest
```

## 完了条件

```text
scripts/start_render.sh がある
scripts/seed_master_data.py が起動スクリプトから呼べる
render.yaml がある
buildCommand と startCommand が明記されている
DATABASE_URL が Render database から渡される設定例になっている
秘密情報が含まれていない
```
