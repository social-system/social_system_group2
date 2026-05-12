from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    purchased_at: Mapped[date] = mapped_column(Date, nullable=False)
    store_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    items_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    adjustment_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual_confirmed")
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

    items: Mapped[list["ReceiptItem"]] = relationship(
        back_populates="receipt",
        cascade="all, delete-orphan",
    )


class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipts.id"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounting_categories.id"),
        nullable=True,
    )
    raw_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    purchased_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    purchased_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    base_quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    base_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unit_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_total: Mapped[int] = mapped_column(Integer, nullable=False)
    is_inventory_target: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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

    receipt: Mapped["Receipt"] = relationship(back_populates="items")
    product: Mapped["Product | None"] = relationship(back_populates="receipt_items")
    category: Mapped["AccountingCategory | None"] = relationship(back_populates="receipt_items")


class AccountingCategory(Base):
    __tablename__ = "accounting_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    products: Mapped[list["Product"]] = relationship(back_populates="default_category")
    receipt_items: Mapped[list["ReceiptItem"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    default_base_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    default_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounting_categories.id"),
        nullable=True,
    )
    is_inventory_target: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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

    default_category: Mapped["AccountingCategory | None"] = relationship(back_populates="products")
    receipt_items: Mapped[list["ReceiptItem"]] = relationship(back_populates="product")
    aliases: Mapped[list["ProductAlias"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    unit_conversions: Mapped[list["ProductUnitConversion"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class ProductAlias(Base):
    __tablename__ = "product_aliases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    raw_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
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

    product: Mapped["Product"] = relationship(back_populates="aliases")


class ProductUnitConversion(Base):
    __tablename__ = "product_unit_conversions"
    __table_args__ = (
        UniqueConstraint("product_id", "from_unit", "to_unit", name="uq_product_unit_conversion"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    from_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    to_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
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

    product: Mapped["Product"] = relationship(back_populates="unit_conversions")
