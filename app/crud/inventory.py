from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.inventory.models import (
    InventoryBatch,
    InventoryLocation,
    InventoryMovement,
    InventoryOperation,
)
from app.receipts.models import Product, Receipt
from app.schemas.inventory_requests import (
    InventoryMovementCreateRequest,
    InventoryReceiptApplyRequest,
)
from app.schemas.inventory_responses import (
    InventoryBalanceItemResponse,
    InventoryBalanceListResponse,
    InventoryBatchListResponse,
    InventoryBatchResponse,
    InventoryMovementCreateResponse,
    InventoryMovementListResponse,
    InventoryMovementResponse,
    InventoryMovementResult,
    InventoryReceiptApplyItemResponse,
    InventoryReceiptApplyResponse,
)

ACTIVE = "active"
DEPLETED = "depleted"
DISCARDED = "discarded"


class InventoryNotFoundError(ValueError):
    pass


class InventoryBadRequestError(ValueError):
    pass


@dataclass(frozen=True)
class _BatchReduction:
    batch: InventoryBatch
    quantity: Decimal


def _now() -> datetime:
    return datetime.now()


def _movement_idempotency_key(base_key: str | None, index: int) -> str | None:
    if base_key is None:
        return None
    return f"{base_key}:movement:{index}"


def _set_status_from_quantity(batch: InventoryBatch, *, movement_type: str) -> None:
    if batch.current_quantity > 0:
        batch.status = ACTIVE
    elif movement_type == "dispose":
        batch.status = DISCARDED
    else:
        batch.status = DEPLETED


def _validate_location(db: Session, location_id: int | None) -> None:
    if location_id is not None and db.get(InventoryLocation, location_id) is None:
        raise InventoryBadRequestError(f"location_id does not exist: {location_id}")


def seed_inventory_locations(db: Session) -> None:
    defaults = [
        ("冷蔵", 10),
        ("冷凍", 20),
        ("常温", 30),
        ("その他", 90),
    ]
    existing_names = set(db.scalars(select(InventoryLocation.name)).all())
    for name, sort_order in defaults:
        if name not in existing_names:
            db.add(InventoryLocation(name=name, sort_order=sort_order, is_active=True))
    db.flush()


def apply_receipt_to_inventory(
    db: Session,
    receipt_id: int,
    request: InventoryReceiptApplyRequest,
) -> InventoryReceiptApplyResponse:
    receipt = db.scalars(
        select(Receipt)
        .options(selectinload(Receipt.items))
        .where(Receipt.id == receipt_id)
    ).first()
    if receipt is None:
        raise InventoryNotFoundError("receipt not found")

    _validate_location(db, request.default_location_id)

    if request.idempotency_key:
        existing_operation = db.scalars(
            select(InventoryOperation).where(
                InventoryOperation.idempotency_key == request.idempotency_key
            )
        ).first()
        if existing_operation is not None:
            movements = db.scalars(
                select(InventoryMovement).where(
                    InventoryMovement.operation_id == existing_operation.id
                )
            ).all()
            items = [
                InventoryReceiptApplyItemResponse(
                    receipt_item_id=movement.receipt_item_id or 0,
                    product_id=movement.product_id,
                    product_name=movement.product.name,
                    quantity=movement.quantity_delta,
                    unit=movement.unit,
                    batch_id=movement.batch_id,
                    status="applied",
                )
                for movement in movements
            ]
            return InventoryReceiptApplyResponse(
                receipt_id=receipt_id,
                operation_id=existing_operation.id,
                applied_count=len(items),
                skipped_count=0,
                items=items,
            )

    operation = InventoryOperation(
        operation_type="receipt_apply",
        receipt_id=receipt.id,
        idempotency_key=request.idempotency_key,
        reason="receipt apply",
        occurred_at=_now(),
    )
    db.add(operation)
    db.flush()

    response_items: list[InventoryReceiptApplyItemResponse] = []
    movement_index = 0

    for item in receipt.items:
        product_name = item.product.name if item.product is not None else item.normalized_name

        if not item.is_inventory_target:
            response_items.append(
                InventoryReceiptApplyItemResponse(
                    receipt_item_id=item.id,
                    product_id=item.product_id,
                    product_name=product_name,
                    status="skipped",
                    reason="not_inventory_target",
                )
            )
            continue

        if (
            item.product_id is None
            or item.product is None
            or item.base_quantity is None
            or item.base_quantity <= 0
            or item.base_unit is None
        ):
            response_items.append(
                InventoryReceiptApplyItemResponse(
                    receipt_item_id=item.id,
                    product_id=item.product_id,
                    product_name=product_name,
                    status="skipped",
                    reason="missing_product_or_base_quantity",
                )
            )
            continue

        existing_batch = db.scalars(
            select(InventoryBatch).where(InventoryBatch.receipt_item_id == item.id)
        ).first()
        if existing_batch is not None:
            response_items.append(
                InventoryReceiptApplyItemResponse(
                    receipt_item_id=item.id,
                    product_id=item.product_id,
                    product_name=product_name,
                    quantity=item.base_quantity,
                    unit=item.base_unit,
                    batch_id=existing_batch.id,
                    status="skipped",
                    reason="already_applied",
                )
            )
            continue

        batch = InventoryBatch(
            product_id=item.product_id,
            receipt_item_id=item.id,
            location_id=request.default_location_id,
            initial_quantity=item.base_quantity,
            current_quantity=item.base_quantity,
            unit=item.base_unit,
            purchased_at=receipt.purchased_at,
            expires_at=request.expires_at_by_receipt_item_id.get(item.id),
            status=ACTIVE,
        )
        db.add(batch)
        db.flush()

        movement_index += 1
        movement = InventoryMovement(
            operation_id=operation.id,
            batch_id=batch.id,
            product_id=item.product_id,
            location_id=request.default_location_id,
            movement_type="purchase",
            quantity_delta=item.base_quantity,
            unit=item.base_unit,
            receipt_item_id=item.id,
            idempotency_key=_movement_idempotency_key(request.idempotency_key, movement_index),
            reason="receipt apply",
            occurred_at=operation.occurred_at,
        )
        db.add(movement)
        db.flush()

        response_items.append(
            InventoryReceiptApplyItemResponse(
                receipt_item_id=item.id,
                product_id=item.product_id,
                product_name=product_name,
                quantity=item.base_quantity,
                unit=item.base_unit,
                batch_id=batch.id,
                status="applied",
            )
        )

    applied_count = sum(1 for item in response_items if item.status == "applied")
    skipped_count = len(response_items) - applied_count
    return InventoryReceiptApplyResponse(
        receipt_id=receipt_id,
        operation_id=operation.id,
        applied_count=applied_count,
        skipped_count=skipped_count,
        items=response_items,
    )


def receipt_has_applicable_inventory_items(receipt: Receipt) -> bool:
    return any(
        item.is_inventory_target
        and item.product_id is not None
        and item.base_quantity is not None
        and item.base_quantity > 0
        and item.base_unit is not None
        for item in receipt.items
    )


def get_inventory_balances(
    db: Session,
    *,
    product_id: int | None = None,
    location_id: int | None = None,
    include_zero: bool = False,
) -> InventoryBalanceListResponse:
    statement = select(InventoryBatch).options(selectinload(InventoryBatch.product))

    if product_id is not None:
        statement = statement.where(InventoryBatch.product_id == product_id)
    if location_id is not None:
        statement = statement.where(InventoryBatch.location_id == location_id)
    if not include_zero:
        statement = statement.where(
            InventoryBatch.status == ACTIVE,
            InventoryBatch.current_quantity > 0,
        )

    grouped: dict[tuple[int, str], dict[str, object]] = {}
    for batch in db.scalars(statement).all():
        key = (batch.product_id, batch.unit)
        current = grouped.setdefault(
            key,
            {
                "product_id": batch.product_id,
                "product_name": batch.product.name,
                "quantity": Decimal("0"),
                "unit": batch.unit,
                "nearest_expires_at": None,
                "batch_count": 0,
                "normalized_name": batch.product.name,
                "current_quantity": Decimal("0"),
                "base_unit": batch.unit,
            },
        )
        current["quantity"] = current["quantity"] + batch.current_quantity  # type: ignore[operator]
        current["current_quantity"] = current["current_quantity"] + batch.current_quantity  # type: ignore[operator]
        current["batch_count"] = current["batch_count"] + 1  # type: ignore[operator]
        if batch.expires_at is not None:
            nearest = current["nearest_expires_at"]
            if nearest is None or batch.expires_at < nearest:
                current["nearest_expires_at"] = batch.expires_at

    return InventoryBalanceListResponse(
        items=[InventoryBalanceItemResponse(**item) for item in grouped.values()]
    )


def list_inventory_batches(
    db: Session,
    *,
    product_id: int | None = None,
    location_id: int | None = None,
    status: str | None = None,
    expires_before: date | None = None,
    include_zero: bool = False,
) -> InventoryBatchListResponse:
    if status is not None and status not in {ACTIVE, DEPLETED, DISCARDED}:
        raise InventoryBadRequestError("invalid status")

    statement = (
        select(InventoryBatch)
        .options(selectinload(InventoryBatch.product), selectinload(InventoryBatch.location))
        .order_by(
            InventoryBatch.expires_at.is_(None),
            InventoryBatch.expires_at,
            InventoryBatch.purchased_at.is_(None),
            InventoryBatch.purchased_at,
            InventoryBatch.id,
        )
    )

    if product_id is not None:
        statement = statement.where(InventoryBatch.product_id == product_id)
    if location_id is not None:
        statement = statement.where(InventoryBatch.location_id == location_id)
    if status is not None:
        statement = statement.where(InventoryBatch.status == status)
    if expires_before is not None:
        statement = statement.where(InventoryBatch.expires_at <= expires_before)
    if not include_zero:
        statement = statement.where(
            InventoryBatch.status == ACTIVE,
            InventoryBatch.current_quantity > 0,
        )

    return InventoryBatchListResponse(
        items=[
            InventoryBatchResponse(
                batch_id=batch.id,
                product_id=batch.product_id,
                product_name=batch.product.name,
                initial_quantity=batch.initial_quantity,
                current_quantity=batch.current_quantity,
                unit=batch.unit,
                location_id=batch.location_id,
                location_name=batch.location.name if batch.location is not None else None,
                purchased_at=batch.purchased_at,
                expires_at=batch.expires_at,
                status=batch.status,
                receipt_item_id=batch.receipt_item_id,
            )
            for batch in db.scalars(statement).all()
        ]
    )


def _available_batches_statement(product_id: int, unit: str):
    return (
        select(InventoryBatch)
        .where(
            InventoryBatch.product_id == product_id,
            InventoryBatch.unit == unit,
            InventoryBatch.status == ACTIVE,
            InventoryBatch.current_quantity > 0,
        )
        .order_by(
            InventoryBatch.expires_at.is_(None),
            InventoryBatch.expires_at,
            InventoryBatch.purchased_at.is_(None),
            InventoryBatch.purchased_at,
            InventoryBatch.id,
        )
    )


def _select_reductions(
    db: Session,
    *,
    product_id: int,
    unit: str,
    requested_quantity: Decimal,
    batch_id: int | None,
) -> list[_BatchReduction]:
    if batch_id is not None:
        batch = db.get(InventoryBatch, batch_id)
        if batch is None:
            raise InventoryNotFoundError("batch not found")
        if batch.product_id != product_id or batch.unit != unit or batch.status != ACTIVE:
            raise InventoryBadRequestError("batch is not available for this product and unit")
        if batch.current_quantity < requested_quantity:
            raise InventoryBadRequestError("insufficient_inventory")
        return [_BatchReduction(batch=batch, quantity=requested_quantity)]

    batches = db.scalars(_available_batches_statement(product_id, unit)).all()
    available_quantity = sum((batch.current_quantity for batch in batches), Decimal("0"))
    if available_quantity < requested_quantity:
        raise InventoryBadRequestError("insufficient_inventory")

    remaining = requested_quantity
    reductions: list[_BatchReduction] = []
    for batch in batches:
        if remaining <= 0:
            break
        quantity = min(batch.current_quantity, remaining)
        reductions.append(_BatchReduction(batch=batch, quantity=quantity))
        remaining -= quantity
    return reductions


def _response_from_operation(
    db: Session,
    operation: InventoryOperation,
    request: InventoryMovementCreateRequest,
    product: Product,
) -> InventoryMovementCreateResponse:
    movements = db.scalars(
        select(InventoryMovement)
        .where(InventoryMovement.operation_id == operation.id)
        .order_by(InventoryMovement.id)
    ).all()
    return InventoryMovementCreateResponse(
        operation_id=operation.id,
        movement_type=request.movement_type,
        product_id=product.id,
        product_name=product.name,
        requested_quantity=request.quantity,
        unit=request.unit,
        movements=[
            InventoryMovementResult(
                movement_id=movement.id,
                batch_id=movement.batch_id or 0,
                quantity_delta=movement.quantity_delta,
                remaining_quantity=movement.batch.current_quantity if movement.batch else Decimal("0"),
            )
            for movement in movements
        ],
    )


def create_inventory_movement(
    db: Session,
    request: InventoryMovementCreateRequest,
) -> InventoryMovementCreateResponse:
    product = db.get(Product, request.product_id)
    if product is None:
        raise InventoryNotFoundError("product not found")
    if request.unit != product.default_base_unit:
        raise InventoryBadRequestError("unit does not match product default_base_unit")
    _validate_location(db, request.location_id)

    if request.idempotency_key:
        existing_operation = db.scalars(
            select(InventoryOperation).where(
                InventoryOperation.idempotency_key == request.idempotency_key
            )
        ).first()
        if existing_operation is not None:
            return _response_from_operation(db, existing_operation, request, product)

    occurred_at = request.occurred_at or _now()
    operation = InventoryOperation(
        operation_type=request.movement_type,
        idempotency_key=request.idempotency_key,
        reason=request.reason,
        occurred_at=occurred_at,
    )
    db.add(operation)
    db.flush()

    movement_results: list[InventoryMovementResult] = []
    quantity = request.quantity

    if request.movement_type == "adjust" and quantity > 0:
        batch = InventoryBatch(
            product_id=product.id,
            receipt_item_id=None,
            location_id=request.location_id,
            initial_quantity=quantity,
            current_quantity=quantity,
            unit=request.unit,
            purchased_at=occurred_at.date(),
            status=ACTIVE,
            note=request.reason,
        )
        db.add(batch)
        db.flush()

        movement = InventoryMovement(
            operation_id=operation.id,
            batch_id=batch.id,
            product_id=product.id,
            location_id=request.location_id,
            movement_type="adjust",
            quantity_delta=quantity,
            unit=request.unit,
            receipt_item_id=None,
            idempotency_key=_movement_idempotency_key(request.idempotency_key, 1),
            reason=request.reason,
            occurred_at=occurred_at,
        )
        db.add(movement)
        db.flush()
        movement_results.append(
            InventoryMovementResult(
                movement_id=movement.id,
                batch_id=batch.id,
                quantity_delta=movement.quantity_delta,
                remaining_quantity=batch.current_quantity,
            )
        )
    else:
        requested_reduction = abs(quantity)
        reductions = _select_reductions(
            db,
            product_id=product.id,
            unit=request.unit,
            requested_quantity=requested_reduction,
            batch_id=request.batch_id,
        )

        for index, reduction in enumerate(reductions, start=1):
            batch = reduction.batch
            batch.current_quantity -= reduction.quantity
            _set_status_from_quantity(batch, movement_type=request.movement_type)

            movement = InventoryMovement(
                operation_id=operation.id,
                batch_id=batch.id,
                product_id=product.id,
                location_id=batch.location_id,
                movement_type=request.movement_type,
                quantity_delta=-reduction.quantity,
                unit=request.unit,
                receipt_item_id=batch.receipt_item_id,
                idempotency_key=_movement_idempotency_key(request.idempotency_key, index),
                reason=request.reason,
                occurred_at=occurred_at,
            )
            db.add(movement)
            db.flush()
            movement_results.append(
                InventoryMovementResult(
                    movement_id=movement.id,
                    batch_id=batch.id,
                    quantity_delta=movement.quantity_delta,
                    remaining_quantity=batch.current_quantity,
                )
            )

    return InventoryMovementCreateResponse(
        operation_id=operation.id,
        movement_type=request.movement_type,
        product_id=product.id,
        product_name=product.name,
        requested_quantity=request.quantity,
        unit=request.unit,
        movements=movement_results,
    )


def list_inventory_movements(
    db: Session,
    *,
    product_id: int | None = None,
    batch_id: int | None = None,
    operation_id: int | None = None,
    movement_type: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> InventoryMovementListResponse:
    statement = (
        select(InventoryMovement)
        .options(selectinload(InventoryMovement.product))
        .order_by(InventoryMovement.occurred_at.desc(), InventoryMovement.id.desc())
        .offset(offset)
        .limit(limit)
    )

    if product_id is not None:
        statement = statement.where(InventoryMovement.product_id == product_id)
    if batch_id is not None:
        statement = statement.where(InventoryMovement.batch_id == batch_id)
    if operation_id is not None:
        statement = statement.where(InventoryMovement.operation_id == operation_id)
    if movement_type is not None:
        statement = statement.where(InventoryMovement.movement_type == movement_type)
    if from_date is not None:
        statement = statement.where(InventoryMovement.occurred_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date is not None:
        statement = statement.where(InventoryMovement.occurred_at <= datetime.combine(to_date, datetime.max.time()))

    return InventoryMovementListResponse(
        items=[
            InventoryMovementResponse(
                movement_id=movement.id,
                operation_id=movement.operation_id,
                batch_id=movement.batch_id,
                product_id=movement.product_id,
                product_name=movement.product.name,
                movement_type=movement.movement_type,
                quantity_delta=movement.quantity_delta,
                unit=movement.unit,
                reason=movement.reason,
                occurred_at=movement.occurred_at,
            )
            for movement in db.scalars(statement).all()
        ]
    )
