# Milestone 07: Integration and Documentation

## 目的

OCR API 全体を統合し、README とテストを整備する。

## 実装対象

- README.md 更新
- curl 例の追加
- `.env.example` の確認
- エラー仕様の反映
- 主要テストの追加または整理
- `uv run python -m compileall app`
- `uv run pytest`

## README に書くこと

- プロジェクト概要
- DB 登録しないこと
- フロントエンド確認用 API であること
- 処理フロー
- セットアップ方法
- `.env.example` の説明
- 起動方法
- `GET /health` の例
- `POST /ocr/receipts/extract` の curl 例
- 正常レスポンス例
- テスト実行方法

## 統合テスト

外部 API をモックした状態で、次を確認する。

- 正常な画像アップロードで OCR レスポンスが返る
- `warnings` を含む結果が返る
- provider 失敗が適切な HTTP status になる
- 不正画像系のエラーが適切に返る

## 最終確認コマンド

```bash
uv run python -m compileall app
uv run pytest
```

## 完了報告に含めること

Codex の最後の報告には、次を含める。

```txt
変更したファイル
追加した API
追加した schema
追加した provider
テスト結果
未対応事項
```

## 非対象

最後まで、次は実装しない。

- DB 登録
- database API 呼び出し
- 在庫反映
- レシピ提案
- 認証
- 画像保存
