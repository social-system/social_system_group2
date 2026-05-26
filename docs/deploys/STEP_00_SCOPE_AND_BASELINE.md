# STEP_00_SCOPE_AND_BASELINE

## 目的

Render + Render PostgreSQL にデプロイするための前提確認を行い、既存実装の動作を壊さない基準点を作る。

このSTEPでは、原則として大きな実装変更は行わない。

## Codexへの指示

あなたはこのリポジトリのデプロイ対応を行う。

今回の対象は Render + Render PostgreSQL である。Supabase対応は行わない。

まず以下のファイルを読む。

```text
AGENTS.md
README.md
docs/DATABASE_DESIGN.md
docs/INVENTORY_IMPLEMENTATION_SPEC.md
docs/API_SPEC.md
docs/OCR_DB_INTERFACE.md
pyproject.toml
app/db/session.py
app/main.py
tests/conftest.py
```

## 現状確認

以下を確認する。

```text
現在のDB接続が SQLite 固定になっているか
app/main.py で Base.metadata.create_all() を実行しているか
CORS が localhost 固定になっているか
pyproject.toml に PostgreSQL ドライバと Alembic がないか
テストが SQLite を前提にしているか
```

## 実行するコマンド

まず依存関係を同期し、テストを実行する。

```bash
uv sync
uv run pytest
```

`uv` が使えない場合は次を使う。

```bash
python -m pip install -e .
python -m pip install pytest
python -m pytest
```

## 変更してよいもの

このSTEPでは、必要最小限のドキュメント追記またはメモ作成だけ許可する。

例:

```text
docs/deploys/BASELINE_NOTES.md
```

ただし、以降のSTEPで不要なら作成しなくてよい。

## 変更してはいけないもの

```text
APIレスポンス形式
DBモデル
DBスキーマ
ルーティング
OCR連携仕様
在庫ロジック
```

## 完了条件

```text
現状のテスト結果を把握している
以降の修正対象を把握している
SupabaseではなくRender PostgreSQL前提で進めることを確認している
```
