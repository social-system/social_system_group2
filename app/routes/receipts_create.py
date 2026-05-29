from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.date import format_yyyymmdd
from app.crud.inventory import (
    apply_receipt_to_inventory,
    receipt_has_applicable_inventory_items,
)
from app.crud.receipts_create import create_receipt
from app.db.session import get_db
from app.schemas.inventory_requests import InventoryReceiptApplyRequest
from app.schemas.receipts_prepare import (
    ReceiptAutoCreateRequest,
    ReceiptAutoCreateResponse,
    ReceiptPrepareRequest,
    ReceiptPrepareResponse,
)
from app.schemas.receipts_requests import ReceiptCreate
from app.schemas.receipts_responses import ReceiptSummaryResponse
from app.services.operations_metrics import record_receipt_prepare_metrics
from app.services.receipt_auto_create import evaluate_auto_registration
from app.services.receipts_prepare import prepare_receipt

router = APIRouter(
    prefix="/receipts",
    tags=["receipts"],
)


@router.post("/prepare", response_model=ReceiptPrepareResponse)
def post_receipt_prepare(
    payload: ReceiptPrepareRequest,
    db: Session = Depends(get_db),
):
    response = prepare_receipt(db, payload)
    try:
        record_receipt_prepare_metrics(db, response)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return response


@router.post("/auto-create", response_model=ReceiptAutoCreateResponse)
def post_receipt_auto_create(
    payload: ReceiptAutoCreateRequest,
    db: Session = Depends(get_db),
):
    response = prepare_receipt(db, payload)
    decision = evaluate_auto_registration(
        payload,
        response,
        auto_register_enabled=payload.auto_register_enabled,
    )
    summary = None
    receipt_id = None
    created = False

    try:
        record_receipt_prepare_metrics(db, response)
        if decision.eligible:
            receipt_payload = ReceiptCreate.model_validate(
                response.receipt.model_dump(mode="python")
            )
            receipt = create_receipt(db, receipt_payload)
            receipt.source = "ocr_auto_registered"
            if receipt_has_applicable_inventory_items(receipt):
                apply_receipt_to_inventory(
                    db,
                    receipt.id,
                    InventoryReceiptApplyRequest(
                        idempotency_key=f"receipt:auto-create:{receipt.id}"
                    ),
                )
            db.commit()
            db.refresh(receipt)
            receipt_id = receipt.id
            created = True
            summary = ReceiptSummaryResponse(
                id=receipt.id,
                purchased_at=format_yyyymmdd(receipt.purchased_at),
                store_name=receipt.store_name,
                total_amount=receipt.total_amount,
                items_total=receipt.items_total,
                adjustment_amount=receipt.adjustment_amount,
                item_count=len(receipt.items),
            )
        else:
            db.commit()
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_auto_receipt", "message": str(e)},
        )
    except Exception:
        db.rollback()
        raise

    return ReceiptAutoCreateResponse(
        created=created,
        receipt_id=receipt_id,
        summary=summary,
        receipt=response.receipt,
        item_resolutions=response.item_resolutions,
        unresolved_items=response.unresolved_items,
        warnings=response.warnings,
        validation_issues=response.validation_issues,
        auto_registration=decision,
    )


@router.post(
    "",
    response_model=ReceiptSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_receipt(
    payload: ReceiptCreate,
    db: Session = Depends(get_db),
):
    try:
        receipt = create_receipt(db, payload)
        if receipt_has_applicable_inventory_items(receipt):
            apply_receipt_to_inventory(
                db,
                receipt.id,
                InventoryReceiptApplyRequest(idempotency_key=f"receipt:create:{receipt.id}"),
            )
        db.commit()
        db.refresh(receipt)
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_receipt", "message": str(e)},
        )
    except Exception:
        db.rollback()
        raise

    return ReceiptSummaryResponse(
        id=receipt.id,
        purchased_at=format_yyyymmdd(receipt.purchased_at),
        store_name=receipt.store_name,
        total_amount=receipt.total_amount,
        items_total=receipt.items_total,
        adjustment_amount=receipt.adjustment_amount,
        item_count=len(receipt.items),
    )
