from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.date import format_yyyymmdd, parse_yyyymmdd
from app.receipts.models import AccountingCategory
from app.schemas.receipts_prepare import (
    PreparedItemResolution,
    PreparedProductCandidate,
    PreparedReceipt,
    PreparedReceiptItem,
    ReceiptPrepareItemRequest,
    ReceiptPrepareRequest,
    ReceiptPrepareResponse,
)
from app.services.product_resolution import ProductResolutionInput, resolve_product


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _prepare_purchased_at(value: int | str | None) -> tuple[int | None, list[str]]:
    if value is None:
        return None, ["purchased_at_missing"]

    if isinstance(value, int):
        try:
            parse_yyyymmdd(value)
        except ValueError:
            return None, ["purchased_at_invalid"]
        return value, []

    stripped = value.strip()
    if not stripped:
        return None, ["purchased_at_missing"]

    if stripped.isdigit():
        int_value = int(stripped)
        try:
            parse_yyyymmdd(int_value)
        except ValueError:
            return None, ["purchased_at_invalid"]
        return int_value, []

    try:
        parsed = datetime.strptime(stripped, "%Y-%m-%d").date()
    except ValueError:
        return None, ["purchased_at_invalid"]
    return format_yyyymmdd(parsed), []


def _find_category_id_by_name(db: Session, category_name: str | None) -> int | None:
    normalized_name = _blank_to_none(category_name)
    if normalized_name is None:
        return None

    statement = select(AccountingCategory.id).where(AccountingCategory.name == normalized_name)
    return db.scalars(statement).first()


def _candidate_response(candidate) -> PreparedProductCandidate:
    return PreparedProductCandidate(
        product_id=candidate.product_id,
        name=candidate.product_name,
        default_category_id=candidate.default_category_id,
        default_base_unit=candidate.default_base_unit,
        is_inventory_target=candidate.is_inventory_target,
        matched_name=candidate.matched_name,
        match_source=candidate.match_source,
    )


def _item_issues(
    *,
    item: ReceiptPrepareItemRequest,
    prepared_item: PreparedReceiptItem,
    resolution_status: str,
) -> list[str]:
    issues: list[str] = []

    if _blank_to_none(item.raw_name) is None:
        issues.append("raw_name_missing")
    if item.purchased_quantity is None:
        issues.append("purchased_quantity_missing")
    if item.line_total is None:
        issues.append("line_total_missing")
    if item.is_inventory_target is None:
        issues.append("inventory_target_missing")

    if resolution_status == "unresolved":
        issues.append("product_not_resolved")
    elif resolution_status == "invalid_product_id":
        issues.append("invalid_product_id")

    if item.is_inventory_target is True:
        if _blank_to_none(prepared_item.normalized_name) is None:
            issues.append("inventory_target_without_normalized_name")
        if prepared_item.base_quantity is None:
            issues.append("inventory_target_without_base_quantity")
        if _blank_to_none(prepared_item.base_unit) is None:
            issues.append("inventory_target_without_base_unit")

    return issues


def prepare_receipt(
    db: Session,
    payload: ReceiptPrepareRequest,
) -> ReceiptPrepareResponse:
    purchased_at, validation_issues = _prepare_purchased_at(payload.purchased_at)
    if payload.total_amount is None:
        validation_issues.append("total_amount_missing")
    if not payload.items:
        validation_issues.append("items_empty")

    prepared_items: list[PreparedReceiptItem] = []
    item_resolutions: list[PreparedItemResolution] = []
    unresolved_items: list[PreparedItemResolution] = []

    for index, item in enumerate(payload.items):
        resolution = resolve_product(
            db,
            ProductResolutionInput(
                product_id=item.product_id,
                raw_name=item.raw_name,
                normalized_name=item.normalized_name,
            ),
        )

        category_id = item.category_id
        if resolution.default_category_id is not None:
            category_id = resolution.default_category_id
        elif category_id is None:
            category_id = _find_category_id_by_name(db, item.category_name)

        base_unit = _blank_to_none(item.base_unit)
        if base_unit is None and resolution.default_base_unit is not None:
            base_unit = resolution.default_base_unit

        normalized_name = _blank_to_none(item.normalized_name)
        if resolution.product_name is not None:
            normalized_name = resolution.product_name

        prepared_item = PreparedReceiptItem(
            raw_name=_blank_to_none(item.raw_name),
            normalized_name=normalized_name,
            product_id=resolution.product_id,
            category_id=category_id,
            purchased_quantity=item.purchased_quantity,
            purchased_unit=_blank_to_none(item.purchased_unit),
            base_quantity=item.base_quantity,
            base_unit=base_unit,
            unit_price=item.unit_price,
            line_total=item.line_total,
            is_inventory_target=item.is_inventory_target,
        )
        prepared_items.append(prepared_item)

        issues = _item_issues(
            item=item,
            prepared_item=prepared_item,
            resolution_status=resolution.resolution_status,
        )
        item_resolution = PreparedItemResolution(
            index=index,
            resolution_status=resolution.resolution_status,
            resolution_source=resolution.resolution_source,
            product_id=resolution.product_id,
            product_name=resolution.product_name,
            product_candidates=[
                _candidate_response(candidate)
                for candidate in resolution.candidates
            ],
            issues=issues,
        )
        item_resolutions.append(item_resolution)
        if issues:
            unresolved_items.append(item_resolution)

    return ReceiptPrepareResponse(
        receipt=PreparedReceipt(
            store_name=_blank_to_none(payload.store_name),
            purchased_at=purchased_at,
            total_amount=payload.total_amount,
            items=prepared_items,
        ),
        item_resolutions=item_resolutions,
        unresolved_items=unresolved_items,
        warnings=payload.warnings,
        validation_issues=validation_issues,
    )
