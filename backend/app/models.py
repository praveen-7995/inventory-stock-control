import enum
import datetime as dt

from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Text,
    UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


class Role(str, enum.Enum):
    manager = "manager"
    staff = "staff"


class MovementKind(str, enum.Enum):
    receipt = "receipt"
    issue = "issue"
    transfer = "transfer"
    adjustment = "adjustment"


class HistoryEvent(str, enum.Enum):
    created = "created"
    field_change = "field_change"
    note = "note"
    archived = "archived"
    restored = "restored"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    assignments = relationship("LocationAssignment", back_populates="user", cascade="all, delete-orphan")


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    assignments = relationship("LocationAssignment", back_populates="location", cascade="all, delete-orphan")


class LocationAssignment(Base):
    """Many-to-many: which staff can act at which locations."""
    __tablename__ = "location_assignments"
    __table_args__ = (UniqueConstraint("user_id", "location_id", name="uq_user_location"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="assignments")
    location = relationship("Location", back_populates="assignments")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    items = relationship("Item", back_populates="category")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    sku = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    unit_of_measure = Column(String, nullable=False)
    reorder_level = Column(Integer, nullable=False, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # Reset to False whenever on-hand rises back above reorder_level.
    # This is what lets a dismissed alert legitimately reappear later,
    # instead of being permanently silenced. See docs/decisions.md.
    alert_dismissed = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    category = relationship("Category", back_populates="items")
    movements = relationship("StockMovement", back_populates="item", cascade="all, delete-orphan")
    history = relationship("ItemHistoryEntry", back_populates="item", cascade="all, delete-orphan")


class StockMovement(Base):
    """
    Append-only ledger. Rows are never updated or deleted by application code
    (no update/delete endpoint exists for this table at all).

    Sign convention: `quantity` is always stored as the signed effect on the
    location(s) involved:
      - receipt:    +quantity at location_id
      - issue:      -quantity at location_id   (quantity stored positive, applied negative)
      - adjustment: quantity can be positive or negative, applied as-is at location_id
      - transfer:   -quantity at from_location_id, +quantity at to_location_id
    """
    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint("quantity != 0", name="ck_quantity_nonzero"),
    )

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    kind = Column(Enum(MovementKind), nullable=False)
    quantity = Column(Integer, nullable=False)  # magnitude for receipt/issue/transfer; signed for adjustment

    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # receipt/issue/adjustment
    from_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # transfer only
    to_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # transfer only

    reason = Column(String, nullable=True)  # required (enforced in app) for adjustment
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    item = relationship("Item", back_populates="movements")


class ItemHistoryEntry(Base):
    """
    Immutable audit trail for an item: creation, field edits, archive/restore,
    and free-text notes staff leave. No update/delete endpoint touches this table.
    """
    __tablename__ = "item_history_entries"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    event_type = Column(Enum(HistoryEvent), nullable=False)
    field_name = Column(String, nullable=True)
    old_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    item = relationship("Item", back_populates="history")
