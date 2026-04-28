以下の編集をすれば、フロントとバックエンドの側のデータのやり取りのテストが実行できる(現状はちゃんと動いてる)
uvicorn main:app --reload　でpythonファイルを実行できる。これを実行した状態で、カメラとか家計簿を実行すると、python側のコマンドラインで結果が表示される。
31行目　data = await request.json()　でdataに追加される内容が、
50行目　contents = await file.read()　でcontentsに撮った画像が受け取れるはず


家計簿とカメラのtsxファイルのAPIURLを以下のように変更!!!!!!!!!

// 修正後 (PythonサーバーのURL):
const API_URL = "http://localhost:8000/kakeibo/add";

// 修正後 (PythonサーバーのURL):
const response = await fetch("http://localhost:8000/upload", { 



