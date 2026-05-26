# レシート・家計簿・在庫データベース API

このリポジトリは、ユーザー確認済みのレシート購入履歴を保存する FastAPI バックエンドです。

OCR API ではありません。画像アップロード、OCR 処理、OCR 仮データ保存、認証、ユーザー管理、世帯管理、レシピ提案 API はこのリポジトリでは扱いません。

```text
OCR 結果 = 仮データ
DB 登録データ = ユーザー確認済みデータ
```

OCR 連携では、OCR API のレスポンスを直接 `POST /receipts` に登録しません。フロントエンドはまず OCR 仮データを `POST /receipts/prepare` に送り、DB 側で日付変換、不要項目除去、`product_id` 解決、カテゴリ補完、数量確認課題の付与を行います。その結果を確認画面でユーザーが修正・確認した後、確定データだけを `POST /receipts` で保存します。

```text
OCR API
  -> OCR 仮 JSON
  -> DB API POST /receipts/prepare
  -> フロントエンド確認画面
  -> DB API POST /receipts
  -> 必要に応じて POST /inventory/receipts/{receipt_id}/apply
  -> GET /prices/cheapest
```

OCR API は `product_id` や `category_id` を決めません。OCR の `normalized_name` は商品名候補であり、DB の正式な `products.name` と一致する保証はありません。DB 側では `products.name_key` と `product_aliases.alias_key` を使って表記揺れを吸収し、未解決の商品は確認画面でユーザーが選択して `POST /product-aliases` により学習させます。

## OCR・フロントエンド・データベースの詳細フロー

OCR から DB 保存までの責務は次のように分けます。

```text
レシート画像
  -> OCR API
      画像から文字、金額、日付、商品名候補を抽出する
      product_id / category_id / alias は決めない
      OCR 信頼度、警告、metadata は仮データとして返す
  -> フロントエンド
      OCR 仮データを受け取る
      そのまま POST /receipts へ送らず、POST /receipts/prepare へ送る
  -> DB API POST /receipts/prepare
      日付形式を YYYY-MM-DD から YYYYMMDD へ変換する
      OCR 専用項目を登録用 receipt から除外する
      raw_name / normalized_name を products と product_aliases に照合する
      product_id と category_id を補完する
      base_quantity / base_unit の補完可否を判定する
      未解決明細と確認課題を返す
  -> フロントエンド確認画面
      ユーザーが購入日、店舗名、合計、明細、カテゴリ、在庫数量を確認する
      未解決商品は既存商品から選ぶ、または商品を新規作成する
      ユーザー確認済みの表記揺れを POST /product-aliases で学習させる
  -> DB API POST /receipts
      ユーザー確認済みデータだけを保存する
      items_total と adjustment_amount をサーバー側で計算する
  -> 必要に応じて在庫・価格比較・レシピ提案で利用する
```

### OCR API の役割

OCR API は、画像から読み取れた値を仮データとして返します。

OCR API が返してよいもの:

```text
store_name
purchased_at
total_amount
raw_name
normalized_name 候補
category_name 候補
purchased_quantity / purchased_unit
base_quantity / base_unit 候補
unit_price
line_total
is_inventory_target 候補
confidence
warnings
ocr_metadata
```

OCR API が決めないもの:

```text
product_id
category_id
product_aliases
products.name
products.default_base_unit
```

`confidence`、`warnings`、`ocr_metadata` は確認や自動登録可否の判断材料です。確定レシートの保存データとしては扱いません。

### POST /receipts/prepare の役割

`POST /receipts/prepare` は OCR 仮データを DB 登録前の確認用データへ変換します。この API はレシートを保存しません。

主な変換:

| 入力 | prepare 後 |
| --- | --- |
| `purchased_at: "2026-05-12"` | `purchased_at: 20260512` |
| `confidence`, `warnings`, `ocr_metadata` | 登録用 `receipt` から除外 |
| OCR の `normalized_name` | 商品解決できた場合は `products.name` に寄せる |
| `category_name` | 解決できる場合は `category_id` に変換 |
| `raw_name` / `normalized_name` | `product_id` 解決に使う |
| `purchased_quantity` / `purchased_unit` | `base_quantity` / `base_unit` 補完に使う |

商品解決では、次のキーを使います。

```text
products.name_key
product_aliases.alias_key
```

解決できた明細は `item_resolutions[].resolution_status = "resolved"` になり、`product_id` と正式な `product_name` が返ります。解決できない明細は `product_id = null` のまま `unresolved_items` に含まれます。

### product_aliases の役割

`product_aliases` は、レシート上の表記や OCR が出した表記を商品マスタへ対応させるテーブルです。

例:

| レシート/OCR 上の表記 `alias_name` | 照合用 `alias_key` | 商品マスタ `products.name` |
| --- | --- | --- |
| `タマゴM 10コ` | `たまごm10こ` | `卵` |
| `白たまご` | `白たまご` | `卵` |
| `牛乳1000ml` | `牛乳1000ml` | `牛乳` |
| `絹とうふ 300g` | `絹とうふ300g` | `豆腐` |

`alias_key` は検索・照合用に正規化したキーです。空白や表記揺れを吸収し、同じ別名を同じ商品に結びつけるために使います。

alias の `source` は自動解決に使えるかどうかを分けます。

| source | 自動解決 | 候補検索 | 用途 |
| --- | --- | --- | --- |
| `user_confirmed` | 可 | 可 | ユーザーが確認画面で選択した対応 |
| `seed` | 可 | 可 | 初期データ・テストデータとして安全に登録した対応 |
| `admin` | 可 | 可 | 管理者が確認して登録した対応 |
| `ocr_suggested` | 不可 | 可 | OCR や AI が推定しただけの候補 |

`POST /receipts/prepare` の自動解決では、`is_active = true` かつ `source` が `user_confirmed`、`seed`、`admin` の alias だけを使います。`ocr_suggested` は候補として表示できますが、ユーザー確認なしに `resolved` にはしません。`is_active = false` の alias は自動解決にも候補検索にも使いません。

未解決商品をユーザーが確認した場合、フロントエンドは次の順で対応します。

```text
1. GET /products/search で既存商品を探す
2. 商品があれば、ユーザーが商品を選択する
3. 商品がなければ、POST /products で商品マスタを作る
4. 確認した raw_name を POST /product-aliases で product_id に紐づける
5. 次回以降の POST /receipts/prepare では alias から自動解決される
```

同じ `alias_key` が同じ `product_id` に登録済みなら冪等に成功します。別の `product_id` に紐づいている場合は `409 Conflict` になり、誤った表記学習を防ぎます。

### フロントエンド確認画面の役割

フロントエンド確認画面では、`POST /receipts/prepare` の `receipt` を編集対象にします。OCR の元レスポンスを直接編集・登録するのではなく、DB API が返した確認用データを基準にします。

最低限確認する項目:

```text
購入日 purchased_at
店舗名 store_name
合計金額 total_amount
レシート上の商品名 raw_name
アプリ内の商品名 normalized_name
商品マスタ product_id
カテゴリ category_id
購入時数量 purchased_quantity
購入時単位 purchased_unit
共通数量 base_quantity
共通単位 base_unit
単価 unit_price
明細行合計 line_total
在庫対象 is_inventory_target
```

在庫対象の明細では、次の項目が確定してから `POST /receipts` へ送ります。

```text
normalized_name
base_quantity
base_unit
```

`product_id` は MVP では nullable ですが、最安店表示や安定した在庫・レシピ連携には重要です。可能な限り確認画面で既存商品に紐づけ、必要に応じて alias を登録します。

### POST /receipts の役割

`POST /receipts` はユーザー確認済みデータだけを保存します。OCR 信頼度や警告、OCR metadata は保存対象ではありません。

保存時にサーバーが計算する値:

```text
items_total = sum(line_total)
adjustment_amount = total_amount - items_total
```

`total_amount == items_total` は必須にしません。実レシートでは、割引、ポイント、税、レジ袋、OCR 漏れなどで差額が発生するためです。

保存されたデータは次のように使われます。

| 利用先 | 主に使う項目 |
| --- | --- |
| 家計簿 | `purchased_at`, `store_name`, `total_amount`, `items_total`, `adjustment_amount`, `category_id` |
| 在庫管理 | `product_id`, `normalized_name`, `base_quantity`, `base_unit`, `is_inventory_target` |
| 価格比較 | `product_id`, `store_name`, `line_total`, `base_quantity`, `base_unit` |
| AI レシピ提案 | 在庫 API から取得できる商品名、数量、単位、期限 |

価格比較の `GET /prices/cheapest` は、`receipt_items.product_id` が一致する履歴を対象にします。`product_id` が未解決の明細は購入履歴として保存できますが、商品別の最安店検索には使えません。

## 責務

この API は、家計簿、在庫管理、AI レシピ提案などの外部機能が共通で使える購入履歴と在庫情報を提供します。

| 利用先 | この API が提供するデータ |
| --- | --- |
| 家計簿 | 購入日、店舗名、カテゴリ、支払額、明細合計、差額 |
| 在庫管理 | 商品、数量、単位、保管場所、期限、在庫増減履歴 |
| 価格比較 | 商品ごとの共通単位あたり価格と最安購入店舗 |
| AI レシピ提案 | 在庫 API から取得できる商品名、数量、単位、期限 |

料理 AI やレシピ提案自体は、この API の外側で実装します。AI 側は `GET /inventory/balances` や `GET /inventory/batches` のレスポンスを利用します。

## 実装済み機能

| 区分 | 内容 |
| --- | --- |
| レシート管理 | 登録、一覧、詳細、削除 |
| OCR 登録準備 | OCR 仮データの整形、商品解決、カテゴリ補完、登録前課題の返却 |
| OCR 自動登録ゲート | 安全条件を満たす OCR 仮データだけを自動保存 |
| 商品マスタ | 商品検索、商品作成、別名学習 |
| 明細管理 | 購入時の商品名・数量と、在庫/レシピ用の正規化名・共通単位を保存 |
| 価格比較 | 指定商品の過去購入履歴から共通単位あたり最安店舗を取得 |
| 在庫反映 | レシート明細を在庫ロットへ反映 |
| 在庫残量 | 商品単位の現在在庫を取得 |
| 在庫ロット | 購入日、期限、保管場所、残量、ステータスを管理 |
| 在庫増減 | 消費、廃棄、手動調整と履歴取得 |
| 運用指標 | 登録準備回数、未解決率、別名衝突数、未解決名上位を取得 |

## 使用技術

- Python 3.12+
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- pytest
- uv

## データ設計

詳細は `docs/DATABASE_DESIGN.md` と `docs/INVENTORY_IMPLEMENTATION_SPEC.md` を参照してください。

主なテーブル:

```text
receipts
receipt_items
accounting_categories
products
product_aliases
product_unit_conversions
receipt_prepare_metrics
receipt_prepare_unresolved_names
product_alias_conflict_events
inventory_locations
inventory_batches
inventory_operations
inventory_movements
```

レシート明細では、購入時の表記とアプリ内で扱う共通単位を分けます。

```text
raw_name              レシート上の商品名
normalized_name       アプリ内で扱う商品名
purchased_quantity    購入時の数量
purchased_unit        購入時の単位
base_quantity         在庫・レシピ用に変換した数量
base_unit             在庫・レシピ用の共通単位
```

例:

```json
{
  "raw_name": "卵 1パック",
  "normalized_name": "卵",
  "purchased_quantity": 1,
  "purchased_unit": "パック",
  "base_quantity": 10,
  "base_unit": "個"
}
```

`store_name` は NULL を許可します。OCR で店名が取れない場合や、ユーザーが空欄で確定する場合を許容します。

## セットアップ

```bash
uv sync
```

必要に応じて仮想環境を有効化します。

```bash
source .venv/bin/activate
```

## 起動

```bash
uv run uvicorn app.main:app --reload
```

既定の URL:

```text
http://localhost:8000
```

開発環境では `http://localhost:5173` からの CORS を許可しています。

FastAPI の自動ドキュメント:

```text
http://localhost:8000/docs
http://localhost:8000/redoc
```

## API 一覧

| メソッド | パス | 概要 |
| --- | --- | --- |
| `GET` | `/` | ヘルスチェック |
| `POST` | `/receipts/prepare` | OCR 仮データを DB 登録前の確認用データへ整形 |
| `POST` | `/receipts/auto-create` | OCR 仮データを安全条件つきで自動登録 |
| `POST` | `/receipts` | ユーザー確認済みレシートを登録 |
| `GET` | `/receipts` | レシート一覧 |
| `GET` | `/receipts/{receipt_id}` | レシート詳細 |
| `DELETE` | `/receipts/{receipt_id}` | レシート削除 |
| `GET` | `/products/search` | 商品マスタ検索 |
| `POST` | `/products` | 商品マスタ作成 |
| `POST` | `/product-aliases` | 商品別名登録 |
| `GET` | `/prices/cheapest` | 商品の最安購入店舗取得 |
| `POST` | `/inventory/receipts/{receipt_id}/apply` | レシート明細を在庫へ反映 |
| `GET` | `/inventory/balances` | 在庫残量一覧 |
| `GET` | `/inventory/batches` | 在庫ロット一覧 |
| `POST` | `/inventory/movements` | 在庫増減登録 |
| `GET` | `/inventory/movements` | 在庫増減履歴 |
| `GET` | `/operations/receipt-prepare-metrics` | OCR 登録準備と別名学習の運用指標 |

## API 詳細

### GET /

ヘルスチェックです。

レスポンス:

```json
{
  "status": "ok"
}
```

### POST /receipts/prepare

OCR レスポンスに近い JSON を受け取り、DB 登録前の確認画面で扱いやすい `receipt` オブジェクトへ整形します。この API はレシートを保存しません。

主な処理:

- `purchased_at: "YYYY-MM-DD"` を `YYYYMMDD` の整数に変換
- OCR 専用の `status`、`confidence`、明細内の `warnings`、`ocr_metadata` を登録用 `receipt` から除外
- `raw_name` / `normalized_name` と `product_aliases` / `products` から `product_id` を解決
- 解決できた場合は `normalized_name` を `products.name` に寄せる
- `products.default_category_id` から `category_id` を補完
- 商品別単位変換が可能な場合は `base_quantity` / `base_unit` を補完
- 未解決または確認が必要な明細を `unresolved_items` と `item_resolutions[].issues` に返す
- 登録準備の集約指標を保存する

リクエスト:

```json
{
  "status": "needs_confirmation",
  "store_name": "サンプルスーパー",
  "purchased_at": "2026-05-12",
  "total_amount": 238,
  "items": [
    {
      "raw_name": "タマゴM 10コ",
      "normalized_name": "たまご",
      "category_name": "食費",
      "purchased_quantity": 1,
      "purchased_unit": "パック",
      "base_quantity": 10,
      "base_unit": "個",
      "unit_price": 238,
      "line_total": 238,
      "is_inventory_target": true,
      "confidence": 0.82,
      "warnings": [],
      "ocr_metadata": {
        "auto_register_candidate": true,
        "needs_review_reasons": []
      }
    }
  ],
  "warnings": []
}
```

レスポンス:

```json
{
  "receipt": {
    "store_name": "サンプルスーパー",
    "purchased_at": 20260512,
    "total_amount": 238,
    "items": [
      {
        "raw_name": "タマゴM 10コ",
        "normalized_name": "卵",
        "product_id": 1,
        "category_id": 1,
        "purchased_quantity": "1.00",
        "purchased_unit": "パック",
        "base_quantity": "10.00",
        "base_unit": "個",
        "unit_price": 238,
        "line_total": 238,
        "is_inventory_target": true
      }
    ]
  },
  "item_resolutions": [
    {
      "index": 0,
      "resolution_status": "resolved",
      "resolution_source": "raw_name_alias",
      "product_id": 1,
      "product_name": "卵",
      "product_candidates": [],
      "issues": []
    }
  ],
  "unresolved_items": [],
  "warnings": [],
  "validation_issues": []
}
```

代表的な課題:

| 課題コード | 意味 |
| --- | --- |
| `product_not_resolved` | 商品マスタに解決できない |
| `unit_conversion_missing` | 商品別変換が必要だが、`product_unit_conversions` に該当行がない |
| `ambiguous_quantity` | 単位だけでは共通数量を決められない |
| `base_quantity_missing` | 在庫対象なのに `base_quantity` が空 |
| `base_unit_missing` | 在庫対象なのに `base_unit` が空 |
| `inventory_target_without_base_quantity` | 後方互換用。`base_quantity_missing` と併せて返る |
| `inventory_target_without_base_unit` | 後方互換用。`base_unit_missing` と併せて返る |

数量確認が必要な明細がある場合、`validation_issues` には `inventory_items_require_quantity_confirmation` が入ります。確認画面ではユーザーが `base_quantity` / `base_unit` を修正してから `POST /receipts` へ送ります。

### POST /receipts/auto-create

`POST /receipts/prepare` と同じ整形・解決を行ったうえで、自動登録してよい条件を満たす場合だけレシートを保存します。条件を満たさない場合は保存せず、確認画面に回せるレスポンスを返します。

リクエストは `POST /receipts/prepare` と同じ構造に `auto_register_enabled` を追加します。

```json
{
  "auto_register_enabled": true,
  "status": "needs_confirmation",
  "store_name": "サンプルスーパー",
  "purchased_at": "2026-05-12",
  "total_amount": 238,
  "items": [
    {
      "raw_name": "タマゴM 10コ",
      "normalized_name": "たまご",
      "purchased_quantity": 1,
      "purchased_unit": "パック",
      "base_quantity": 10,
      "base_unit": "個",
      "unit_price": 238,
      "line_total": 238,
      "is_inventory_target": true,
      "confidence": 0.95,
      "warnings": []
    }
  ],
  "warnings": []
}
```

自動登録する条件:

```text
auto_register_enabled が true
validation_issues が空
unresolved_items が空
OCR 全体の warnings が空
各明細の warnings が空
各明細の confidence が 0.85 以上
各 `item_resolutions[].issues` が空
各 `item_resolutions[].resolution_status` が `resolved`
購入日、合計金額、明細が揃っている
各明細の raw_name / purchased_quantity / line_total / is_inventory_target が揃っている
在庫対象明細は product_id / normalized_name / base_quantity / base_unit が揃っている
OCR メタデータが確認理由を要求していない
total_amount と line_total 合計が一致する
```

レスポンス例: 登録された場合

```json
{
  "created": true,
  "receipt_id": 1,
  "summary": {
    "id": 1,
    "purchased_at": 20260512,
    "store_name": "サンプルスーパー",
    "total_amount": 238,
    "items_total": 238,
    "adjustment_amount": 0,
    "item_count": 1
  },
  "receipt": {
    "store_name": "サンプルスーパー",
    "purchased_at": 20260512,
    "total_amount": 238,
    "items": []
  },
  "item_resolutions": [],
  "unresolved_items": [],
  "warnings": [],
  "validation_issues": [],
  "auto_registration": {
    "eligible": true,
    "reasons": [],
    "min_item_confidence": 0.85
  }
}
```

レスポンス例: 登録されなかった場合

```json
{
  "created": false,
  "receipt_id": null,
  "summary": null,
  "receipt": {
    "store_name": "サンプルスーパー",
    "purchased_at": 20260512,
    "total_amount": 238,
    "items": []
  },
  "item_resolutions": [],
  "unresolved_items": [],
  "warnings": [],
  "validation_issues": [],
  "auto_registration": {
    "eligible": false,
    "reasons": [
      "auto_registration_disabled"
    ],
    "min_item_confidence": 0.85
  }
}
```

### POST /receipts

フロントエンドでユーザー確認が完了したレシートだけを登録します。

リクエスト:

```json
{
  "purchased_at": 20260512,
  "store_name": "サンプルスーパー",
  "total_amount": 636,
  "items": [
    {
      "raw_name": "タマゴM 10コ",
      "normalized_name": "卵",
      "product_id": 1,
      "category_id": 1,
      "purchased_quantity": 1,
      "purchased_unit": "パック",
      "base_quantity": 10,
      "base_unit": "個",
      "unit_price": 238,
      "line_total": 238,
      "is_inventory_target": true
    }
  ]
}
```

必須項目:

| 対象 | 必須項目 |
| --- | --- |
| receipt | `purchased_at`, `total_amount`, `items` |
| item | `raw_name`, `purchased_quantity`, `line_total`, `is_inventory_target` |
| 在庫対象明細 | `normalized_name` または `product_id`, `base_quantity`, `base_unit` |

`items_total` と `adjustment_amount` はサーバー側で計算します。

```text
items_total = sum(line_total)
adjustment_amount = total_amount - items_total
```

レシートには割引、ポイント、税、レジ袋、OCR 漏れなどがあるため、`total_amount == items_total` は必須にしません。

レスポンス: `201`

```json
{
  "id": 1,
  "purchased_at": 20260512,
  "store_name": "サンプルスーパー",
  "total_amount": 636,
  "items_total": 636,
  "adjustment_amount": 0,
  "item_count": 1
}
```

### GET /receipts

レシート一覧を返します。

クエリパラメータ:

| 名前 | 型 | 必須 | 既定値 | 説明 |
| --- | --- | ---: | --- | --- |
| `skip` | 整数 | いいえ | `0` | 取得開始位置 |
| `limit` | 整数 | いいえ | `50` | 取得件数。`1` から `100` |
| `date_from` | 整数 | いいえ | - | 開始日。`YYYYMMDD` |
| `date_to` | 整数 | いいえ | - | 終了日。`YYYYMMDD` |
| `category_id` | 整数 | いいえ | - | カテゴリで絞り込み |
| `inventory_only` | 真偽値 | いいえ | `false` | 在庫対象明細を含むレシートに絞り込み |

レスポンス:

```json
[
  {
    "id": 1,
    "purchased_at": 20260512,
    "store_name": "サンプルスーパー",
    "total_amount": 636,
    "items_total": 636,
    "adjustment_amount": 0,
    "item_count": 1
  }
]
```

### GET /receipts/{receipt_id}

レシート詳細を返します。

レスポンス:

```json
{
  "id": 1,
  "purchased_at": 20260512,
  "store_name": "サンプルスーパー",
  "total_amount": 636,
  "items_total": 636,
  "adjustment_amount": 0,
  "items": [
    {
      "id": 1,
      "raw_name": "タマゴM 10コ",
      "normalized_name": "卵",
      "product_id": 1,
      "category_id": 1,
      "purchased_quantity": "1.00",
      "purchased_unit": "パック",
      "base_quantity": "10.00",
      "base_unit": "個",
      "unit_price": 238,
      "line_total": 238,
      "is_inventory_target": true
    }
  ]
}
```

存在しない `receipt_id` は `404` です。

### DELETE /receipts/{receipt_id}

レシートを削除します。`receipt_items` は連動して削除されます。

レスポンス:

```json
{
  "deleted": true,
  "id": 1
}
```

存在しない `receipt_id` は `404` です。

### GET /products/search

未解決商品に対して、フロントエンドが商品候補を検索します。検索には `products.name_key` と `product_aliases.alias_key` を使います。

クエリパラメータ:

| 名前 | 型 | 必須 | 既定値 | 説明 |
| --- | --- | ---: | --- | --- |
| `query` | 文字列 | はい | - | 検索語 |
| `limit` | 整数 | いいえ | `10` | 取得件数。`1` から `50` |

レスポンス:

```json
{
  "query": "タマゴ",
  "query_key": "たまご",
  "items": [
    {
      "product_id": 1,
      "name": "卵",
      "default_base_unit": "個",
      "default_category_id": 1,
      "is_inventory_target": true
    }
  ]
}
```

`query` が空白だけの場合は `400` です。

### POST /products

確認画面で商品候補が存在しない場合に、商品マスタを新規作成します。`name_key` は API 利用者が入力せず、サーバー側で `name` から生成します。

リクエスト:

```json
{
  "name": "豆腐",
  "default_base_unit": "g",
  "is_inventory_target": true,
  "default_category_id": 1,
  "initial_alias_name": "絹とうふ 300g",
  "alias_source": "user_confirmed"
}
```

| 名前 | 型 | 必須 | 説明 |
| --- | --- | ---: | --- |
| `name` | 文字列 | はい | 商品マスタ名。空白だけは不可 |
| `default_base_unit` | 文字列 | はい | 在庫・レシピで使う標準単位。空白だけは不可 |
| `is_inventory_target` | 真偽値 | はい | 通常在庫対象にするか |
| `default_category_id` | 整数 | いいえ | 既定カテゴリ。指定された場合は存在確認する |
| `initial_alias_name` | 文字列 | いいえ | 確認画面で元になった `raw_name` を別名登録する |
| `alias_source` | 文字列 | いいえ | `initial_alias_name` の登録元。既定値は `user_confirmed` |

レスポンス: `201`

```json
{
  "id": 1,
  "name": "豆腐",
  "name_key": "豆腐",
  "default_base_unit": "g",
  "default_category_id": 1,
  "is_inventory_target": true,
  "created_alias": {
    "id": 10,
    "alias_name": "絹とうふ 300g",
    "alias_key": "絹とうふ300g",
    "product_id": 1,
    "source": "user_confirmed"
  }
}
```

`initial_alias_name` がない場合、`created_alias` は `null` です。存在しないカテゴリは `404`、同じ `name_key` の商品は `409`、`initial_alias_name` が別商品の別名と衝突した場合も `409` です。

### POST /product-aliases

ユーザーが確認した OCR 名やレシート表記と商品マスタの対応を `product_aliases` に保存します。

リクエスト:

```json
{
  "alias_name": "タマゴM 10コ",
  "product_id": 1,
  "source": "user_confirmed"
}
```

`source` の既定値は `user_confirmed` です。許可値:

| 登録元 | 自動解決 | 候補検索 | 説明 |
| --- | --- | --- | --- |
| `user_confirmed` | 可 | 可 | ユーザーが確認画面で選択した別名 |
| `seed` | 可 | 可 | 初期データ・テストデータとして安全に登録した別名 |
| `admin` | 可 | 可 | 管理者が確認して登録した別名 |
| `ocr_suggested` | 不可 | 可 | OCR や AI が推定しただけの別名 |

レスポンス:

```json
{
  "id": 1,
  "alias_name": "タマゴM 10コ",
  "alias_key": "たまごm10こ",
  "product_id": 1,
  "product_name": "卵",
  "source": "user_confirmed",
  "created": true
}
```

同じ `alias_key` が同じ `product_id` に登録済みなら冪等に成功し、`created: false` を返します。別 `product_id` に登録済みなら `409` です。存在しない `product_id` は `404`、空白だけの `alias_name` や許可されていない `source` は `400` です。

### GET /prices/cheapest

指定した `product_id` の購入履歴から、最安購入店舗を返します。

クエリパラメータ:

| 名前 | 型 | 必須 | 既定値 | 説明 |
| --- | --- | ---: | --- | --- |
| `product_id` | 整数 | はい | - | 商品 ID |
| `period_days` | 整数 | いいえ | `90` | 過去何日を対象にするか |

比較式:

```text
price_per_base_unit = line_total / base_quantity
```

対象外になる明細:

- `product_id` が一致しない
- `base_quantity` が `null` または `0` 以下
- `base_unit` が `null`
- `receipts.store_name` が `null`
- `purchased_at` が `period_days` の範囲外

レスポンス:

```json
{
  "product_id": 1,
  "product_name": "卵",
  "period_days": 90,
  "cheapest": {
    "store_name": "サンプルスーパー",
    "price_per_base_unit": 23.8,
    "line_total": 238,
    "base_quantity": "10.00",
    "base_unit": "個",
    "purchased_at": 20260512,
    "receipt_item_id": 31
  }
}
```

該当データがない場合:

```json
{
  "product_id": 1,
  "product_name": "卵",
  "period_days": 90,
  "cheapest": null
}
```

存在しない `product_id` は `404` です。

### POST /inventory/receipts/{receipt_id}/apply

`is_inventory_target = true` で、`product_id`、`base_quantity`、`base_unit` がそろっているレシート明細を在庫ロットへ反映します。同じレシート明細は二重に在庫化しません。

リクエスト:

```json
{
  "default_location_id": 1,
  "expires_at_by_receipt_item_id": {
    "31": "2026-05-20"
  },
  "idempotency_key": "receipt:12:apply-inventory"
}
```

レスポンス:

```json
{
  "receipt_id": 12,
  "operation_id": 100,
  "applied_count": 1,
  "skipped_count": 0,
  "items": [
    {
      "receipt_item_id": 31,
      "product_id": 1,
      "product_name": "卵",
      "quantity": "10.00",
      "unit": "個",
      "batch_id": 201,
      "status": "applied",
      "reason": null
    }
  ]
}
```

主なスキップ理由:

| 理由コード | 意味 |
| --- | --- |
| `not_inventory_target` | 在庫対象ではない |
| `missing_product_or_base_quantity` | `product_id`、`base_quantity`、`base_unit` のいずれかが不足、または `base_quantity <= 0` |
| `already_applied` | 既に在庫ロットへ反映済み |

存在しない `receipt_id` は `404`、存在しない `default_location_id` は `400` です。

### GET /inventory/balances

商品・単位ごとの現在在庫を返します。

クエリパラメータ:

| 名前 | 型 | 必須 | 既定値 | 説明 |
| --- | --- | ---: | --- | --- |
| `product_id` | 整数 | いいえ | - | 商品で絞り込み |
| `location_id` | 整数 | いいえ | - | 保管場所で絞り込み |
| `include_zero` | 真偽値 | いいえ | `false` | 残量 0 の在庫も含める |

レスポンス:

```json
{
  "items": [
    {
      "product_id": 1,
      "product_name": "卵",
      "quantity": "16.00",
      "unit": "個",
      "nearest_expires_at": "2026-05-20",
      "batch_count": 2
    }
  ]
}
```

### GET /inventory/batches

在庫ロット一覧を返します。

クエリパラメータ:

| 名前 | 型 | 必須 | 既定値 | 説明 |
| --- | --- | ---: | --- | --- |
| `product_id` | 整数 | いいえ | - | 商品で絞り込み |
| `location_id` | 整数 | いいえ | - | 保管場所で絞り込み |
| `status` | 文字列 | いいえ | - | `active` / `depleted` / `discarded` |
| `expires_before` | 日付 | いいえ | - | 指定日以前に期限が来るもの |
| `include_zero` | 真偽値 | いいえ | `false` | 残量 0 の在庫も含める |

レスポンス:

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

無効な `status` は `400` です。

### POST /inventory/movements

在庫の消費、廃棄、手動調整を登録します。

`movement_type` は `consume`、`dispose`、`adjust` を受け取ります。`batch_id` を指定しない消費・廃棄では、期限が近いロットから順に差し引きます。`adjust` で正の数量を指定した場合は手動追加ロットを作成します。

リクエスト:

```json
{
  "product_id": 1,
  "movement_type": "consume",
  "quantity": "2.00",
  "unit": "個",
  "batch_id": null,
  "location_id": null,
  "reason": "夕食で使用",
  "occurred_at": "2026-05-13T18:30:00",
  "idempotency_key": "manual:consume:egg:20260513-001"
}
```

レスポンス:

```json
{
  "operation_id": 101,
  "movement_type": "consume",
  "product_id": 1,
  "product_name": "卵",
  "requested_quantity": "2.00",
  "unit": "個",
  "movements": [
    {
      "movement_id": 301,
      "batch_id": 201,
      "quantity_delta": "-2.00",
      "remaining_quantity": "8.00"
    }
  ]
}
```

存在しない `product_id` / `batch_id` は `404` です。単位不一致、存在しない `location_id`、在庫不足、対象外ロット指定は `400` です。

### GET /inventory/movements

在庫増減履歴を返します。

クエリパラメータ:

| 名前 | 型 | 必須 | 既定値 | 説明 |
| --- | --- | ---: | --- | --- |
| `product_id` | 整数 | いいえ | - | 商品で絞り込み |
| `batch_id` | 整数 | いいえ | - | 在庫ロットで絞り込み |
| `operation_id` | 整数 | いいえ | - | 操作単位で絞り込み |
| `movement_type` | 文字列 | いいえ | - | 増減種別で絞り込み |
| `from_date` | 日付 | いいえ | - | 発生日の開始日 |
| `to_date` | 日付 | いいえ | - | 発生日の終了日 |
| `limit` | 整数 | いいえ | `100` | 取得件数。`1` から `500` |
| `offset` | 整数 | いいえ | `0` | 取得開始位置 |

レスポンス:

```json
{
  "items": [
    {
      "movement_id": 301,
      "operation_id": 101,
      "batch_id": 201,
      "product_id": 1,
      "product_name": "卵",
      "movement_type": "consume",
      "quantity_delta": "-2.00",
      "unit": "個",
      "reason": "夕食で使用",
      "occurred_at": "2026-05-13T18:30:00"
    }
  ]
}
```

### GET /operations/receipt-prepare-metrics

`POST /receipts/prepare` と別名学習の最小限の運用指標を返します。この API のために保存するのは集約情報だけです。OCR 生 JSON、価格、店舗名、購入日、全明細は保存しません。

クエリパラメータ:

| 名前 | 型 | 必須 | 既定値 | 説明 |
| --- | --- | ---: | --- | --- |
| `top_limit` | 整数 | いいえ | `10` | 未解決名上位の件数。`1` から `50` |

レスポンス:

```json
{
  "prepare_count": 120,
  "total_item_count": 640,
  "unresolved_item_count": 38,
  "unresolved_rate": 0.059375,
  "alias_count": 82,
  "active_alias_count": 80,
  "alias_conflict_count": 3,
  "inventory_base_quantity_missing_count": 11,
  "top_unresolved_raw_names": [
    {
      "raw_name": "タマゴM 10コ",
      "raw_name_key": "たまごm10こ",
      "count": 9
    }
  ]
}
```

`unresolved_rate` は `unresolved_item_count / total_item_count` で計算します。`total_item_count = 0` の場合は `0` を返します。

## 確認画面での商品紐づけフロー

フロントエンドは OCR 結果を直接 `POST /receipts` へ送らず、次の順でユーザー確認済みデータを作ります。

```text
1. OCR 結果を POST /receipts/prepare に送る
2. 未解決商品の product_candidates を確認画面に表示する
3. 候補が足りない場合は GET /products/search?query=... で商品名または別名から検索する
4. 候補が存在しない場合は POST /products で商品を作成し、必要なら raw_name を initial_alias_name として登録する
5. 既存商品を選んだ場合は OCR 由来の raw_name を POST /product-aliases で product_aliases に登録する
6. 確認済みの receipt を POST /receipts で保存する
```

`raw_name` はレシート上の表記であり、最優先の別名学習対象です。

`normalized_name` は OCR や AI が推定した候補であり、DB 正式名とは限りません。そのため `POST /receipts/prepare` は `normalized_name` を自動で別名登録しません。`normalized_name` を別名として登録したい場合は、ユーザーが明示的に確認した値を `POST /product-aliases` の `alias_name` として送ります。

## バリデーション

| 条件 | ステータス |
| --- | ---: |
| 型や形式が不正 | 422 |
| `items` が空 | 422 |
| `purchased_at` が実在しない日付 | 422 |
| `total_amount` が 0 未満 | 422 |
| `raw_name` が空 | 422 |
| `purchased_quantity` が 0 以下 | 422 |
| `line_total` が 0 未満 | 422 |
| `is_inventory_target = true` なのに `normalized_name` と `product_id` がどちらも空 | 422 |
| `is_inventory_target = true` なのに `base_quantity` または `base_unit` が空 | 422 |
| 形式は正しいが業務ルールに反する | 400 |
| 存在しない `receipt_id` | 404 |
| 存在しない `product_id` または `category_id` | 400 または 404。API ごとの説明を参照 |

`unit_price * purchased_quantity == line_total` は必須にしません。

`total_amount == sum(line_total)` も必須にしません。ただし `POST /receipts/auto-create` の自動登録ゲートでは一致を要求します。

## エラー形式

FastAPI / Pydantic 標準の `422` はそのまま返します。業務エラーでは、API によって文字列または次の形式の `detail` を返します。

```json
{
  "detail": {
    "code": "invalid_receipt",
    "message": "レシートデータが不正です"
  }
}
```

代表的なステータス:

| 状況 | ステータス |
| --- | ---: |
| 登録成功 | 201 |
| 取得成功 | 200 |
| 削除成功 | 200 |
| 型・形式が不正 | 422 |
| 形式は正しいが業務ルールに反する | 400 |
| 対象が存在しない | 404 |
| 一意制約・別名衝突 | 409 |

## テスト

基本確認:

```bash
uv run python -m compileall app
```

テスト:

```bash
uv run pytest
```

利用可能なら実行:

```bash
uv run ruff check .
```

テストでは通常開発用の `receipts.db` を使わず、一時 SQLite DB に差し替えます。

## 開発時の注意

- 既存の `receipts.db` に実データが入っている可能性があるため、勝手に削除しないでください。
- Alembic は導入していません。
- 本番 DB 対応は未実装です。
- GitHub へのプッシュは行いません。
- ローカルコミットは利用者から明示された場合のみ行います。

## 関連ドキュメント

- `AGENTS.md`
- `docs/DATABASE_DESIGN.md`
- `docs/API_SPEC.md`
- `docs/OCR_DB_INTERFACE.md`
- `docs/CODEX_IMPLEMENTATION_PLAN.md`
- `docs/INVENTORY_IMPLEMENTATION_SPEC.md`
