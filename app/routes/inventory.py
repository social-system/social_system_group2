from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud.inventory import (
    InventoryBadRequestError,
    InventoryNotFoundError,
    apply_receipt_to_inventory,
    create_inventory_movement,
    get_inventory_balances,
    list_inventory_batches,
    list_inventory_movements,
)
from app.db.session import get_db
from app.schemas.inventory_requests import (
    InventoryMovementCreateRequest,
    InventoryReceiptApplyRequest,
)
from app.schemas.inventory_responses import (
    InventoryBalanceListResponse,
    InventoryBatchListResponse,
    InventoryMovementCreateResponse,
    InventoryMovementListResponse,
    InventoryReceiptApplyResponse,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post(
    "/receipts/{receipt_id}/apply",
    response_model=InventoryReceiptApplyResponse,
)
def apply_receipt(
    receipt_id: int,
    payload: InventoryReceiptApplyRequest = Body(default_factory=InventoryReceiptApplyRequest),
    db: Session = Depends(get_db),
):
    try:
        response = apply_receipt_to_inventory(db, receipt_id, payload)
        db.commit()
        return response
    except InventoryNotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InventoryBadRequestError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        db.rollback()
        raise


@router.get("/balances", response_model=InventoryBalanceListResponse)
def read_balances(
    product_id: int | None = None,
    location_id: int | None = None,
    include_zero: bool = False,
    db: Session = Depends(get_db),
):
    return get_inventory_balances(
        db,
        product_id=product_id,
        location_id=location_id,
        include_zero=include_zero,
    )


@router.get("/batches", response_model=InventoryBatchListResponse)
def read_batches(
    product_id: int | None = None,
    location_id: int | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    expires_before: date | None = None,
    include_zero: bool = False,
    db: Session = Depends(get_db),
):
    try:
        return list_inventory_batches(
            db,
            product_id=product_id,
            location_id=location_id,
            status=status_filter,
            expires_before=expires_before,
            include_zero=include_zero,
        )
    except InventoryBadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/movements", response_model=InventoryMovementCreateResponse)
def create_movement(
    payload: InventoryMovementCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        response = create_inventory_movement(db, payload)
        db.commit()
        return response
    except InventoryNotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InventoryBadRequestError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        db.rollback()
        raise


@router.get("/movements", response_model=InventoryMovementListResponse)
def read_movements(
    product_id: int | None = None,
    batch_id: int | None = None,
    operation_id: int | None = None,
    movement_type: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return list_inventory_movements(
        db,
        product_id=product_id,
        batch_id=batch_id,
        operation_id=operation_id,
        movement_type=movement_type,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )
