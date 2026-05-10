# AGENTS.md

## 目的

このリポジトリは、一人用のローカル家計簿として使うレシート管理バックエンドである。

Codex は `doc/milestone/MILESTONE01.md` から `doc/milestone/MILESTONE09.md` までを、番号順に実装すること。  
内部では各マイルストーンを独立した作業単位として扱い、各段階で確認、テスト、デバッグ、ローカル git commit まで行う。

GitHub への push は行わない。  
作業後、利用者が内容を確認してから GitHub に反映する。

## 基本方針

このプロジェクトは当面、一人用のローカルアプリとして開発する。

そのため、以下は実装しない。

- 認証
- ユーザー管理
- 世帯管理
- `user_id` によるデータ分離
- OCR 連携
- レシート更新 API
- 集計 API
- Alembic などのマイグレーション導入
- 本番用 DB 構成
- 外部サービス連携

今回の対象は、登録済みレシートを確認・削除できる状態にし、不正なレシートデータを保存しにくくすることである。

## 参照すべき文書

作業前に必ず以下を確認する。

1. `PROJECT STATUS.md`
2. `doc/milestone/MILESTONE01.md`
3. 現在作業対象の `doc/milestone/MILESTONEXX.md`

マイルストーン文書に書かれていない機能を勝手に追加しない。

## 実行順序

Codex は次の順番で作業する。

1. `MILESTONE01.md`  
   バリデーション強化

2. `MILESTONE02.md`  
   レシート詳細取得 CRUD 追加

3. `MILESTONE03.md`  
   `GET /receipts/{receipt_id}` 追加

4. `MILESTONE04.md`  
   レシート一覧取得 CRUD 追加

5. `MILESTONE05.md`  
   `GET /receipts` 追加

6. `MILESTONE06.md`  
   レシート削除 CRUD 追加

7. `MILESTONE07.md`  
   `DELETE /receipts/{receipt_id}` 追加

8. `MILESTONE08.md`  
   テスト用 DB 設定追加

9. `MILESTONE09.md`  
   API テスト追加

順番を飛ばさない。  
複数のマイルストーンをまとめて 1 commit にしない。  
各マイルストーンの完了後、テストが通った場合のみ git commit する。

## git 運用

作業開始時に必ず以下を確認する。

```bash
git status --short
git branch --show-current
```

作業前に未コミット変更がある場合は、利用者の変更である可能性がある。  
その場合、Codex は勝手に上書きしない。可能であれば現在の変更を壊さない形で作業する。衝突や上書きの恐れがある場合は作業を止め、状況を報告する。

各マイルストーン完了後、テスト通過を確認したうえで commit する。

commit メッセージは次の形式にする。

```text
milestone01: strengthen receipt validation
milestone02: add receipt detail crud
milestone03: add receipt detail endpoint
milestone04: add receipt list crud
milestone05: add receipt list endpoint
milestone06: add receipt delete crud
milestone07: add receipt delete endpoint
milestone08: add test database setup
milestone09: add receipt api tests
```

GitHub への push は絶対に行わない。

禁止コマンド:

```bash
git push
git push --force
git push --force-with-lease
```

ローカル commit までを行い、最後に以下を表示する。

```bash
git status --short
git log --oneline -9
```

## テスト方針

各マイルストーン完了時に、利用可能なテストを必ず実行する。

基本コマンド:

```bash
uv run pytest
```

まだテスト環境がない段階では、少なくとも構文確認を行う。

```bash
uv run python -m compileall app
```

テストが存在しない場合でも、`compileall` が通ることを最低条件にする。  
`MILESTONE08` 以降は、テスト用 DB を使う設定を追加し、`uv run pytest` が通ることを必須にする。

本番用または通常開発用の `receipts.db` をテストで使用しない。  
テストでは一時 DB またはテスト専用 SQLite DB を使う。  
テスト実行によって、既存のローカルデータを破壊してはならない。

## 自動デバッグ方針

テストまたは構文確認に失敗した場合、Codex は次の順番で自動修正する。

1. エラーメッセージと失敗したテストを読む
2. 原因を特定する
3. 最小限の修正を行う
4. 失敗したテストだけを再実行する
5. 通ったら全体テストを実行する
6. 全体テストが通ったら commit する

修正は最小限にする。  
失敗の原因と無関係な大規模リファクタリングを行わない。  
同じ問題で繰り返し失敗する場合は、修正内容を見直し、実装方針がマイルストーンに合っているか確認する。

解決不能な場合は、未完成のまま commit しない。  
その時点の状況、失敗しているテスト、推定原因、次に人間が確認すべき点を報告する。

## API 設計方針

入力値の型や形式が不正な場合は `422 Unprocessable Entity` を返す。  
形式は正しいがレシートとして矛盾している場合は `400 Bad Request` を返す。  
存在しないレシート ID を指定した場合は `404 Not Found` を返す。

主な扱いは次の通り。

| 内容                                | ステータス |
| ----------------------------------- | ---------- |
| `items` が空                        | `422`      |
| `date` が実在しない                 | `422`      |
| `item` が空                         | `422`      |
| `num` が 0 以下                     | `422`      |
| `amount` が 0 未満                  | `422`      |
| `total` が 0 未満                   | `422`      |
| `num * amount != total`             | `400`      |
| `receipt_total != sum(items.total)` | `400`      |
| 存在しないレシート取得              | `404`      |
| 存在しないレシート削除              | `404`      |

## バリデーション方針

`items` は 1 件以上必須にする。  
空配列は許可しない。

`date` は `YYYYMMDD` 形式の整数として受け取り、実在する日付のみ許可する。  
例として `20260230` は不正である。

`total` は `num * amount` と一致する必要がある。  
一致しない場合は `400 Bad Request` とする。

`receipt_total` は全明細の `total` 合計と一致する必要がある。  
一致しない場合は `400 Bad Request` とする。

## DB 設計方針

現時点では既存の DB 構造を大きく変えない。

`receipts` はレシート全体を表す。  
`receipt_items` はレシート明細を表す。  
`Receipt` と `ReceiptItem` の 1 対多関係を維持する。

親レシートを削除した場合、関連する明細も削除される設計を維持する。

レシート日付は現状 `receipt_items.date` に存在する。  
今回のマイルストーンでは `receipts` へ `date` カラムを移動しない。  
一覧 API では、必要に応じて `date_min` と `date_max` を返す。

## レイヤー責務

API ルーティング、CRUD、スキーマ、モデルの責務を分ける。

ルーターでは以下を行う。

- リクエスト受け取り
- 依存性注入による DB セッション取得
- CRUD 関数の呼び出し
- HTTP 例外への変換

CRUD では以下を行う。

- DB 検索
- DB 登録
- DB 削除
- 業務ルール検証
- SQLAlchemy モデルの操作

スキーマでは以下を行う。

- 入力形式の検証
- レスポンス形式の定義
- Pydantic による基本バリデーション

モデルでは以下を行う。

- SQLAlchemy テーブル定義
- リレーション定義

## 実装時の注意

既存の API 互換性をできるだけ保つ。  
既存の `POST /receipts` の正常系レスポンスを不要に変えない。  
ただし、バリデーション強化により不正データが登録できなくなる変更は許可する。

FastAPI と SQLAlchemy 2.x の書き方に合わせる。  
古い SQLAlchemy 記法へ戻さない。

不要な依存関係を追加しない。  
必要な場合でも、まず標準ライブラリと既存依存関係で実現できるか確認する。

## MILESTONE01 の完了条件

以下を満たしたら完了とする。

- `items` が空の場合に `422` になる
- `date` が実在しない場合に `422` になる
- `num * amount != total` の場合に `400` になる
- `receipt_total != sum(items.total)` の既存検証が維持されている
- 利用可能なテストまたは構文確認が通る
- commit が作成されている

## MILESTONE02 の完了条件

以下を満たしたら完了とする。

- CRUD 層にレシート詳細取得関数がある
- 明細付きで 1 件のレシートを取得できる
- 存在しない ID の場合に `None` または同等の結果を返せる
- API 層に過度な DB 操作を書かない
- 利用可能なテストまたは構文確認が通る
- commit が作成されている

## MILESTONE03 の完了条件

以下を満たしたら完了とする。

- `GET /receipts/{receipt_id}` が追加されている
- 登録済みレシートを明細付きで取得できる
- 存在しない ID の場合に `404` になる
- レスポンス形式が登録 API のレスポンスと整合している
- 利用可能なテストまたは構文確認が通る
- commit が作成されている

## MILESTONE04 の完了条件

以下を満たしたら完了とする。

- CRUD 層にレシート一覧取得関数がある
- `skip` と `limit` を扱える
- 必要に応じて日付範囲で絞り込める
- 一覧用の要約情報を取得できる
- 利用可能なテストまたは構文確認が通る
- commit が作成されている

## MILESTONE05 の完了条件

以下を満たしたら完了とする。

- `GET /receipts` が追加されている
- `skip` と `limit` をクエリパラメータで受け取れる
- 必要に応じて `date_from` と `date_to` を受け取れる
- 一覧では明細全文ではなく要約を返す
- 利用可能なテストまたは構文確認が通る
- commit が作成されている

## MILESTONE06 の完了条件

以下を満たしたら完了とする。

- CRUD 層にレシート削除関数がある
- 親レシート削除時に明細も削除される
- 存在しない ID の場合に削除失敗を表現できる
- 利用可能なテストまたは構文確認が通る
- commit が作成されている

## MILESTONE07 の完了条件

以下を満たしたら完了とする。

- `DELETE /receipts/{receipt_id}` が追加されている
- 存在する ID を削除できる
- 存在しない ID の場合に `404` になる
- 削除後に詳細取得すると `404` になる
- 利用可能なテストまたは構文確認が通る
- commit が作成されている

## MILESTONE08 の完了条件

以下を満たしたら完了とする。

- テスト用 DB 設定がある
- テストが通常開発用の `receipts.db` を使わない
- FastAPI の DB 依存性をテストで差し替えられる
- テスト実行前後で DB 状態を制御できる
- `uv run pytest` が実行できる
- commit が作成されている

## MILESTONE09 の完了条件

以下を満たしたら完了とする。

- 正常なレシート登録テストがある
- 合計金額不一致時の `400` テストがある
- `num * amount != total` の `400` テストがある
- 空 `items` の `422` テストがある
- 不正日付の `422` テストがある
- 詳細取得の正常系テストがある
- 存在しない詳細取得の `404` テストがある
- 一覧取得のテストがある
- 削除の正常系テストがある
- 削除後に詳細取得すると `404` になるテストがある
- `uv run pytest` が通る
- commit が作成されている

## 完了時の報告

全マイルストーン完了後、Codex は以下を報告する。

- 実装したマイルストーン一覧
- 作成した commit 一覧
- 実行したテストコマンド
- テスト結果
- GitHub へ push していないこと
- 利用者が次に確認すべきこと

最後に以下のコマンド結果を確認する。

```bash
git status --short
git log --oneline -9
```

作業ツリーが clean であることが望ましい。  
未コミット変更が残っている場合は、その理由を明記する。
