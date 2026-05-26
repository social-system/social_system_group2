from dataclasses import dataclass

from app.schemas.receipts_prepare import (
    AutoRegistrationDecision,
    ReceiptPrepareRequest,
    ReceiptPrepareResponse,
)

MIN_ITEM_CONFIDENCE = 0.85


@dataclass(frozen=True)
class AutoRegistrationEvaluation:
    eligible: bool
    reasons: list[str]


def evaluate_auto_registration(
    payload: ReceiptPrepareRequest,
    prepared: ReceiptPrepareResponse,
    *,
    auto_register_enabled: bool = True,
    min_item_confidence: float = MIN_ITEM_CONFIDENCE,
) -> AutoRegistrationDecision:
    reasons: list[str] = []

    if not auto_register_enabled:
        reasons.append("auto_registration_disabled")

    for issue in prepared.validation_issues:
        reasons.append(f"validation_issue:{issue}")

    if prepared.warnings:
        reasons.append("ocr_warnings_present")

    if prepared.unresolved_items:
        reasons.append("unresolved_items_present")

    receipt = prepared.receipt
    if receipt.purchased_at is None:
        reasons.append("purchased_at_missing")
    if receipt.total_amount is None:
        reasons.append("total_amount_missing")
    if not receipt.items:
        reasons.append("items_empty")

    items_total = 0
    line_totals_complete = True

    for index, (source_item, prepared_item, resolution) in enumerate(
        zip(payload.items, receipt.items, prepared.item_resolutions, strict=False)
    ):
        if source_item.warnings:
            reasons.append(f"item_{index}_warnings_present")

        if source_item.confidence is None:
            reasons.append(f"item_{index}_confidence_missing")
        elif source_item.confidence < min_item_confidence:
            reasons.append(f"item_{index}_confidence_below_threshold")

        metadata = source_item.ocr_metadata
        if metadata.auto_register_candidate is False:
            reasons.append(f"item_{index}_metadata_blocks_auto_registration")
        for review_reason in metadata.needs_review_reasons:
            reasons.append(f"item_{index}_needs_review:{review_reason}")

        if resolution.issues:
            reasons.append(f"item_{index}_issues_present")
        if resolution.resolution_status != "resolved":
            reasons.append(f"item_{index}_not_resolved")

        if prepared_item.raw_name is None:
            reasons.append(f"item_{index}_raw_name_missing")
        if prepared_item.purchased_quantity is None:
            reasons.append(f"item_{index}_purchased_quantity_missing")
        if prepared_item.line_total is None:
            line_totals_complete = False
            reasons.append(f"item_{index}_line_total_missing")
        else:
            items_total += prepared_item.line_total
        if prepared_item.is_inventory_target is None:
            reasons.append(f"item_{index}_inventory_target_missing")

        if prepared_item.is_inventory_target is True:
            if prepared_item.product_id is None:
                reasons.append(f"item_{index}_product_id_missing")
            if prepared_item.normalized_name is None:
                reasons.append(f"item_{index}_normalized_name_missing")
            if prepared_item.base_quantity is None:
                reasons.append(f"item_{index}_base_quantity_missing")
            if prepared_item.base_unit is None:
                reasons.append(f"item_{index}_base_unit_missing")

    if (
        receipt.total_amount is not None
        and line_totals_complete
        and receipt.items
        and receipt.total_amount != items_total
    ):
        reasons.append("items_total_mismatch")

    deduped_reasons = list(dict.fromkeys(reasons))
    return AutoRegistrationDecision(
        eligible=not deduped_reasons,
        reasons=deduped_reasons,
        min_item_confidence=min_item_confidence,
    )
