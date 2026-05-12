# OCR Project Specification

## 概要

このプロジェクトは、レシート画像を読み取り、フロントエンド確認用の仮レシートデータを返す OCR API である。

レシート OCR の結果は、ユーザーの確認・修正を受ける前の候補データである。そのため、このサービスは DB に直接保存しない。

## 目的

この OCR API の目的は次の通り。

```txt
レシート画像
  ↓
Gemini による画像読解
  ↓
OpenAI Structured Outputs による JSON 厳密化
  ↓
Pydantic による検証
  ↓
フロントエンド確認画面へ返却
```

## このプロジェクトが担当すること

- レシート画像の受け取り
- 画像形式とサイズの検証
- Gemini によるレシート画像読解
- OpenAI Structured Outputs による JSON 整形
- Pydantic によるレスポンス検証
- フロントエンド確認画面で使える仮データの返却
- API エラーの整理
- テストしやすい provider 分離

## このプロジェクトが担当しないこと

- DB 登録
- 家計簿データの確定保存
- 在庫反映
- レシピ提案
- 商品マスタとの ID 照合
- category_id の確定
- product_id の確定
- ユーザー認証
- 画像ファイルの永続保存

## 設計上の重要原則

OCR は誤読する可能性がある。したがって、OCR API の出力を確定データとして扱ってはいけない。

この API は、次の状態のデータだけを返す。

```txt
needs_confirmation
```

これは「ユーザー確認が必要」という意味である。

## 全体フロー

```txt
[Frontend]
  | multipart/form-data
  v
[OCR API]
  | validate file
  v
[Gemini Provider]
  | raw extraction text / JSON-like candidates
  v
[OpenAI Structured Provider]
  | strict JSON
  v
[Pydantic Validation]
  | validated response
  v
[Frontend Confirmation Screen]
```

## Gemini の役割

Gemini は、画像から読み取れる情報をできる限り抽出する役割を持つ。

Gemini の出力は信頼済みデータではない。Gemini の出力をそのまま API レスポンスとして返してはいけない。

Gemini には、次の情報を読み取らせる。

- 店舗名
- 購入日
- 合計金額
- 商品名
- 数量
- 単位
- 単価
- 明細金額
- 割引や税に関する行
- 読み取りにくい箇所

## OpenAI Structured Outputs の役割

OpenAI Structured Outputs は、Gemini の出力をフロントエンドで扱いやすい JSON に変換する役割を持つ。

次の処理を行う。

- スキーマに沿った JSON へ整形する
- スキーマ外のキーを排除する
- 不明な値を `null` にする
- 商品名を `raw_name` と `normalized_name` に分ける
- 在庫対象かどうかの候補を作る
- `base_quantity` / `base_unit` の候補を作る
- 警告を `warnings` にまとめる

## Pydantic の役割

Pydantic は、OpenAI から返った JSON がアプリ内部で扱える形かどうかを検証する。

Pydantic 検証に失敗した場合は、外部 API または構造化処理の失敗として扱い、API 利用者へ安全なエラーを返す。

## データの扱い

金額は日本円の整数として扱う。

日付は `YYYY-MM-DD` の文字列として扱う。

数量は小数を許可する。例: `0.5`, `1.5`。

不明な値は `null` とする。

## 商品名の扱い

商品名は次の2種類に分ける。

```txt
raw_name         レシートに書かれていた文字列に近い商品名
normalized_name  在庫管理やレシピ提案で使いやすい商品名候補
```

例:

```json
{
  "raw_name": "タマゴM 10コ",
  "normalized_name": "卵"
}
```

`normalized_name` が判断できない場合は `null` にする。

## 単位の扱い

購入時の単位と、在庫管理で使いやすい基準単位を分ける。

```txt
purchased_quantity  レシート上の数量
purchased_unit      レシート上の単位
base_quantity       基準単位に換算した数量候補
base_unit           基準単位
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

変換が判断できない場合は、`base_quantity` と `base_unit` を `null` にする。

## 在庫対象判定

OCR API は `is_inventory_target` を候補として返す。

ただし、これは確定値ではない。フロントエンド確認後、DB 登録側で最終的に保存される。

例:

```json
{
  "raw_name": "卵",
  "is_inventory_target": true
}
```

```json
{
  "raw_name": "洗剤",
  "is_inventory_target": false
}
```

判断できない場合は `null` にする。

## 合計金額の扱い

明細合計とレシート合計が一致しない場合がある。

理由の例:

- 税表示
- 割引
- ポイント利用
- クーポン
- レジ袋
- OCR 漏れ
- 小計・合計行の誤読

この場合、API はエラーにしない。`warnings` に警告を入れて返す。

## セキュリティと個人情報

レシートには個人の行動履歴や支払い情報が含まれる可能性がある。

次を守ること。

- 画像を永続保存しない
- API キーをログに出さない
- 外部 API の生レスポンス全体をログに出さない
- エラーに内部スタックトレースを含めない
- テスト用画像には個人情報を含めない

## 完了状態

このプロジェクトの最初の完成状態は次の通り。

- `GET /health` が使える
- `POST /ocr/receipts/extract` が使える
- Gemini provider が分離されている
- OpenAI Structured Outputs provider が分離されている
- 外部 API をモックしたテストがある
- README に起動方法と curl 例がある
- DB に直接保存しないことが明記されている
