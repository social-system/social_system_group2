# deploys

このディレクトリは、Render + Render PostgreSQL にデプロイするための Codex 実装指示書を置く場所である。

## 実行順

```text
STEP_00_SCOPE_AND_BASELINE.md
STEP_01_RUNTIME_CONFIG_AND_DATABASE_URL.md
STEP_02_DISABLE_PRODUCTION_CREATE_ALL_AND_SEEDING.md
STEP_03_ALEMBIC_INITIAL_MIGRATION.md
STEP_04_RENDER_DEPLOYMENT_FILES.md
STEP_05_TESTS_AND_POSTGRES_COMPATIBILITY.md
STEP_06_README_DEPLOYMENT_DOCS.md
STEP_07_FINAL_VERIFICATION.md
```

## 前提

```text
API: Render Web Service
DB: Render PostgreSQL
Schema管理: Alembic
ローカル開発DB: SQLite継続可
```

## Codexへの渡し方

各STEPを順番に開き、内容をそのままCodexへ渡す。

複数STEPを同時に実行させない。
