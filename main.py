from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn



"""
家計簿とカメラのtsxファイルのAPIURLを以下のように変更!!!!!!!!!

// 修正後 (PythonサーバーのURL):
const API_URL = "http://localhost:8000/kakeibo/add";


// 修正後 (PythonサーバーのURL):
const response = await fetch("http://localhost:8000/upload", { 
"""

app = FastAPI()

# --- CORS設定: Next.jsからのアクセスを許可 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 機能1: 家計簿データの受信 ---
@app.post("/kakeibo/add")
async def receive_kakeibo(request: Request):
    data = await request.json()
    
    print("\n" + "="*30)
    print("      【家計簿データ受信】")
    print("="*30)
    print(f" 品名     : {data.get('item')}")
    print(f" 金額     : {data.get('amount')}円")
    print(f" 個数     : {data.get('num')}個")
    print(f" 日付     : {data.get('date')}")
    # 数値(1)でも文字列("1")でも判定できるようにしています
    is_ingredient = str(data.get('ingredients')) == "1"
    print(f" 食材判定 : {'はい' if is_ingredient else 'いいえ'}")
    print("="*30 + "\n")

    return {"status": "success", "message": "Python側で家計簿を表示しました"}

# --- 機能2: 画像データの受信 ---
@app.post("/upload")
async def test_upload(file: UploadFile = File(...)):
    contents = await file.read()
    
    print("\n" + "---"*10)
    print("      【画像データ受信】")
    print("---"*10)
    print(f" ファイル名 : {file.filename}")
    print(f" 形式       : {file.content_type}")
    print(f" サイズ     : {len(contents)} バイト")
    print("---"*10 + "\n")

    return {
        "status": "success",
        "message": f"画像 '{file.filename}' を受信しました",
        "received_size": len(contents)
    }

# --- サーバー起動 ---
if __name__ == "__main__":
    # これで8000番ポートで両方のURLが有効になります
    uvicorn.run(app, host="127.0.0.1", port=8000)