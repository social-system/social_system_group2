# テーブル定義
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

# テーブル定義1(レシート全体)
class Receipt(Base):
    __tablename__ = "receipts"

    # レシートID(自動採番)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # レシート合計金額
    receipt_total: Mapped[int] = mapped_column(Integer, nullable=False)

    # 明細とのRelation
    items: Mapped[list["ReceiptItem"]] = relationship(
        back_populates="receipt",
        cascade="all, delete-orphan",
    )

# テーブル定義2(明細)
class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    # 明細ID(自動採番)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 親レシートへの外部キー
    receipt_id: Mapped[int] = mapped_column(
        ForeignKey("receipts.id"),
        nullable=False,
    )

    # 商品名
    item: Mapped[str] = mapped_column(String(255), nullable=False)

    # 数量
    num: Mapped[int] = mapped_column(Integer, nullable=False)

    # 単価
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    # 総額
    total: Mapped[int] = mapped_column(Integer, nullable=False)

    # 日付
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # 食材区分(整数フィールド)
    ingredients: Mapped[int] = mapped_column(Integer, nullable=False)

    receipt: Mapped["Receipt"] = relationship(back_populates="items")
