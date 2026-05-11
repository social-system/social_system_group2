# レシート管理バックエンド

一人用のローカル家計簿として使う、レシート管理バックエンドです。

FastAPI、SQLAlchemy、SQLite を使い、レシートの登録、一覧取得、詳細取得、削除を行います。

## 主な機能

- レシート登録
- レシート一覧取得
- レシート詳細取得
- レシート削除
- レシート登録時のバリデーション
- テスト用 SQLite DB を使った API テスト
- React + TypeScript フロントエンドからの呼び出しに必要な CORS 設定

## 使用技術

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- pytest
- uv

## ディレクトリ構成

```text
app/
  common/              # 日付変換などの共通処理
  crud/                # DB 操作、業務ルール検証
  db/                  # DB セッション設定
  receipts/            # SQLAlchemy モデル
  routes/              # FastAPI ルーター
  schemas/             # Pydantic スキーマ
tests/                 # API テスト
docs/milestone/        # 実装マイルストーン
```

## セットアップ

依存関係をインストールします。

```bash
uv sync
```

必要に応じて仮想環境を有効化します。

```bash
source .venv/bin/activate
```

## 起動方法

バックエンド API を起動します。

```bash
uv run uvicorn app.main:app --reload
```

通常は以下の URL で起動します。

```text
http://localhost:8000
```

ヘルスチェック:

```bash
curl http://localhost:8000/
```

レスポンス例:

```json
{
  "status": "ok"
}
```

## API

### レシート登録

```http
POST /receipts
```

リクエスト例:

```json
{
  "receipt_total": 500,
  "items": [
    {
      "item": "milk",
      "num": 1,
      "amount": 500,
      "total": 500,
      "date": 20260428,
      "ingredients": 1
    }
  ]
}
```

成功時は `201 Created` を返します。

### レシート一覧取得

```http
GET /receipts
```

クエリパラメータ:

| 名前 | 内容 |
| --- | --- |
| `skip` | 取得開始位置 |
| `limit` | 取得件数 |
| `date_from` | 開始日。`YYYYMMDD` 形式 |
| `date_to` | 終了日。`YYYYMMDD` 形式 |

レスポンス例:

```json
[
  {
    "id": 1,
    "receipt_total": 500,
    "item_count": 1,
    "date_min": 20260428,
    "date_max": 20260428
  }
]
```

### レシート詳細取得

```http
GET /receipts/{receipt_id}
```

存在しない ID の場合は `404 Not Found` を返します。

### レシート削除

```http
DELETE /receipts/{receipt_id}
```

レスポンス例:

```json
{
  "deleted": true,
  "id": 1
}
```

存在しない ID の場合は `404 Not Found` を返します。

## バリデーション

主な入力チェックは以下です。

| 条件 | ステータス |
| --- | ---: |
| `items` が空 | 422 |
| `date` が実在しない | 422 |
| `item` が空 | 422 |
| `num` が 0 以下 | 422 |
| `amount` が 0 未満 | 422 |
| `total` が 0 未満 | 422 |
| `num * amount != total` | 400 |
| `receipt_total != sum(items.total)` | 400 |
| 存在しないレシート取得 | 404 |
| 存在しないレシート削除 | 404 |

`date` は `YYYYMMDD` 形式の整数として受け取ります。

例:

- `20260428`: 有効
- `20260230`: 無効

## DB

通常実行時は、プロジェクト直下の SQLite DB を使います。

```text
receipts.db
```

テーブルは大きく 2 つです。

- `receipts`: レシート本体
- `receipt_items`: レシート明細

親レシートを削除すると、関連する明細も削除されます。

## テスト

テストを実行します。

```bash
uv run pytest
```

テストでは通常開発用の `receipts.db` は使わず、テスト用 SQLite DB に差し替えます。

## フロントエンド連携

React + TypeScript + Vite のフロントエンドから API を呼び出す場合、バックエンドを先に起動します。

```bash
uv run uvicorn app.main:app --reload
```

別ターミナルでフロントエンドを起動します。

```bash
cd frontend
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

ブラウザで以下を開きます。

```text
http://localhost:5173
```

このバックエンドでは、Vite の標準開発サーバーから呼び出せるように、以下の origin を CORS で許可しています。

```text
http://localhost:5173
```

## 連携確認の流れ

最低限、以下を確認します。

1. 一覧画面で `GET /receipts` が成功する
2. 登録画面で `POST /receipts` が成功する
3. 登録後、一覧にレシートが表示される
4. 詳細画面で `GET /receipts/{receipt_id}` が成功する
5. 一覧または詳細画面から `DELETE /receipts/{receipt_id}` が成功する
6. 削除後、同じ ID の詳細取得が `404` になる
7. API エラーが画面に表示される

## 現時点で実装しないもの

このプロジェクトは当面、一人用のローカルアプリとして開発します。

そのため、現時点では以下を実装していません。

- 認証
- ユーザー管理
- 世帯管理
- `user_id` によるデータ分離
- OCR 連携
- レシート更新 API
- 集計 API
- Alembic などのマイグレーション
- 本番用 DB 構成
- 外部サービス連携

## 開発時の注意

- GitHub への push は手動確認後に行います
- テストでは通常開発用の `receipts.db` を使わないようにします
- バックエンド API のフィールド名は snake_case です
- フロントエンドから登録する場合も、API 通信時は `receipt_total` などのフィールド名をそのまま使います
- 不正な入力値は、形式不正なら `422`、業務ルール不整合なら `400` を返します
