import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.inventory import router as inventory_router
from app.routes.operations import router as operations_router
from app.routes.prices import router as prices_router
from app.routes.products import router as products_router
from app.routes.receipts import router as receipts_router


DEFAULT_CORS_ALLOW_ORIGINS = ["http://localhost:5173","https://socialsystemgroup2.vercel.app"]


def parse_cors_allow_origins(value: str | None) -> list[str]:
    if not value:
        return DEFAULT_CORS_ALLOW_ORIGINS

    origins = [origin.strip() for origin in value.split(",")]
    origins = [origin for origin in origins if origin]

    if "*" in origins:
        raise ValueError("CORS_ALLOW_ORIGINS must not contain '*'")

    return origins or DEFAULT_CORS_ALLOW_ORIGINS


app = FastAPI(
    title="Receipt API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_allow_origins(os.environ.get("CORS_ALLOW_ORIGINS")),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(receipts_router)
app.include_router(inventory_router)
app.include_router(prices_router)
app.include_router(products_router)
app.include_router(operations_router)


@app.get("/")
def health_check():
    return {"status": "ok"}
