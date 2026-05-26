# STEP_06_README_DEPLOYMENT_DOCS

## 目的

READMEに Render + Render PostgreSQL へのデプロイ手順を追加する。

Codex実装後、チームメンバーが同じ手順でデプロイできる状態にする。

## Codexへの指示

`README.md` に「Render デプロイ」セクションを追加する。

既存の説明を壊さず、末尾付近に追加する。

## READMEに書く内容

最低限、次を含める。

```text
構成
必要な環境変数
Render PostgreSQL作成手順
Render Web Service作成手順
build command
start command
migrationの流れ
CORS設定
疎通確認
よくある失敗
```

## 構成説明

次のように明記する。

```text
API: Render Web Service
DB: Render PostgreSQL
DB接続: Render PostgreSQL の Internal Database URL
Schema管理: Alembic
```

## 環境変数

表形式で書く。

```text
DATABASE_URL          Render PostgreSQLの接続URL
APP_ENV               production
CORS_ALLOW_ORIGINS    フロントエンドURL。カンマ区切り可
PORT                  Renderが自動設定するため通常は手動設定不要
```

## Render設定例

READMEに次を明記する。

```text
Build Command: pip install -e .
Start Command: bash scripts/start_render.sh
```

## 手順

手動デプロイの場合の流れを書く。

```text
1. RenderでPostgreSQLを作成する
2. RenderでWeb Serviceを作成する
3. GitHubリポジトリを接続する
4. Build Commandを設定する
5. Start Commandを設定する
6. 環境変数を設定する
7. Deployする
8. / と /docs を確認する
```

## 疎通確認

次の確認をREADMEに書く。

```bash
curl https://YOUR_RENDER_SERVICE.onrender.com/
```

期待値:

```json
{"status":"ok"}
```

## よくある失敗

以下を書く。

```text
DATABASE_URL が未設定でSQLiteに接続してしまう
CORS_ALLOW_ORIGINS にフロントエンドURLが入っていない
alembic upgrade head が失敗してテーブルがない
RenderのStart Commandが uvicorn app.main:app になっておらず起動しない
秘密情報をREADMEに直接書いてしまう
```

## 注意点

READMEに実際のDBパスワードや接続URLを書かない。

## 実行するコマンド

```bash
uv run pytest
```

## 完了条件

```text
READMEにRenderデプロイ手順がある
Build CommandとStart Commandが明記されている
環境変数の説明がある
migrationの説明がある
秘密情報が含まれていない
```
