# MILESTONE02: 商品名正規化関数とproduct_id解決ロジック

## Codex指示

```text
AGENTS.md、README.md、docs/miles/README.md、docs/miles/MILESTONE02_PRODUCT_NORMALIZATION_AND_RESOLUTION.md を読んでください。
このmileでは、商品名の表記揺れを吸収するための normalize_product_key() と resolve_product() をDB側に実装してください。
API追加はまだ行わないでください。
```

## 目的

OCRの `raw_name` や `normalized_name` が揺れても、DB側でできる限り `product_id` を解決できるようにする。

## 実装対象

DBリポジトリのみを変更する。
OCRリポジトリは変更しない。

## normalize_product_key()

商品名照合用のキーを作る関数を追加する。

配置例:

```text
app/common/product_key.py
```

関数名:

```python
def normalize_product_key(value: str | None) -> str | None:
    ...
```

推奨処理:

```text
NoneならNoneを返す
Unicode NFKC正規化
前後空白除去
全空白除去
英字小文字化
カタカナをひらがなへ寄せる
空文字ならNoneを返す
```

注意:

```text
数字を消さない
単位を消さない
意味推定をしない
AI APIを呼ばない
外部ライブラリを追加しない
```

理由:

`卵10個` と `卵6個` を雑に `卵` に寄せると危険である。
そのような対応は `product_aliases` に学習させる。

## resolve_product()

DBから `product_id` を解決する関数を追加する。

配置例:

```text
app/crud/products_resolver.py
```

入力例:

```python
@dataclass
class ProductResolutionInput:
    product_id: int | None
    raw_name: str | None
    normalized_name: str | None
```

出力例:

```python
@dataclass
class ProductResolutionResult:
    product_id: int | None
    product_name: str | None
    normalized_name: str | None
    default_category_id: int | None
    default_base_unit: str | None
    is_inventory_target: bool | None
    resolution_status: str
    resolution_source: str | None
    candidates: list[ProductCandidate]
```

`resolution_status` の候補:

```text
resolved
unresolved
invalid_product_id
```

`resolution_source` の候補:

```text
request_product_id
raw_name_alias
normalized_name_alias
normalized_name_product
candidate_only
none
```

## 解決順序

必ず以下の順序で解決する。

```text
1. product_id が指定されている場合、存在確認して有効ならそれを採用する
2. raw_name を normalize_product_key し、product_aliases.alias_key と完全一致検索する
3. normalized_name を normalize_product_key し、product_aliases.alias_key と完全一致検索する
4. normalized_name を normalize_product_key し、products.name_key と完全一致検索する
5. 候補検索を行う
6. 解決不能なら product_id = null のまま返す
```

## 自動決定してよい条件

自動で `resolved` にしてよいのは以下だけ。

```text
明示された product_id が存在する
alias_key に完全一致した
products.name_key に完全一致した
```

部分一致や候補検索だけでは自動決定しない。

## 候補検索

完全一致しない場合でも、フロントエンドでユーザーが選べるように候補を返す。

候補検索はMVPでは単純でよい。

```text
products.name_key LIKE %query_key%
または query_key LIKE %products.name_key%
```

候補は最大5件程度に制限する。

複数候補がある場合、自動決定しない。

## テスト

最低限、以下を追加する。

```text
normalize_product_key がNFKC正規化する
normalize_product_key が空白を除去する
normalize_product_key がカタカナとひらがなを寄せる
product_id 指定が最優先される
raw_name alias 完全一致で解決できる
normalized_name alias 完全一致で解決できる
products.name_key 完全一致で解決できる
候補検索だけでは自動resolvedにしない
解決不能なら product_id null で返る
存在しない product_id 指定なら invalid_product_id になる
```

## 非ゴール

このmileでは以下を実装しない。

```text
POST /receipts/prepare
GET /products/search
POST /product-aliases
POST /receipts の仕様変更
OCR側修正
```

## 実行コマンド

```bash
uv run python -m compileall app
uv run pytest
```

## 完了報告

以下を報告する。

```text
変更したファイル:
追加した関数:
resolve_product の解決順序:
追加・更新したテスト:
実行したコマンド:
テスト結果:
残TODO:
```
