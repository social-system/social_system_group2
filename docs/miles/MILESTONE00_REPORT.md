# MILESTONE00 REPORT

## 確認したファイル

- `AGENTS.md`
- `README.md`
- `docs/miles/README.md`
- `docs/miles/MILESTONE00_OVERVIEW.md`
- `docs/DATABASE_DESIGN.md`
- `docs/API_SPEC.md`
- `docs/OCR_DB_INTERFACE.md`
- `docs/CODEX_IMPLEMENTATION_PLAN.md`
- `app/receipts/models.py`
- `app/schemas/receipts_requests.py`
- `app/schemas/receipts_responses.py`
- `app/crud/receipts_create.py`
- `app/crud/receipts.py`
- `app/crud/prices.py`
- `app/routes/receipts_create.py`
- `app/routes/receipts.py`
- `app/routes/prices.py`
- `app/main.py`
- `tests/conftest.py`
- `tests/test_receipts.py`
- `tests/test_prices.py`
- `tests/test_inventory.py`
- `tests/test_setup.py`
- `pyproject.toml`

## 現在存在する関連モデル

`app/receipts/models.py` に次のモデルが存在する。

- `Receipt`
  - `receipts` テーブル。
  - `purchased_at`, `store_name`, `total_amount`, `items_total`, `adjustment_amount`, `source` を持つ。
  - `store_name` は nullable で反映済み。
- `ReceiptItem`
  - `receipt_items` テーブル。
  - `product_id` は `products.id` への nullable FK。
  - `category_id` は `accounting_categories.id` への nullable FK。
  - `raw_name`, `normalized_name`, `purchased_quantity`, `purchased_unit`, `base_quantity`, `base_unit`, `unit_price`, `line_total`, `is_inventory_target` を持つ。
- `AccountingCategory`
  - `accounting_categories` テーブル。
  - `name`, `sort_order` を持つ。
- `Product`
  - `products` テーブル。
  - `name`, `default_base_unit`, `default_category_id`, `is_inventory_target` を持つ。
  - `name_key` はまだ存在しない。
- `ProductAlias`
  - `product_aliases` テーブル。
  - 現状は `raw_name`, `product_id` のみ。
  - `alias_name`, `alias_key`, `source`, `is_active` はまだ存在しない。
- `ProductUnitConversion`
  - `product_unit_conversions` テーブル。
  - `product_id`, `from_unit`, `to_unit`, `multiplier` を持つ。

## 現在存在する関連 API

- `POST /receipts`
  - `app/routes/receipts_create.py`
  - ユーザー確認済みの `ReceiptCreate` を受け取る。
  - `items_total` と `adjustment_amount` は `app/crud/receipts_create.py` で計算する。
  - `product_id` / `category_id` が指定された場合は存在確認し、存在しない場合は `400`。
  - `product_id = null` の item は登録可能。
- `GET /receipts`
  - `app/routes/receipts.py`
  - `skip`, `limit`, `date_from`, `date_to`, `category_id`, `inventory_only` に対応済み。
- `GET /receipts/{receipt_id}`
  - `app/routes/receipts.py`
  - 明細を含む詳細を返す。
- `DELETE /receipts/{receipt_id}`
  - `app/routes/receipts.py`
  - 存在しない ID は `404`。
- `GET /prices/cheapest`
  - `app/routes/prices.py`
  - 存在する。
  - `product_id` と `period_days` を query parameter で受け取る。
  - `app/crud/prices.py` は `receipt_items.product_id` を基準に検索し、`normalized_name` では検索しない。
  - `base_quantity` null / 0、`base_unit` null、`store_name` null、期間外の履歴は除外する。

現時点で `POST /receipts/prepare` は存在しない。

## 現状の `POST /receipts` request schema

`app/schemas/receipts_requests.py` の `ReceiptCreate` は次を受け取る。

```text
purchased_at: int
store_name: str | None
total_amount: int >= 0
items: list[ReceiptItemCreate] min_length=1
```

`ReceiptItemCreate` は次を受け取る。

```text
raw_name: str
normalized_name: str | None
product_id: int | None
category_id: int | None
purchased_quantity: Decimal > 0
purchased_unit: str | None
base_quantity: Decimal | None
base_unit: str | None
unit_price: int | None >= 0
line_total: int >= 0
is_inventory_target: bool
```

現在の validation:

- `raw_name` は trim 後に空なら `422`。
- `store_name`, `normalized_name`, `purchased_unit`, `base_unit` は空文字を `None` に変換する。
- `purchased_at` は `YYYYMMDD` として実在日付か確認する。
- `items` は 1 件以上。
- `is_inventory_target = true` の場合、`normalized_name`, `base_quantity`, `base_unit` が必須。
- `unit_price * purchased_quantity == line_total` は必須ではない。
- `total_amount == sum(line_total)` は必須ではない。

## OCR JSON と DB request JSON の主な差分

`docs/OCR_DB_INTERFACE.md` の OCR 仮 JSON と、現在の `POST /receipts` request には次の差分がある。

- OCR 側には `status` があるが、DB request にはない。
- OCR 側には receipt 全体の `warnings` があるが、DB request にはない。
- OCR item には `confidence` があるが、DB request にはない。
- OCR item には item ごとの `warnings` があるが、DB request にはない。
- OCR item は `category_name` を返すが、DB request は `category_id` を要求する。
- OCR item は `product_id` を決めない前提だが、DB request は任意で `product_id` を受け取る。
- OCR の `normalized_name` は AI 推定候補だが、DB の `normalized_name` は保存されるアプリ内商品名として扱われている。
- OCR では不明値が `null` で返りうるが、DB request は在庫対象 item について `normalized_name`, `base_quantity`, `base_unit` を必須にしている。
- prepare API がないため、現状ではフロントエンド側で OCR 専用項目の除去、`category_name -> category_id`、`normalized_name/raw_name -> product_id` の解決、登録可能 JSON への整形を行う必要がある。

## 指定論点の確認結果

- product 関連テーブルは存在する。
  - `products`, `product_aliases`, `product_unit_conversions` がモデル定義済み。
- `product_aliases` は存在する。
  - ただし現状は `raw_name` と `product_id` 中心で、後続 milestone の `alias_name` / `alias_key` 形式ではない。
- `store_name` は `receipts` に反映済み。
  - request / response / tests / cheapest price API でも利用されている。
- `GET /prices/cheapest` は存在する。
  - `product_id` 基準で動作している。
- `POST /receipts` は現在、確認済み DB request JSON を受け取る。
  - OCR JSON をそのまま受け取る schema ではない。
- `products.name_key` は存在しない。
- `product_aliases.alias_key` は存在しない。
- `normalized_name` から `product_id` を解決する処理は存在しない。
  - `app/crud/receipts_create.py` は指定済み `product_id` の存在確認だけを行う。
- OCR JSON をそのまま受け取れる prepare API は存在しない。
- `POST /receipts` は `product_id` 未解決の item を許可する。
  - `product_id = null` は登録可能。
  - `product_id` に存在しない ID が指定された場合は `400`。
  - 在庫対象の場合は `product_id` が null でも、`normalized_name`, `base_quantity`, `base_unit` があれば登録可能。

## DB 側で吸収できる差分

後続 milestone で DB 側に寄せると、フロントエンド側の変換量を減らせる差分は次の通り。

- OCR JSON から DB 登録用 JSON への変換。
  - `status`, `confidence`, `warnings` など DB 登録不要項目の除去。
  - `POST /receipts` に送れる `receipt` オブジェクトの生成。
- `raw_name` / `normalized_name` 候補からの `product_id` 解決。
  - `products.name_key` と `product_aliases.alias_key` を使う想定。
- 解決済み商品の情報補完。
  - `normalized_name` を `products.name` に置き換える。
  - `category_id` を `products.default_category_id` から補完する。
  - `base_unit` を `products.default_base_unit` から補助できる。
- 未解決商品の扱い。
  - `product_id = null` のまま返し、候補や validation issue を返す。
  - 現状の `POST /receipts` は `product_id = null` を保存できるため、prepare 後の未解決 item も購入履歴としては登録可能。
- `category_name -> category_id`。
  - 現在この変換処理はない。DB 側で吸収するなら category 名の検索・補完ロジックが必要。

## 後続 milestone で変更すべきファイル

- `app/receipts/models.py`
  - `products.name_key` 追加。
  - `product_aliases` を `alias_name`, `alias_key`, `source`, `is_active` 形式へ強化。
- `app/crud/`
  - 商品名正規化関数と `resolve_product()` の追加。
  - prepare 用 CRUD の追加。
  - product search / alias learning 用 CRUD の追加。
- `app/routes/`
  - `POST /receipts/prepare` の追加。
  - `GET /products/search` の追加。
  - `POST /product-aliases` の追加。
- `app/schemas/`
  - prepare request / response schema の追加。
  - product search / alias response schema の追加。
  - 必要なら `ReceiptCreate` と prepare 出力の整合性調整。
- `tests/`
  - product key / alias model tests。
  - `resolve_product()` tests。
  - prepare API tests。
  - product search / alias learning API tests。
  - prepare 結果を `POST /receipts` に送れる integration tests。
  - `GET /prices/cheapest` が解決済み `product_id` 基準で動く integration tests。
- `docs/`
  - API spec と OCR/DB interface の prepare flow 追記。
  - OCR 側契約の最小更新内容の反映。

## 破壊的変更になりそうな箇所

- `products` に `name_key` を nullable false / unique で追加する場合。
  - 既存データがある DB では backfill が必要。
  - このリポジトリには Alembic 等の migration 管理は見当たらないため、既存 SQLite DB の扱いを明確にする必要がある。
- `product_aliases.raw_name` から `alias_name` / `alias_key` へ移行する場合。
  - 既存の `raw_name` unique 前提と、後続 milestone の `alias_key` unique 前提の差分がある。
  - 既存 alias データがある場合は `raw_name -> alias_name` と `alias_key` 生成が必要。
- `Product` 作成箇所。
  - tests と在庫/価格系の helper で `Product(name=..., default_base_unit=...)` を直接作っている。
  - `name_key` が必須になると既存 tests が一斉に更新対象になる。
- `ProductAlias` 作成箇所。
  - 現状 tests では大きく使われていないが、schema 変更後は alias 登録 tests が必要。
- `POST /receipts` の validation を強化する場合。
  - 現在は `product_id = null` を許可する。
  - MILESTONE05 までは、未解決 item を購入履歴として登録できる方針を維持する必要がある。
- `normalized_name` の意味。
  - 現状は request の値をそのまま保存する。
  - prepare で解決済みの場合に `products.name` へ置き換えると、OCR 候補名と正式商品名の扱いが分かれる。
- `GET /prices/cheapest`
  - 現状は `product_id` 基準でよいが、未解決 item は対象外になる。
  - prepare / alias 学習で product_id を埋める流れと結合テストが必要。

## テスト追加が必要な箇所

- `products.name_key` が作成でき、unique であること。
- `product_aliases.alias_key` が作成でき、unique であること。
- `normalize_product_key()` の表記ゆれ吸収。
- `resolve_product()` の解決順序。
  - 明示 `product_id`
  - `raw_name` alias
  - `normalized_name` alias
  - `products.name_key`
  - 未解決
  - 不正 `product_id`
- `POST /receipts/prepare`
  - OCR JSON を受け取れること。
  - OCR 専用項目を DB 登録用 `receipt` から除外すること。
  - 解決済み item に `product_id`, `normalized_name`, `category_id`, `base_unit` が反映されること。
  - 未解決 item は `product_id = null` として返ること。
  - 不正日付や登録時に問題になる項目を `validation_issues` に返すこと。
- `GET /products/search`
  - `products.name_key` と `product_aliases.alias_key` から検索できること。
- `POST /product-aliases`
  - 新規登録。
  - 同じ `alias_key` と同じ `product_id` の再登録。
  - 同じ `alias_key` と別 `product_id` の conflict。
  - 存在しない `product_id`。
- prepare 結果を `POST /receipts` に送れること。
- 未解決 `product_id = null` の item も `POST /receipts` で保存できること。
- 解決済み `product_id` で登録後、`GET /prices/cheapest` が同一 product の最安店を返すこと。

## Migration 管理の有無

- `pyproject.toml` に Alembic 依存はない。
- `alembic` ディレクトリや migration ファイルは確認できなかった。
- 現状は `Base.metadata.create_all()` による SQLite テーブル作成が中心。

## 実装時に注意すべき点

- この milestone では新 API / 新テーブル / schema 変更は実装しない。
- 後続 milestone では、既存の `product_id = null` 許容を壊さない。
- OCR の `normalized_name` は正式名ではなく候補として扱う。
- `GET /prices/cheapest` は `normalized_name` ではなく `product_id` 基準を維持する。
- migration 管理がないため、既存 `receipts.db` の扱いは作業前に確認する。
