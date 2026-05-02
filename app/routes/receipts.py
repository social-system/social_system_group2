from fastapi import APIRouter

from app.routes import receipts_create

# レシート関連のAPIをまとめるrouter
router = APIRouter()

router.include_router(receipts_create.router)
