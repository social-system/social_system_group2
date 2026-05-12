# 在庫テーブルおよび在庫増減 API 実装仕様書

## 1. 目的

この仕様書は、レシートOCR・家計簿DBの次段階として、冷蔵庫などの在庫管理を実装するための設計書である。

DBには、OCR結果そのものではなく、ユーザー確認済みの購入履歴が保存されている前提とする。在庫管理では、その購入履歴のうち「在庫対象の商品」だけを在庫として反映する。

この実装で達成することは、次の4つである。

1. レシート登録済みの商品を在庫へ反映できる。
2. 現在の在庫量を商品単位で取得できる。
3. 消費、廃棄、手動修正によって在庫を増減できる。
4. なぜ在庫数が増減したのかを履歴として追跡できる。

## 2. 実装範囲

### 2.1 実装するもの

今回実装する対象は以下である。

| 区分 | 実装内容 |
|---|---|
| DB | `inventory_locations` |
| DB | `inventory_batches` |
| DB | `inventory_operations` |
| DB | `inventory_movements` |
| API | `POST /inventory/receipts/{receipt_id}/apply` |
| API | `GET /inventory/balances` |
| API | `GET /inventory/batches` |
| API | `GET /inventory/movements` |
| API | `POST /inventory/movements` |
| 初期データ | 冷蔵、冷凍、常温、その他 |
| テスト | 在庫反映、二重反映防止、消費、廃棄、手動追加、残量不足エラー |

### 2.2 実装しないもの

今回の実装対象外は以下である。

| 対象外 | 理由 |
|---|---|
| OCR API | OCRは別モジュールの責務であるため |
| レシピ提案API | 在庫DB完成後に実装するため |
| ユーザー認証 | MVPでは単一ユーザー前提で進めるため |
| 複数ユーザー対応 | MVPでは不要なため |
| 自動賞味期限推定 | 後続機能として扱うため |
| バーコード管理 | MVPでは不要なため |
| 画像保存 | 在庫管理の本質ではないため |

## 3. 前提となる既存DB

既存DBには、少なくとも次のテーブルまたは同等のテーブルが存在している前提である。

```txt
receipts
receipt_items
products
accounting_categories
product_aliases
product_unit_conversions
```

特に在庫反映では、`receipt_items` の以下のカラムを使用する。

| カラム | 用途 |
|---|---|
| `id` | 在庫反映済みかどうかの判定に使う |
| `receipt_id` | レシート単位で在庫反映するために使う |
| `product_id` | 在庫上の商品を識別するために使う |
| `raw_name` | 表示や履歴確認に使う |
| `normalized_name` | 人間向け表示に使う |
| `base_quantity` | 在庫に加算する数量 |
| `base_unit` | 在庫管理上の単位 |
| `is_inventory_target` | 在庫反映対象かどうかの判定に使う |

また、`products` には以下のカラムがある前提とする。

| カラム | 用途 |
|---|---|
| `id` | 商品ID |
| `name` | 商品名 |
| `default_base_unit` | 在庫管理上の標準単位 |
| `is_inventory_target` | 通常在庫対象にする商品かどうか |

## 4. 設計方針

## 4.1 在庫は購入履歴から直接計算しない

`receipt_items` は購入履歴であり、現在の在庫そのものではない。

たとえば卵を10個買ったあとに2個使った場合、`receipt_items` だけを見ても現在8個であることは分からない。

そのため、現在在庫は `inventory_batches` に保存し、増減履歴は `inventory_movements` に保存する。

```txt
receipt_items          購入履歴
inventory_batches      現在存在する在庫ロット
inventory_movements    在庫増減の履歴
```

## 4.2 在庫はロット単位で管理する

同じ商品でも、購入日、賞味期限、保管場所が異なる場合がある。

そのため、商品単位だけで1行にまとめず、購入または手動追加ごとに `inventory_batches` を作成する。

例:

```txt
卵 10個 2026-05-01購入 賞味期限2026-05-15 冷蔵
卵 6個  2026-05-05購入 賞味期限2026-05-20 冷蔵
```

この2つは、同じ商品であっても別ロットとして保存する。

## 4.3 数量は標準単位で管理する

レシート上では「1パック」「1袋」「1本」のように記録されることがある。

しかし、在庫管理では計算しやすい単位にそろえる必要がある。

例:

| 商品 | レシート上の単位 | 在庫管理上の単位 |
|---|---|---|
| 卵 | パック | 個 |
| 牛乳 | 本 | ml |
| 米 | 袋 | g |
| 肉 | パック | g |

在庫管理では、必ず `receipt_items.base_quantity` と `receipt_items.base_unit` を使う。

## 4.4 履歴を必ず残す

在庫を増減するときは、`inventory_batches.current_quantity` を更新するだけでは不十分である。

必ず `inventory_movements` に履歴を残す。

```txt
購入による増加    +10個
料理で消費        -2個
期限切れで廃棄    -1個
手動修正          +3個 または -3個
```

## 4.5 操作単位と明細単位を分ける

1回の在庫操作で、複数のロットが変化することがある。

例として、卵を12個消費するが、古いロットに6個、新しいロットに10個残っている場合、2つのロットから減らす必要がある。

そのため、操作全体を `inventory_operations` に保存し、ロットごとの増減を `inventory_movements` に保存する。

```txt
inventory_operations
  └── inventory_movements
  └── inventory_movements
```

## 5. テーブル定義

## 5.1 inventory_locations

在庫の保管場所を表す。

### カラム

| カラム | 型 | NULL | 説明 |
|---|---|---:|---|
| `id` | integer | false | 主キー |
| `name` | string(100) | false | 場所名 |
| `sort_order` | integer | false | 表示順 |
| `is_active` | boolean | false | 使用中かどうか |
| `created_at` | datetime | false | 作成日時 |
| `updated_at` | datetime | false | 更新日時 |

### 制約

| 制約 | 内容 |
|---|---|
| unique | `name` は一意 |

### 初期データ

| name | sort_order |
|---|---:|
| 冷蔵 | 10 |
| 冷凍 | 20 |
| 常温 | 30 |
| その他 | 90 |

### SQLAlchemyモデル例

```python
class InventoryLocation(Base):
    __tablename__ = "inventory_locations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

## 5.2 inventory_batches

現在存在している在庫ロットを表す。

### カラム

| カラム | 型 | NULL | 説明 |
|---|---|---:|---|
| `id` | integer | false | 主キー |
| `product_id` | integer | false | `products.id` |
| `receipt_item_id` | integer | true | 元になった `receipt_items.id` |
| `location_id` | integer | true | `inventory_locations.id` |
| `initial_quantity` | numeric(10,2) | false | 初期数量 |
| `current_quantity` | numeric(10,2) | false | 現在数量 |
| `unit` | string(50) | false | 在庫管理単位 |
| `purchased_at` | date | true | 購入日 |
| `expires_at` | date | true | 賞味期限または消費期限 |
| `status` | string(50) | false | `active` / `depleted` / `discarded` |
| `note` | string(255) | true | 備考 |
| `created_at` | datetime | false | 作成日時 |
| `updated_at` | datetime | false | 更新日時 |

### 制約

| 制約 | 内容 |
|---|---|
| foreign key | `product_id` references `products.id` |
| foreign key | `receipt_item_id` references `receipt_items.id` |
| foreign key | `location_id` references `inventory_locations.id` |
| unique | `receipt_item_id` は一意。ただしNULLは許可する |
| check | `initial_quantity > 0` |
| check | `current_quantity >= 0` |
| check | `status in ('active', 'depleted', 'discarded')` |

### 重要ルール

`receipt_item_id` を一意にする理由は、同じレシート明細を二重に在庫反映しないためである。

手動追加された在庫は、レシート由来ではないため `receipt_item_id = null` とする。

`unit` は `products.default_base_unit` と一致することを基本とする。

### SQLAlchemyモデル例

```python
class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    receipt_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("receipt_items.id"),
        nullable=True,
        unique=True,
        index=True,
    )

    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_locations.id"),
        nullable=True,
        index=True,
    )

    initial_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    current_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)

    purchased_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

## 5.3 inventory_operations

在庫操作の単位を表す。

1つの操作で複数のロットが増減する場合があるため、操作全体をこのテーブルに保存する。

### カラム

| カラム | 型 | NULL | 説明 |
|---|---|---:|---|
| `id` | integer | false | 主キー |
| `operation_type` | string(50) | false | 操作種別 |
| `receipt_id` | integer | true | レシート反映の場合の `receipts.id` |
| `idempotency_key` | string(255) | true | 二重実行防止キー |
| `reason` | string(255) | true | 理由 |
| `occurred_at` | datetime | false | 操作日時 |
| `created_at` | datetime | false | 作成日時 |

### operation_type

| 値 | 意味 |
|---|---|
| `receipt_apply` | レシート明細を在庫へ反映 |
| `consume` | 使用・消費 |
| `dispose` | 廃棄 |
| `adjustment_in` | 手動追加 |
| `adjustment_out` | 手動減少 |
| `transfer` | 保管場所移動 |

### 制約

| 制約 | 内容 |
|---|---|
| foreign key | `receipt_id` references `receipts.id` |
| unique | `idempotency_key` は一意。ただしNULLは許可する |
| check | `operation_type` は定義済みの値のみ |

### SQLAlchemyモデル例

```python
class InventoryOperation(Base):
    __tablename__ = "inventory_operations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    operation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    receipt_id: Mapped[int | None] = mapped_column(
        ForeignKey("receipts.id"),
        nullable=True,
        index=True,
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
```

## 5.4 inventory_movements

ロットごとの在庫増減を表す。

### カラム

| カラム | 型 | NULL | 説明 |
|---|---|---:|---|
| `id` | integer | false | 主キー |
| `operation_id` | integer | false | `inventory_operations.id` |
| `batch_id` | integer | true | `inventory_batches.id` |
| `product_id` | integer | false | `products.id` |
| `location_id` | integer | true | `inventory_locations.id` |
| `movement_type` | string(50) | false | 増減種別 |
| `quantity_delta` | numeric(10,2) | false | 増減数量 |
| `unit` | string(50) | false | 単位 |
| `receipt_item_id` | integer | true | 元になった `receipt_items.id` |
| `reason` | string(255) | true | 理由 |
| `occurred_at` | datetime | false | 発生日時 |
| `created_at` | datetime | false | 作成日時 |

### movement_type

| 値 | quantity_delta | 意味 |
|---|---:|---|
| `purchase` | 正 | 購入による増加 |
| `consume` | 負 | 使用・消費 |
| `dispose` | 負 | 廃棄 |
| `adjustment_in` | 正 | 手動追加 |
| `adjustment_out` | 負 | 手動減少 |
| `transfer_in` | 正 | 移動先への増加 |
| `transfer_out` | 負 | 移動元からの減少 |

### 制約

| 制約 | 内容 |
|---|---|
| foreign key | `operation_id` references `inventory_operations.id` |
| foreign key | `batch_id` references `inventory_batches.id` |
| foreign key | `product_id` references `products.id` |
| foreign key | `location_id` references `inventory_locations.id` |
| foreign key | `receipt_item_id` references `receipt_items.id` |
| check | `quantity_delta != 0` |
| check | `movement_type` は定義済みの値のみ |

### SQLAlchemyモデル例

```python
class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    operation_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_operations.id"),
        nullable=False,
        index=True,
    )

    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_batches.id"),
        nullable=True,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_locations.id"),
        nullable=True,
        index=True,
    )

    movement_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)

    receipt_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("receipt_items.id"),
        nullable=True,
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
```

## 6. API仕様

## 6.1 POST /inventory/receipts/{receipt_id}/apply

レシート明細から在庫対象の商品を在庫へ反映する。

### 目的

`receipt_items` のうち、在庫対象の商品だけを `inventory_batches` に追加し、`inventory_movements` に購入履歴を作成する。

### パスパラメータ

| 名前 | 型 | 必須 | 説明 |
|---|---|---:|---|
| `receipt_id` | integer | true | 在庫反映するレシートID |

### リクエストボディ

```json
{
  "default_location_id": 1,
  "expires_at_by_receipt_item_id": {
    "31": "2026-05-20",
    "32": "2026-05-18"
  },
  "idempotency_key": "receipt:12:apply-inventory"
}
```

### リクエスト項目

| 項目 | 型 | 必須 | 説明 |
|---|---|---:|---|
| `default_location_id` | integer | false | 作成する在庫ロットの標準保管場所 |
| `expires_at_by_receipt_item_id` | object | false | 明細IDごとの期限日 |
| `idempotency_key` | string | false | 二重実行防止キー |

### 処理対象条件

以下をすべて満たす `receipt_items` だけを処理する。

```txt
receipt_items.receipt_id = pathのreceipt_id
receipt_items.is_inventory_target = true
receipt_items.product_id is not null
receipt_items.base_quantity is not null
receipt_items.base_quantity > 0
receipt_items.base_unit is not null
```

### 処理内容

1. `receipt_id` に該当する `receipts` を取得する。
2. 見つからない場合は404を返す。
3. `idempotency_key` が指定されており、同じキーの `inventory_operations` が存在する場合は、既存の実行結果として200を返す。
4. 対象の `receipt_items` を取得する。
5. 各明細について、すでに `inventory_batches.receipt_item_id` に存在する場合はスキップする。
6. 対象明細ごとに `inventory_batches` を作成する。
7. 対象明細ごとに `inventory_movements` を作成する。
8. 操作全体を `inventory_operations` に保存する。
9. すべてを同一transactionで確定する。

### 二重反映防止

二重反映防止は2段階で行う。

| 方法 | 目的 |
|---|---|
| `inventory_operations.idempotency_key` | 同じAPIリクエストの二重送信を防ぐ |
| `inventory_batches.receipt_item_id unique` | 同じレシート明細の二重在庫化を防ぐ |

### レスポンス例

```json
{
  "receipt_id": 12,
  "operation_id": 100,
  "applied_count": 2,
  "skipped_count": 2,
  "items": [
    {
      "receipt_item_id": 31,
      "product_id": 1,
      "product_name": "卵",
      "quantity": "10.00",
      "unit": "個",
      "batch_id": 201,
      "status": "applied"
    },
    {
      "receipt_item_id": 32,
      "product_id": 2,
      "product_name": "牛乳",
      "quantity": "1000.00",
      "unit": "ml",
      "batch_id": 202,
      "status": "applied"
    },
    {
      "receipt_item_id": 33,
      "product_name": "洗剤",
      "status": "skipped",
      "reason": "not_inventory_target"
    },
    {
      "receipt_item_id": 34,
      "product_name": "不明商品",
      "status": "skipped",
      "reason": "missing_product_or_base_quantity"
    }
  ]
}
```

### エラー

| HTTP | 条件 |
|---:|---|
| 404 | `receipt_id` が存在しない |
| 422 | `default_location_id` が存在しない |
| 409 | idempotency処理で矛盾が発生した |
| 500 | transaction失敗 |

## 6.2 GET /inventory/balances

現在の在庫を商品単位で集計して返す。

### クエリパラメータ

| 名前 | 型 | 必須 | 説明 |
|---|---|---:|---|
| `location_id` | integer | false | 保管場所で絞り込み |
| `product_id` | integer | false | 商品で絞り込み |
| `include_zero` | boolean | false | 残量0を含めるか。標準はfalse |

### 集計ルール

```sql
SELECT
    product_id,
    unit,
    SUM(current_quantity) AS quantity
FROM inventory_batches
WHERE status = 'active'
  AND current_quantity > 0
GROUP BY product_id, unit;
```

### レスポンス例

```json
{
  "items": [
    {
      "product_id": 1,
      "product_name": "卵",
      "quantity": "16.00",
      "unit": "個",
      "nearest_expires_at": "2026-05-15",
      "batch_count": 2
    },
    {
      "product_id": 2,
      "product_name": "牛乳",
      "quantity": "1000.00",
      "unit": "ml",
      "nearest_expires_at": "2026-05-18",
      "batch_count": 1
    }
  ]
}
```

## 6.3 GET /inventory/batches

現在の在庫ロット一覧を返す。

### クエリパラメータ

| 名前 | 型 | 必須 | 説明 |
|---|---|---:|---|
| `product_id` | integer | false | 商品で絞り込み |
| `location_id` | integer | false | 保管場所で絞り込み |
| `status` | string | false | `active` / `depleted` / `discarded` |
| `expires_before` | date | false | 指定日以前に期限が来るもの |
| `include_zero` | boolean | false | 残量0を含めるか |

### 並び順

標準の並び順は以下とする。

```txt
expires_at が近い順
purchased_at が古い順
id が古い順
```

`expires_at` がNULLの場合は最後に並べる。

### レスポンス例

```json
{
  "items": [
    {
      "batch_id": 201,
      "product_id": 1,
      "product_name": "卵",
      "initial_quantity": "10.00",
      "current_quantity": "8.00",
      "unit": "個",
      "location_id": 1,
      "location_name": "冷蔵",
      "purchased_at": "2026-05-12",
      "expires_at": "2026-05-20",
      "status": "active",
      "receipt_item_id": 31
    }
  ]
}
```

## 6.4 GET /inventory/movements

在庫増減履歴を返す。

### クエリパラメータ

| 名前 | 型 | 必須 | 説明 |
|---|---|---:|---|
| `product_id` | integer | false | 商品で絞り込み |
| `batch_id` | integer | false | ロットで絞り込み |
| `operation_id` | integer | false | 操作で絞り込み |
| `movement_type` | string | false | 増減種別で絞り込み |
| `from_date` | date | false | 発生日の開始 |
| `to_date` | date | false | 発生日の終了 |
| `limit` | integer | false | 取得件数。標準100 |
| `offset` | integer | false | 取得開始位置。標準0 |

### レスポンス例

```json
{
  "items": [
    {
      "movement_id": 301,
      "operation_id": 100,
      "batch_id": 201,
      "product_id": 1,
      "product_name": "卵",
      "movement_type": "purchase",
      "quantity_delta": "10.00",
      "unit": "個",
      "reason": "receipt apply",
      "occurred_at": "2026-05-12T10:00:00"
    },
    {
      "movement_id": 302,
      "operation_id": 101,
      "batch_id": 201,
      "product_id": 1,
      "product_name": "卵",
      "movement_type": "consume",
      "quantity_delta": "-2.00",
      "unit": "個",
      "reason": "卵焼きに使用",
      "occurred_at": "2026-05-13T08:00:00"
    }
  ]
}
```

## 6.5 POST /inventory/movements

手動で在庫を増減する。

消費、廃棄、手動追加、手動減少を扱う。

### リクエストボディ

```json
{
  "product_id": 1,
  "movement_type": "consume",
  "quantity": "2.00",
  "unit": "個",
  "batch_id": null,
  "location_id": 1,
  "reason": "卵焼きに使用",
  "occurred_at": "2026-05-13T08:00:00",
  "idempotency_key": "manual:consume:20260513:egg:001"
}
```

### リクエスト項目

| 項目 | 型 | 必須 | 説明 |
|---|---|---:|---|
| `product_id` | integer | true | 商品ID |
| `movement_type` | string | true | `consume` / `dispose` / `adjustment_in` / `adjustment_out` |
| `quantity` | numeric | true | 正の数量 |
| `unit` | string | true | 在庫管理単位 |
| `batch_id` | integer | false | 特定ロットを指定する場合 |
| `location_id` | integer | false | 保管場所。手動追加時に使用 |
| `reason` | string | false | 理由 |
| `occurred_at` | datetime | false | 発生日時。未指定なら現在時刻 |
| `idempotency_key` | string | false | 二重実行防止キー |

### movement_type別の処理

| movement_type | 処理 |
|---|---|
| `consume` | 在庫を減らす |
| `dispose` | 在庫を減らす。理由がなければ `discarded` として扱う |
| `adjustment_in` | 新しいロットを作成し、在庫を増やす |
| `adjustment_out` | 在庫を減らす |

### quantity_delta変換

APIでは `quantity` は常に正の数として受け取る。

DB保存時には以下のように変換する。

| movement_type | quantity_delta |
|---|---:|
| `consume` | `-quantity` |
| `dispose` | `-quantity` |
| `adjustment_in` | `+quantity` |
| `adjustment_out` | `-quantity` |

### batch_idが指定された場合

指定されたロットだけを増減する。

減少系の場合、`current_quantity < quantity` なら422を返す。

### batch_idが指定されない場合

減少系の場合、バックエンドが減らすロットを自動選択する。

選択順は以下とする。

```txt
1. expires_at が近いもの
2. purchased_at が古いもの
3. id が古いもの
```

`expires_at` がNULLのロットは、期限ありロットの後に使う。

### 複数ロットにまたがる消費

例として、卵を12個消費する。

在庫は以下とする。

| batch_id | current_quantity |
|---:|---:|
| 201 | 6 |
| 202 | 10 |

この場合、1つの `inventory_operations` に対して、2つの `inventory_movements` を作成する。

| batch_id | quantity_delta |
|---:|---:|
| 201 | -6 |
| 202 | -6 |

処理後の在庫は以下となる。

| batch_id | current_quantity |
|---:|---:|
| 201 | 0 |
| 202 | 4 |

`batch_id = 201` は `status = depleted` に更新する。

### 手動追加の場合

`adjustment_in` の場合は、新しい `inventory_batches` を作成する。

```json
{
  "product_id": 1,
  "movement_type": "adjustment_in",
  "quantity": "6.00",
  "unit": "個",
  "location_id": 1,
  "reason": "初期在庫登録"
}
```

作成される `inventory_batches` は以下のような意味になる。

```txt
receipt_item_id = null
initial_quantity = 6
current_quantity = 6
unit = 個
status = active
```

### レスポンス例

```json
{
  "operation_id": 101,
  "movement_type": "consume",
  "product_id": 1,
  "product_name": "卵",
  "requested_quantity": "12.00",
  "unit": "個",
  "movements": [
    {
      "movement_id": 401,
      "batch_id": 201,
      "quantity_delta": "-6.00",
      "remaining_quantity": "0.00"
    },
    {
      "movement_id": 402,
      "batch_id": 202,
      "quantity_delta": "-6.00",
      "remaining_quantity": "4.00"
    }
  ]
}
```

### エラー

| HTTP | 条件 |
|---:|---|
| 404 | `product_id` が存在しない |
| 404 | `batch_id` が存在しない |
| 422 | `quantity <= 0` |
| 422 | `unit` が商品標準単位と一致しない |
| 422 | 減少させる在庫が不足している |
| 409 | 同じ `idempotency_key` の操作がすでに存在する |

## 7. ステータス更新ルール

`inventory_batches.status` は、数量と操作によって更新する。

| 条件 | status |
|---|---|
| `current_quantity > 0` | `active` |
| `current_quantity = 0` かつ通常消費 | `depleted` |
| `current_quantity = 0` かつ廃棄 | `discarded` |

一度 `discarded` になったロットを再利用しない。

手動追加が必要な場合は、新しいロットを作成する。

## 8. transactionルール

在庫増減では、以下を必ず1つのtransactionで実行する。

```txt
inventory_operations 作成
inventory_batches 作成または更新
inventory_movements 作成
```

どれか1つでも失敗したら、すべてrollbackする。

特に以下は禁止する。

```txt
current_quantity だけ更新して movement を作らない
movement だけ作って current_quantity を更新しない
operation だけ作って movement がない
```

## 9. バリデーションルール

## 9.1 共通

| 項目 | ルール |
|---|---|
| `quantity` | 必ず0より大きい |
| `unit` | 空文字不可 |
| `product_id` | 存在する商品であること |
| `location_id` | 指定された場合、存在する場所であること |
| `reason` | 任意。ただし255文字以内 |
| `occurred_at` | 未指定ならサーバー時刻 |

## 9.2 単位

APIで指定された `unit` は、原則として `products.default_base_unit` と一致しなければならない。

例:

| 商品 | default_base_unit | 許可するunit |
|---|---|---|
| 卵 | 個 | 個 |
| 牛乳 | ml | ml |
| 米 | g | g |

`パック`、`袋`、`本` のような購入時単位は、在庫APIでは受け取らない。

その変換は、レシート登録前またはレシート登録時に `base_quantity` / `base_unit` として済ませる。

## 9.3 在庫不足

減少系操作で在庫が不足している場合は、DBを更新せず422を返す。

例:

```json
{
  "detail": "insufficient_inventory",
  "product_id": 1,
  "requested_quantity": "12.00",
  "available_quantity": "8.00",
  "unit": "個"
}
```

## 10. Pydanticスキーマ案

## 10.1 InventoryReceiptApplyRequest

```python
class InventoryReceiptApplyRequest(BaseModel):
    default_location_id: int | None = None
    expires_at_by_receipt_item_id: dict[int, date] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=255)
```

## 10.2 InventoryReceiptApplyItemResponse

```python
class InventoryReceiptApplyItemResponse(BaseModel):
    receipt_item_id: int
    product_id: int | None = None
    product_name: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    batch_id: int | None = None
    status: str
    reason: str | None = None
```

## 10.3 InventoryReceiptApplyResponse

```python
class InventoryReceiptApplyResponse(BaseModel):
    receipt_id: int
    operation_id: int | None
    applied_count: int
    skipped_count: int
    items: list[InventoryReceiptApplyItemResponse]
```

## 10.4 InventoryMovementCreateRequest

```python
class InventoryMovementCreateRequest(BaseModel):
    product_id: int
    movement_type: Literal["consume", "dispose", "adjustment_in", "adjustment_out"]
    quantity: Decimal
    unit: str
    batch_id: int | None = None
    location_id: int | None = None
    reason: str | None = Field(default=None, max_length=255)
    occurred_at: datetime | None = None
    idempotency_key: str | None = Field(default=None, max_length=255)
```

## 10.5 InventoryMovementCreateResponse

```python
class InventoryMovementResult(BaseModel):
    movement_id: int
    batch_id: int
    quantity_delta: Decimal
    remaining_quantity: Decimal

class InventoryMovementCreateResponse(BaseModel):
    operation_id: int
    movement_type: str
    product_id: int
    product_name: str
    requested_quantity: Decimal
    unit: str
    movements: list[InventoryMovementResult]
```

## 11. CRUD処理方針

## 11.1 apply_receipt_to_inventory

関数名案:

```python
def apply_receipt_to_inventory(
    db: Session,
    receipt_id: int,
    request: InventoryReceiptApplyRequest,
) -> InventoryReceiptApplyResponse:
    ...
```

処理手順:

1. receiptを取得する。
2. 対象receipt_itemsを取得する。
3. operationを作成する。
4. 各itemについて在庫対象か判定する。
5. 処理できないitemはskip結果に入れる。
6. 処理できるitemはbatchを作成する。
7. purchase movementを作成する。
8. transactionをcommitする。
9. レスポンスを返す。

## 11.2 create_inventory_movement

関数名案:

```python
def create_inventory_movement(
    db: Session,
    request: InventoryMovementCreateRequest,
) -> InventoryMovementCreateResponse:
    ...
```

処理手順:

1. productを取得する。
2. unitを検証する。
3. operationを作成する。
4. movement_typeごとに処理を分岐する。
5. 減少系なら対象batchを選択する。
6. current_quantityを更新する。
7. movementを作成する。
8. batchのstatusを更新する。
9. transactionをcommitする。
10. レスポンスを返す。

## 12. ルーティング構成案

既存構成に合わせて、以下のようなファイルを追加する。

```txt
app/
  models.py または app/inventory/models.py
  schemas/
    inventory_requests.py
    inventory_responses.py
  crud/
    inventory.py
  routes/
    inventory.py
```

`app/main.py` で router を追加する。

```python
app.include_router(inventory_router)
```

router prefix は以下を推奨する。

```python
router = APIRouter(prefix="/inventory", tags=["inventory"])
```

## 13. テスト仕様

## 13.1 レシート反映

### test_apply_receipt_to_inventory_success

条件:

```txt
receipt_items に在庫対象の卵がある
product_id, base_quantity, base_unit が設定されている
```

期待:

```txt
inventory_batches が1件作成される
inventory_movements が1件作成される
quantity_delta が正の値になる
current_quantity が base_quantity と一致する
```

## 13.2 二重反映防止

### test_apply_receipt_to_inventory_twice_skips_existing_item

条件:

```txt
同じ receipt_id に対して apply API を2回呼ぶ
```

期待:

```txt
2回目は既存 receipt_item_id を skip する
inventory_batches が重複作成されない
```

## 13.3 在庫対象外スキップ

### test_apply_receipt_skips_non_inventory_item

条件:

```txt
receipt_items.is_inventory_target = false
```

期待:

```txt
在庫ロットを作成しない
レスポンスで status = skipped
reason = not_inventory_target
```

## 13.4 消費

### test_consume_inventory_from_oldest_batch

条件:

```txt
同じ商品に複数batchがある
batch_id を指定せず consume する
```

期待:

```txt
expires_at が近いbatchから減る
inventory_movements が作成される
current_quantity が更新される
```

## 13.5 複数ロット消費

### test_consume_inventory_across_multiple_batches

条件:

```txt
古いbatchだけでは数量が足りない
全体では数量が足りる
```

期待:

```txt
複数batchから減る
movementが複数作成される
operationは1件だけ作成される
```

## 13.6 在庫不足

### test_consume_inventory_insufficient_quantity

条件:

```txt
在庫8個に対して12個 consume する
```

期待:

```txt
422を返す
current_quantity は変わらない
movement は作成されない
```

## 13.7 手動追加

### test_adjustment_in_creates_new_batch

条件:

```txt
adjustment_in で6個追加する
```

期待:

```txt
receipt_item_id = null の batch が作成される
movement quantity_delta が +6 になる
```

## 13.8 手動減少

### test_adjustment_out_decreases_inventory

条件:

```txt
adjustment_out で在庫を減らす
```

期待:

```txt
current_quantity が減る
movement quantity_delta が負になる
```

## 14. 実装順序

Codexは以下の順に実装する。

```txt
1. inventory用モデルを追加する
2. 初期データ投入処理を追加する
3. Pydantic request/response schemaを追加する
4. CRUD関数を追加する
5. routerを追加する
6. main.pyにrouterを登録する
7. テストデータ作成用fixtureを追加する
8. APIテストを追加する
9. compileallを実行する
10. pytestを実行する
```

## 15. Codexへの実装指示

以下をそのままCodexに渡す。

```txt
docs/INVENTORY_IMPLEMENTATION_SPEC.md を読み、この仕様に従って在庫管理用DBテーブルとAPIを実装してください。

実装対象は以下です。

- inventory_locations
- inventory_batches
- inventory_operations
- inventory_movements
- POST /inventory/receipts/{receipt_id}/apply
- GET /inventory/balances
- GET /inventory/batches
- GET /inventory/movements
- POST /inventory/movements

重要な設計ルールは以下です。

- receipt_items は購入履歴であり、現在在庫として直接扱わない
- inventory_batches は現在在庫のロットを表す
- inventory_operations は1回の在庫操作を表す
- inventory_movements はロットごとの増減履歴を表す
- receipt_item_id は在庫反映の二重実行防止に使う
- 同じレシート明細を二重にinventory_batchesへ登録してはいけない
- 減少系操作では、batch_id未指定の場合、期限が近いロットから順に減らす
- 在庫増減は必ずtransaction内で実行する
- current_quantity更新とmovement作成は必ず同時に行う
- OCR API、レシピ提案API、認証、ユーザー管理は実装しない

実装後に以下を実行してください。

- uv run python -m compileall app
- uv run pytest

最後に、実装した内容、テスト結果、残TODOを報告してください。
```

## 16. 受け入れ条件

この実装は、以下を満たしたら完了とする。

```txt
レシート明細から在庫ロットを作成できる
在庫対象外商品はスキップできる
同じレシート明細を二重反映しない
現在在庫を商品単位で集計できる
在庫ロット一覧を取得できる
消費で在庫を減らせる
廃棄で在庫を減らせる
手動追加で在庫を増やせる
手動減少で在庫を減らせる
在庫不足時にDBを変更せずエラーにできる
すべての在庫増減履歴をinventory_movementsで確認できる
compileallが成功する
pytestが成功する
```

## 17. 後続TODO

今回実装しないが、後で追加するとよい機能は以下である。

```txt
賞味期限の自動推定
商品ごとの標準保存場所
在庫の場所移動API
レシピ提案用の在庫取得API
在庫残量が少ない商品の通知
期限切れ間近商品の通知
手動でbatchのexpires_atやlocationを修正するAPI
ユーザー別在庫管理
```
