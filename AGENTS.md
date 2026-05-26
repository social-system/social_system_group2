# AGENTS.md

## 目的

このリポジトリは、ユーザー確認済みのレシート購入履歴、商品マスタ、価格比較、在庫情報を扱う FastAPI バックエンドである。

今回の作業目的は、既存の開発用 SQLite 前提の実装を、Render + Render PostgreSQL に安全にデプロイできる構成へ変更することである。

Supabase は今回の対象外とする。DB は Render PostgreSQL、API 実行環境は Render Web Service を前提にする。

## 最重要方針

本番では `Base.metadata.create_all()` による自動テーブル作成を行わない。

```text
開発・テスト: SQLite を利用してよい
本番: Render PostgreSQL + Alembic migration でスキーマ管理する
```

本番DBのスキーマ変更は必ず Alembic migration で行う。

## 作業順序

Codex は、以下の順番で `docs/deploys/STEP_XX.md` を実行する。

```text
docs/deploys/STEP_00_SCOPE_AND_BASELINE.md
docs/deploys/STEP_01_RUNTIME_CONFIG_AND_DATABASE_URL.md
docs/deploys/STEP_02_DISABLE_PRODUCTION_CREATE_ALL_AND_SEEDING.md
docs/deploys/STEP_03_ALEMBIC_INITIAL_MIGRATION.md
docs/deploys/STEP_04_RENDER_DEPLOYMENT_FILES.md
docs/deploys/STEP_05_TESTS_AND_POSTGRES_COMPATIBILITY.md
docs/deploys/STEP_06_README_DEPLOYMENT_DOCS.md
docs/deploys/STEP_07_FINAL_VERIFICATION.md
```

各STEPは独立して読めるように書いてあるが、順番を飛ばさない。

## 作業前に必ず読む文書

```text
AGENTS.md
README.md
docs/DATABASE_DESIGN.md
docs/INVENTORY_IMPLEMENTATION_SPEC.md
docs/API_SPEC.md
docs/OCR_DB_INTERFACE.md
対象STEPの docs/deploys/STEP_XX.md
```

仕様に矛盾がある場合の優先順位は次の通り。

```text
対象STEPの docs/deploys/STEP_XX.md
AGENTS.md
docs/DATABASE_DESIGN.md
docs/INVENTORY_IMPLEMENTATION_SPEC.md
docs/API_SPEC.md
README.md
既存コード
```

## 実装対象

```text
DATABASE_URL によるDB接続切替
Render PostgreSQL 接続対応
PostgreSQLドライバ追加
Alembic導入
初期migration作成
本番起動時の create_all 無効化
本番起動用スクリプト作成
Render用設定ファイル作成
CORS許可オリジンの環境変数化
Render向けREADME更新
テスト更新
```

## 実装しないもの

```text
Supabase対応
OCR API
画像アップロード
画像保存
レシピ提案 API
認証
ユーザー管理
世帯管理
既存API仕様の大幅変更
既存テーブル設計の作り直し
本番データの初期投入用ダミーデータ追加
秘密情報のコミット
```

## 秘密情報の扱い

`.env` や秘密鍵を作成してコミットしてはいけない。

以下はリポジトリに含めてはいけない。

```text
Render の実際の DATABASE_URL
DBユーザー名
DBパスワード
APIキー
秘密鍵
個人のメールアドレスやトークン
```

ドキュメントには例としてのみ、次のようなプレースホルダーを使う。

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB_NAME
CORS_ALLOW_ORIGINS=https://your-frontend.example.com
```

## DB接続方針

`DATABASE_URL` が設定されていない場合は、開発用として SQLite を使ってよい。

```text
未設定: sqlite:///./receipts.db
本番: Render PostgreSQL の Internal Database URL
```

Render の接続文字列が `postgres://` で始まる場合は、SQLAlchemy + psycopg で扱えるように `postgresql+psycopg://` へ正規化する。

SQLite のときだけ `connect_args={"check_same_thread": False}` を使う。

PostgreSQL のときは `connect_args` に SQLite 専用設定を渡さない。

## 本番起動方針

Render Web Service では、起動時に次を順番に行う。

```text
alembic upgrade head
必要最小限のマスタデータ seed
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

ただし、アプリケーションコードの import 時や FastAPI 起動時に `Base.metadata.create_all()` を実行してはいけない。

## CORS方針

開発環境では `http://localhost:5173` を許可する。

本番では `CORS_ALLOW_ORIGINS` にカンマ区切りで指定されたURLだけを許可する。

`*` を安易に許可してはいけない。資格情報付きCORSと `*` を組み合わせてはいけない。

## テスト方針

テストでは通常開発用の `receipts.db` を使わない。

テストは SQLite in-memory または一時SQLiteでよい。

テストでは Alembic migration の完全検証より、既存APIの回帰、DB接続設定、CORS設定、本番で `create_all()` が自動実行されないことを重視する。

## 変更後に必ず実行する確認

```bash
uv sync
uv run pytest
```

`uv` が使えない環境では次を実行する。

```bash
python -m pip install -e .
python -m pip install pytest
python -m pytest
```

## 完了条件

```text
全テストが成功する
アプリがローカルSQLiteで起動する
DATABASE_URL指定時にPostgreSQL用URLを読める
本番起動時にAlembic migrationを流せる
Render用の設定と手順がREADMEにある
秘密情報がリポジトリに含まれていない
```
