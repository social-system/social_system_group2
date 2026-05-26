from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.receipts.models import (
    ProductAlias,
    ProductAliasConflictEvent,
    ReceiptPrepareMetric,
    ReceiptPrepareUnresolvedName,
)
from app.schemas.receipts_prepare import ReceiptPrepareResponse
from app.services.product_normalization import normalize_product_key


@dataclass(frozen=True)
class TopUnresolvedRawName:
    raw_name: str
    raw_name_key: str
    count: int


@dataclass(frozen=True)
class ReceiptPrepareMetrics:
    prepare_count: int
    total_item_count: int
    unresolved_item_count: int
    unresolved_rate: float
    alias_count: int
    active_alias_count: int
    alias_conflict_count: int
    inventory_base_quantity_missing_count: int
    top_unresolved_raw_names: list[TopUnresolvedRawName]


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _get_or_create_prepare_metric(db: Session) -> ReceiptPrepareMetric:
    metric = db.scalars(select(ReceiptPrepareMetric).order_by(ReceiptPrepareMetric.id)).first()
    if metric is not None:
        return metric

    metric = ReceiptPrepareMetric(
        prepare_count=0,
        total_item_count=0,
        unresolved_item_count=0,
        inventory_base_quantity_missing_count=0,
    )
    db.add(metric)
    db.flush()
    return metric


def record_receipt_prepare_metrics(
    db: Session,
    response: ReceiptPrepareResponse,
) -> None:
    metric = _get_or_create_prepare_metric(db)
    total_item_count = len(response.receipt.items)
    unresolved_item_count = 0
    inventory_base_quantity_missing_count = 0
    unresolved_raw_names: dict[str, tuple[str, int]] = {}

    for item, resolution in zip(response.receipt.items, response.item_resolutions, strict=False):
        if resolution.product_id is None:
            unresolved_item_count += 1
            if item.raw_name is not None:
                raw_name_key = normalize_product_key(item.raw_name)
                if raw_name_key is not None:
                    raw_name, count = unresolved_raw_names.get(raw_name_key, (item.raw_name, 0))
                    unresolved_raw_names[raw_name_key] = (raw_name, count + 1)

        if item.is_inventory_target is True and item.base_quantity is None:
            inventory_base_quantity_missing_count += 1

    metric.prepare_count += 1
    metric.total_item_count += total_item_count
    metric.unresolved_item_count += unresolved_item_count
    metric.inventory_base_quantity_missing_count += inventory_base_quantity_missing_count

    seen_at = _now()
    for raw_name_key, (raw_name, count) in unresolved_raw_names.items():
        unresolved_name = db.scalars(
            select(ReceiptPrepareUnresolvedName).where(
                ReceiptPrepareUnresolvedName.raw_name_key == raw_name_key
            )
        ).first()
        if unresolved_name is None:
            unresolved_name = ReceiptPrepareUnresolvedName(
                raw_name=raw_name,
                raw_name_key=raw_name_key,
                count=count,
                last_seen_at=seen_at,
            )
            db.add(unresolved_name)
        else:
            unresolved_name.raw_name = raw_name
            unresolved_name.count += count
            unresolved_name.last_seen_at = seen_at

    db.flush()


def record_product_alias_conflict(
    db: Session,
    *,
    alias_key: str | None,
    requested_product_id: int | None,
    existing_product_id: int | None,
) -> None:
    if alias_key is None or requested_product_id is None or existing_product_id is None:
        return

    event = db.scalars(
        select(ProductAliasConflictEvent)
        .where(ProductAliasConflictEvent.alias_key == alias_key)
        .where(ProductAliasConflictEvent.requested_product_id == requested_product_id)
        .where(ProductAliasConflictEvent.existing_product_id == existing_product_id)
    ).first()
    seen_at = _now()
    if event is None:
        event = ProductAliasConflictEvent(
            alias_key=alias_key,
            requested_product_id=requested_product_id,
            existing_product_id=existing_product_id,
            count=1,
            last_seen_at=seen_at,
        )
        db.add(event)
    else:
        event.count += 1
        event.last_seen_at = seen_at

    db.flush()


def get_receipt_prepare_metrics(
    db: Session,
    *,
    top_limit: int = 10,
) -> ReceiptPrepareMetrics:
    metric = db.scalars(select(ReceiptPrepareMetric).order_by(ReceiptPrepareMetric.id)).first()
    prepare_count = metric.prepare_count if metric is not None else 0
    total_item_count = metric.total_item_count if metric is not None else 0
    unresolved_item_count = metric.unresolved_item_count if metric is not None else 0
    inventory_base_quantity_missing_count = (
        metric.inventory_base_quantity_missing_count if metric is not None else 0
    )
    unresolved_rate = 0.0
    if total_item_count:
        unresolved_rate = unresolved_item_count / total_item_count

    alias_count = db.scalar(select(func.count()).select_from(ProductAlias)) or 0
    active_alias_count = (
        db.scalar(
            select(func.count())
            .select_from(ProductAlias)
            .where(ProductAlias.is_active.is_(True))
        )
        or 0
    )
    alias_conflict_count = (
        db.scalar(select(func.coalesce(func.sum(ProductAliasConflictEvent.count), 0))) or 0
    )

    unresolved_names = [
        TopUnresolvedRawName(
            raw_name=row.raw_name,
            raw_name_key=row.raw_name_key,
            count=row.count,
        )
        for row in db.scalars(
            select(ReceiptPrepareUnresolvedName)
            .order_by(
                ReceiptPrepareUnresolvedName.count.desc(),
                ReceiptPrepareUnresolvedName.last_seen_at.desc(),
                ReceiptPrepareUnresolvedName.id,
            )
            .limit(top_limit)
        )
    ]

    return ReceiptPrepareMetrics(
        prepare_count=prepare_count,
        total_item_count=total_item_count,
        unresolved_item_count=unresolved_item_count,
        unresolved_rate=unresolved_rate,
        alias_count=alias_count,
        active_alias_count=active_alias_count,
        alias_conflict_count=alias_conflict_count,
        inventory_base_quantity_missing_count=inventory_base_quantity_missing_count,
        top_unresolved_raw_names=unresolved_names,
    )
