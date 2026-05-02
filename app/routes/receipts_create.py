# レシート登録API(FastAPIエンドポイント)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.date import format_yyyymmdd
from app.crud.receipts_create import create_receipt
from app.db.session import get_db
from app.schemas.receipts_requests import ReceiptCreate
from app.schemas.receipts_responses import ReceiptItemResponse, ReceiptResponse

router = APIRouter(
    prefix="/receipts",
    tags=["receipts"],
)


# POST /receipts
@router.post(
    "",
    response_model=ReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_receipt(
    payload: ReceiptCreate,  # リクエストボディ
    db: Session = Depends(get_db),  # FastAPIがget_db()を呼び出し, dbに渡す
):
    # 登録処理
    try:
        receipt = create_receipt(db, payload)
        db.commit()
        db.refresh(receipt)

    # 入力値が不正の場合(明細合計とレシート合計金額が一致しないなど)
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception:
        db.rollback()
        raise

    return ReceiptResponse(
        id=receipt.id,
        receipt_total=receipt.receipt_total,
        items=[
            ReceiptItemResponse(
                id=item.id,
                item=item.item,
                num=item.num,
                amount=item.amount,
                total=item.total,
                date=format_yyyymmdd(item.date),
                ingredients=item.ingredients,
            )
            for item in receipt.items
        ],
    )
