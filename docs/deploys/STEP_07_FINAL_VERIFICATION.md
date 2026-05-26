# STEP_07_FINAL_VERIFICATION

## 目的

Render + Render PostgreSQL 対応が完了しているかを最終確認する。

このSTEPでは、不要ファイル、秘密情報、テスト失敗、ドキュメント不足を検出して修正する。

## Codexへの指示

以下を順番に確認する。

## 1. 変更内容の確認

```bash
git diff --stat
git diff
```

意図しない変更がないか確認する。

特に次が変更されていないか確認する。

```text
APIレスポンス形式
既存エンドポイントのパス
OCR連携仕様
在庫ロジックの業務ルール
```

## 2. 秘密情報の確認

次の文字列を検索する。

```bash
grep -R "postgresql://" -n . --exclude-dir=.git --exclude-dir=.venv || true
grep -R "postgres://" -n . --exclude-dir=.git --exclude-dir=.venv || true
grep -R "PASSWORD" -n . --exclude-dir=.git --exclude-dir=.venv || true
grep -R "DATABASE_URL=" -n . --exclude-dir=.git --exclude-dir=.venv || true
```

READMEやテストにプレースホルダーが出るのはよい。

実際の接続URL、ユーザー名、パスワード、トークンが含まれていたら削除する。

## 3. テスト

```bash
uv sync
uv run pytest
```

`uv` が使えない場合:

```bash
python -m pip install -e .
python -m pip install pytest
python -m pytest
```

## 4. Alembic検証

一時SQLite DBにmigrationを流す。

```bash
rm -f tmp_alembic_check.db
DATABASE_URL=sqlite:///./tmp_alembic_check.db uv run alembic upgrade head
rm -f tmp_alembic_check.db
```

## 5. ローカル起動確認

```bash
uv run uvicorn app.main:app --reload
```

別ターミナルで確認する。

```bash
curl http://localhost:8000/
```

期待値:

```json
{"status":"ok"}
```

## 6. Render起動スクリプト確認

一時SQLiteで `scripts/start_render.sh` を確認する。

```bash
rm -f tmp_render_start_check.db
DATABASE_URL=sqlite:///./tmp_render_start_check.db PORT=8000 bash scripts/start_render.sh
```

サーバーが起動したら停止し、DBファイルを削除する。

```bash
rm -f tmp_render_start_check.db
```

## 7. 完了報告に含める内容

Codexの最終報告には、次を含める。

```text
変更したファイル一覧
実装した内容
実行したテスト
Renderで設定すべきBuild Command
Renderで設定すべきStart Command
必要な環境変数
未対応事項があればその内容
```

## 完了条件

```text
uv run pytest が成功する
alembic upgrade head が一時DBで成功する
app/main.py に Base.metadata.create_all() が残っていない
scripts/start_render.sh がある
render.yaml がある
READMEにRender手順がある
秘密情報が含まれていない
```
