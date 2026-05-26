"""initial_schema

Revision ID: 20260526_0001
Revises:
Create Date: 2026-05-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260526_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accounting_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "inventory_locations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "product_alias_conflict_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("alias_key", sa.String(length=255), nullable=False),
        sa.Column("requested_product_id", sa.Integer(), nullable=False),
        sa.Column("existing_product_id", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "alias_key",
            "requested_product_id",
            "existing_product_id",
            name="uq_product_alias_conflict_event",
        ),
    )
    op.create_table(
        "receipt_prepare_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("prepare_count", sa.Integer(), nullable=False),
        sa.Column("total_item_count", sa.Integer(), nullable=False),
        sa.Column("unresolved_item_count", sa.Integer(), nullable=False),
        sa.Column("inventory_base_quantity_missing_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "receipt_prepare_unresolved_names",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("raw_name", sa.String(length=255), nullable=False),
        sa.Column("raw_name_key", sa.String(length=255), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("raw_name_key"),
    )
    op.create_table(
        "receipts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("purchased_at", sa.Date(), nullable=False),
        sa.Column("store_name", sa.String(length=255), nullable=True),
        sa.Column("total_amount", sa.Integer(), nullable=False),
        sa.Column("items_total", sa.Integer(), nullable=False),
        sa.Column("adjustment_amount", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_key", sa.String(length=255), nullable=False),
        sa.Column("default_base_unit", sa.String(length=50), nullable=False),
        sa.Column("default_category_id", sa.Integer(), nullable=True),
        sa.Column("is_inventory_target", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["default_category_id"], ["accounting_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("name_key"),
    )
    op.create_table(
        "inventory_operations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("operation_type", sa.String(length=50), nullable=False),
        sa.Column("receipt_id", sa.Integer(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "operation_type in ('receipt_apply', 'purchase', 'consume', 'dispose', 'adjust')",
            name="ck_inventory_operations_type",
        ),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_inventory_operations_idempotency_key",
        "inventory_operations",
        ["idempotency_key"],
        unique=True,
    )
    op.create_index(
        "ix_inventory_operations_operation_type",
        "inventory_operations",
        ["operation_type"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_operations_receipt_id",
        "inventory_operations",
        ["receipt_id"],
        unique=False,
    )
    op.create_table(
        "product_aliases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("alias_name", sa.String(length=255), nullable=False),
        sa.Column("alias_key", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alias_key"),
    )
    op.create_table(
        "product_unit_conversions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("from_unit", sa.String(length=50), nullable=False),
        sa.Column("to_unit", sa.String(length=50), nullable=False),
        sa.Column("multiplier", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id",
            "from_unit",
            "to_unit",
            name="uq_product_unit_conversion",
        ),
    )
    op.create_table(
        "receipt_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("receipt_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("raw_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=True),
        sa.Column("purchased_quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("purchased_unit", sa.String(length=50), nullable=True),
        sa.Column("base_quantity", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("base_unit", sa.String(length=50), nullable=True),
        sa.Column("unit_price", sa.Integer(), nullable=True),
        sa.Column("line_total", sa.Integer(), nullable=False),
        sa.Column("is_inventory_target", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["accounting_categories.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "inventory_batches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("receipt_item_id", sa.Integer(), nullable=True),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("initial_quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("current_quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("purchased_at", sa.Date(), nullable=True),
        sa.Column("expires_at", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "current_quantity >= 0",
            name="ck_inventory_batches_current_nonnegative",
        ),
        sa.CheckConstraint(
            "initial_quantity > 0",
            name="ck_inventory_batches_initial_positive",
        ),
        sa.CheckConstraint(
            "status in ('active', 'depleted', 'discarded')",
            name="ck_inventory_batches_status",
        ),
        sa.ForeignKeyConstraint(["location_id"], ["inventory_locations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["receipt_item_id"], ["receipt_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_inventory_batches_location_id",
        "inventory_batches",
        ["location_id"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_batches_product_id",
        "inventory_batches",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_batches_receipt_item_id",
        "inventory_batches",
        ["receipt_item_id"],
        unique=True,
    )
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("operation_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("movement_type", sa.String(length=50), nullable=False),
        sa.Column("quantity_delta", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("receipt_item_id", sa.Integer(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "movement_type in ('purchase', 'consume', 'dispose', 'adjust')",
            name="ck_inventory_movements_type",
        ),
        sa.CheckConstraint(
            "quantity_delta != 0",
            name="ck_inventory_movements_quantity_nonzero",
        ),
        sa.ForeignKeyConstraint(["batch_id"], ["inventory_batches.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["inventory_locations.id"]),
        sa.ForeignKeyConstraint(["operation_id"], ["inventory_operations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["receipt_item_id"], ["receipt_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_inventory_movements_batch_id",
        "inventory_movements",
        ["batch_id"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_movements_idempotency_key",
        "inventory_movements",
        ["idempotency_key"],
        unique=True,
    )
    op.create_index(
        "ix_inventory_movements_location_id",
        "inventory_movements",
        ["location_id"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_movements_movement_type",
        "inventory_movements",
        ["movement_type"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_movements_operation_id",
        "inventory_movements",
        ["operation_id"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_movements_product_id",
        "inventory_movements",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_movements_receipt_item_id",
        "inventory_movements",
        ["receipt_item_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_inventory_movements_receipt_item_id", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_product_id", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_operation_id", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_movement_type", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_location_id", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_idempotency_key", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_batch_id", table_name="inventory_movements")
    op.drop_table("inventory_movements")
    op.drop_index("ix_inventory_batches_receipt_item_id", table_name="inventory_batches")
    op.drop_index("ix_inventory_batches_product_id", table_name="inventory_batches")
    op.drop_index("ix_inventory_batches_location_id", table_name="inventory_batches")
    op.drop_table("inventory_batches")
    op.drop_table("receipt_items")
    op.drop_table("product_unit_conversions")
    op.drop_table("product_aliases")
    op.drop_index("ix_inventory_operations_receipt_id", table_name="inventory_operations")
    op.drop_index("ix_inventory_operations_operation_type", table_name="inventory_operations")
    op.drop_index("ix_inventory_operations_idempotency_key", table_name="inventory_operations")
    op.drop_table("inventory_operations")
    op.drop_table("products")
    op.drop_table("receipts")
    op.drop_table("receipt_prepare_unresolved_names")
    op.drop_table("receipt_prepare_metrics")
    op.drop_table("product_alias_conflict_events")
    op.drop_table("inventory_locations")
    op.drop_table("accounting_categories")
