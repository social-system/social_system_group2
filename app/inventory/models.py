from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class InventoryLocation(Base):
    __tablename__ = "inventory_locations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    batches: Mapped[list["InventoryBatch"]] = relationship(back_populates="location")


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"
    __table_args__ = (
        CheckConstraint("initial_quantity > 0", name="ck_inventory_batches_initial_positive"),
        CheckConstraint("current_quantity >= 0", name="ck_inventory_batches_current_nonnegative"),
        CheckConstraint(
            "status in ('active', 'depleted', 'discarded')",
            name="ck_inventory_batches_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    receipt_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("receipt_items.id"),
        nullable=True,
        index=True,
    )
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_locations.id"),
        nullable=True,
        index=True,
    )
    initial_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    current_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    purchased_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    product: Mapped["Product"] = relationship()  # type: ignore[name-defined]
    receipt_item: Mapped["ReceiptItem | None"] = relationship()  # type: ignore[name-defined]
    location: Mapped["InventoryLocation | None"] = relationship(back_populates="batches")
    movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="batch")


class InventoryOperation(Base):
    __tablename__ = "inventory_operations"
    __table_args__ = (
        CheckConstraint(
            "operation_type in ('receipt_apply', 'purchase', 'consume', 'dispose', 'adjust')",
            name="ck_inventory_operations_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    receipt_id: Mapped[int | None] = mapped_column(
        ForeignKey("receipts.id"),
        nullable=True,
        index=True,
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="operation")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        CheckConstraint("quantity_delta != 0", name="ck_inventory_movements_quantity_nonzero"),
        CheckConstraint(
            "movement_type in ('purchase', 'consume', 'dispose', 'adjust')",
            name="ck_inventory_movements_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operation_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_operations.id"),
        nullable=False,
        index=True,
    )
    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_batches.id"),
        nullable=True,
        index=True,
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_locations.id"),
        nullable=True,
        index=True,
    )
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    receipt_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("receipt_items.id"),
        nullable=True,
        index=True,
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    operation: Mapped["InventoryOperation"] = relationship(back_populates="movements")
    batch: Mapped["InventoryBatch | None"] = relationship(back_populates="movements")
    product: Mapped["Product"] = relationship()  # type: ignore[name-defined]
    location: Mapped["InventoryLocation | None"] = relationship()
