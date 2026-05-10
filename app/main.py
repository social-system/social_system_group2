import os

from fastapi import FastAPI

from app.db.session import Base, engine
from app.receipts import models as receipt_models
from app.routes.receipts import router as receipts_router

if os.environ.get("APP_ENV") != "test":
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Receipt API",
)

app.include_router(receipts_router)


@app.get("/")
def health_check():
    return {"status": "ok"}
