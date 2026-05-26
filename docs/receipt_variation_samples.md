# レシート表記揺れサンプル

## 目的

後続テストで、OCRレシートの商品名・数量・単位の表記揺れを同じ期待値で使い回せるように整理する。

この文書と `database/tests/fixtures/receipt_variation_samples.py` はサンプル定義だけを扱う。商品解決ロジック、API、DBモデル、数量・単位変換ロジックは変更しない。

## 出所

今回追加するサンプルはすべて `docs/TODO.md` に記載された例、またはそこから明示された補完例である。そのため `sample_source` はすべて `provided_example` とする。

実レシート由来であることを確認できる値は今回含めていないため、`real_receipt` のサンプル数は 0 件である。

## フィールド

| フィールド | 説明 |
| --- | --- |
| `sample_source` | `provided_example`, `real_receipt`, `test_seed` のいずれか |
| `raw_name` | OCRまたはレシート上の商品名 |
| `normalized_name` | OCR側が推定した商品名。ない場合は `None` |
| `purchased_quantity` | 購入時数量。ない場合は `None` |
| `purchased_unit` | 購入時単位。ない場合は `None` |
| `expected_product_name` | 期待する商品マスタ名。固定 `product_id` は持たせない |
| `expected_base_quantity` | 期待する共通数量。自動補完しない場合は `None` |
| `expected_base_unit` | 期待する共通単位。自動補完しない場合は `None` |
| `auto_resolve_allowed` | 商品名から `product_id` を自動解決してよいか |
| `needs_user_confirmation` | 商品名または数量・単位の確認が必要か |
| `reason` | 判断理由 |

## サンプル一覧

| sample_source | raw_name | normalized_name | purchased_quantity | purchased_unit | expected_product_name | expected_base_quantity | expected_base_unit | auto_resolve_allowed | needs_user_confirmation | reason |
| --- | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- |
| provided_example | タマゴ | None | None | None | 卵 | None | None | true | false | 信頼できるactive aliasが卵に完全一致する場合だけ自動解決できる商品名表記揺れ。 |
| provided_example | 卵 | None | None | None | 卵 | None | None | true | false | products.name_keyに完全一致するため自動解決できる。 |
| provided_example | たまご | None | None | None | 卵 | None | None | true | false | 信頼できるactive aliasが卵に完全一致する場合だけ自動解決できる商品名表記揺れ。 |
| provided_example | 玉子 | None | None | None | 卵 | None | None | true | false | 信頼できるactive aliasが卵に完全一致する場合だけ自動解決できる商品名表記揺れ。 |
| provided_example | タマゴM 10コ | None | 10 | 個 | 卵 | None | None | false | true | 商品名にサイズと数量が混在しており、信頼済みaliasなしでは候補提示に留める。 |
| provided_example | 卵 1パック | 卵 | 1 | パック | 卵 | 10 | 個 | true | false | 卵を解決後、商品別変換 1パック=10個 があればbase_quantityを補完できる。 |
| provided_example | 卵 2個 | 卵 | 2 | 個 | 卵 | 2 | 個 | true | false | 卵を解決後、購入単位と標準単位が同じなのでそのまま補完できる。 |
| provided_example | 牛乳 1本 | 牛乳 | 1 | 本 | 牛乳 | 1000 | ml | true | false | 牛乳を解決後、商品別変換 1本=1000ml があればbase_quantityを補完できる。 |
| provided_example | 牛乳 1000ml | 牛乳 | 1000 | ml | 牛乳 | 1000 | ml | true | false | 牛乳を解決後、購入単位と標準単位が同じなのでそのまま補完できる。 |
| provided_example | 牛乳 1L | 牛乳 | 1 | L | 牛乳 | 1000 | ml | true | false | 牛乳を解決後、Lからmlへの変換があればbase_quantityを補完できる。 |
| provided_example | 米 1kg | 米 | 1 | kg | 米 | 1000 | g | true | false | 米を解決後、商品別変換 1kg=1000g があればbase_quantityを補完できる。 |
| provided_example | 豚肉 100g | 豚肉 | 100 | g | 豚肉 | 100 | g | true | false | 豚肉を解決後、購入単位と標準単位が同じなのでそのまま補完できる。 |
| provided_example | トマト 2個 | トマト | 2 | 個 | トマト | None | None | true | true | トマトは個数だけではg換算できないため、商品解決後もbase_quantityは自動補完しない。 |
| provided_example | 肉 1パック | 肉 | 1 | パック | 肉 | None | None | true | true | 肉の1パックは商品や店舗で重量が変わるため、g換算を推測せずユーザー確認に回す。 |

## 判断メモ

- `auto_resolve_allowed` は商品名から `product_id` を自動解決してよいかを表す。
- `needs_user_confirmation` は商品名解決だけでなく、数量・単位変換を含めた確認要否を表す。
- `タマゴM 10コ` は期待商品名を `卵` とするが、サイズや数量を含む表記なので、信頼済みaliasがない状態では自動解決しない候補として扱う。
- `卵 1パック -> 10個`、`牛乳 1本 -> 1000ml`、`米 1kg -> 1000g` は、商品解決後に商品別変換がある場合だけ自動補完できる例である。
- `トマト 2個 -> g`、`肉 1パック -> g` は、単位だけでは量が決まらないため自動補完しない。
