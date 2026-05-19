from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 👈 1. これを追加

from app.routes.ocr import router as ocr_router

app = FastAPI(
    title="Receipt OCR API",
    version="0.1.0",
)

# 👈 2. ここからCORS設定を追加
app.add_middleware(
    CORSMiddleware,
    # アクセスを許可するURLのリスト
    allow_origins=[
        "http://localhost:5173",                # ローカル開発環境（Viteのデフォルト）
        "https://socialsystemgroup2.vercel.app" # 本番環境（あなたのVercelのURL）
    ],
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッド（GET, POSTなど）を許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)
# 👈 ここまで

app.include_router(ocr_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
