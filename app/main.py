from fastapi import FastAPI

from app.routes.ocr import router as ocr_router

app = FastAPI(
    title="Receipt OCR API",
    version="0.1.0",
)
app.include_router(ocr_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
