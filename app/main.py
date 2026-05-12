import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.crud.inventory import seed_inventory_locations
from app.db.session import Base, engine
from app.db.session import SessionLocal
from app.inventory import models as inventory_models
from app.receipts import models as receipt_models
from app.routes.inventory import router as inventory_router
from app.routes.receipts import router as receipts_router

if os.environ.get("APP_ENV") != "test":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_inventory_locations(db)
        db.commit()

app = FastAPI(
    title="Receipt API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(receipts_router)
app.include_router(inventory_router)


@app.get("/")
def health_check():
    return {"status": "ok"}
