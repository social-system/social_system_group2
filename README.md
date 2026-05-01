<<<<<<< HEAD
# 運用ルール

## branchについて
個人のPCで開発を行う際には，基本的にbranchを切り分けて作業を行う

### branchに関するコマンド操作
- `git branch`: 現在いるブランチとローカルブランチの一覧を表示する
- `git checkout -b <新しいブランチ名>`: 現在のブランチから，指定した名前の新たなブランチに分岐する
- `git switch <ブランチ名>`: 指定したブランチに移動する

### 大まかなbranchのルール
- mainブランチは実装が完了した機能・パーツのみを置いておく
- デプロイしたらエラーが出ない状態を保ちたい
- 個人のブランチで作業する

### 命名規則
- `main`: 完成品を置くブランチ．基本はここから分岐させる．
- `feature-<名前>-[実装内容]`: 個人で実装を行うブランチ
- `fix-<修正内容>`: `main`にバグが紛れ込んだ場合の修正

### 参考
- [【GitHub】ブランチの運用方法について](https://qiita.com/onishi_820/items/d98c61e0faa67f417829)
    - GitHub flowに基本従っていれば良さそう
=======

  # 家計簿とレシピアプリ

  This is a code bundle for 家計簿とレシピアプリ. The original project is available at https://www.figma.com/design/4Z6kNrGKSjfFK5p8WtdA2l/%E5%AE%B6%E8%A8%88%E7%B0%BF%E3%81%A8%E3%83%AC%E3%82%B7%E3%83%94%E3%82%A2%E3%83%97%E3%83%AA.

  ## Running the code

  Run `npm i` to install the dependencies.

  Run `npm run dev` to start the development server.
  
>>>>>>> feature_inagi_UI
