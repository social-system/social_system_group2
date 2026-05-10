# DB操作本体
from sqlalchemy.orm import Session

from app.common.date import parse_yyyymmdd
from app.receipts.models import Receipt, ReceiptItem
from app.schemas.receipts_requests import ReceiptCreate


def create_receipt(db: Session, data: ReceiptCreate) -> Receipt:
    for item in data.items:
        if item.num * item.amount != item.total:
            raise ValueError(
                f"num * amountとtotalが一致しません: "
                f"num={item.num}, amount={item.amount}, total={item.total}"
            )

    # 明細itemごとの総額の合計
    items_total = sum(item.total for item in data.items)

    # リクエスト上のレシート合計金額と明細の総額が異なる場合
    if items_total != data.receipt_total:
        # routes/receipts_create.py(API)で400 Bad Requestを返す
        raise ValueError(
            f"receipt_totalとitemsの合計が一致しません: "
            f"receipt_total={data.receipt_total}, items_total={items_total}"
        )

    # レシート全体を表すReceiptモデル(DBに登録予定のオブジェクト)
    receipt = Receipt(receipt_total=data.receipt_total)

    for item_data in data.items:
        # ReceiptとReceiptItemのリレーション
        receipt.items.append(
            ReceiptItem(
                item=item_data.item,
                num=item_data.num,
                amount=item_data.amount,
                total=item_data.total,
                # DB用日付に変換"20260428"->date(2026, 4, 28)
                date=parse_yyyymmdd(item_data.date),
                ingredients=item_data.ingredients,
            )
        )

    # DBセッションに追加(親が保存されると子も保存される)
    db.add(receipt)
    # DBにSQLを送る(確定はしない)
    db.flush()

    return receipt
