"""
On-hand quantity is NEVER stored. It is always derived by summing the
append-only stock_movements ledger. This module is the one place that
knows how to turn ledger rows into a quantity, so every part of the app
(item list, item detail, dashboard, alerts, transfer validation, CSV
export) agrees with each other by construction.

Each ledger row is normalised into one or two signed "legs" against a
location:
  - receipt:    +quantity @ location_id
  - issue:      -quantity @ location_id
  - adjustment: quantity (already signed) @ location_id
  - transfer:   -quantity @ from_location_id   AND   +quantity @ to_location_id
"""
from sqlalchemy import select, func, case, literal, union_all
from sqlalchemy.orm import Session

from app.models import StockMovement, MovementKind


def _legs_subquery():
    non_transfer = select(
        StockMovement.item_id.label("item_id"),
        StockMovement.location_id.label("location_id"),
        case(
            (StockMovement.kind == MovementKind.receipt, StockMovement.quantity),
            (StockMovement.kind == MovementKind.issue, -StockMovement.quantity),
            (StockMovement.kind == MovementKind.adjustment, StockMovement.quantity),
            else_=literal(0),
        ).label("signed_qty"),
    ).where(StockMovement.kind != MovementKind.transfer)

    transfer_out = select(
        StockMovement.item_id.label("item_id"),
        StockMovement.from_location_id.label("location_id"),
        (-StockMovement.quantity).label("signed_qty"),
    ).where(StockMovement.kind == MovementKind.transfer)

    transfer_in = select(
        StockMovement.item_id.label("item_id"),
        StockMovement.to_location_id.label("location_id"),
        StockMovement.quantity.label("signed_qty"),
    ).where(StockMovement.kind == MovementKind.transfer)

    return union_all(non_transfer, transfer_out, transfer_in).subquery()


def on_hand_totals_by_item(db: Session) -> dict[int, int]:
    """item_id -> on-hand summed across every location."""
    legs = _legs_subquery()
    rows = db.execute(
        select(legs.c.item_id, func.sum(legs.c.signed_qty)).group_by(legs.c.item_id)
    ).all()
    return {item_id: int(total or 0) for item_id, total in rows}


def on_hand_total_for_item(db: Session, item_id: int) -> int:
    legs = _legs_subquery()
    result = db.execute(
        select(func.sum(legs.c.signed_qty)).where(legs.c.item_id == item_id)
    ).scalar()
    return int(result or 0)


def on_hand_by_item_and_location(db: Session, item_id: int) -> dict[int, int]:
    """location_id -> on-hand for a single item, used for transfer validation."""
    legs = _legs_subquery()
    rows = db.execute(
        select(legs.c.location_id, func.sum(legs.c.signed_qty))
        .where(legs.c.item_id == item_id, legs.c.location_id.isnot(None))
        .group_by(legs.c.location_id)
    ).all()
    return {loc_id: int(total or 0) for loc_id, total in rows}


def on_hand_by_location_for_item(db: Session, item_id: int, location_id: int) -> int:
    return on_hand_by_item_and_location(db, item_id).get(location_id, 0)


def on_hand_breakdown_by_category(db: Session) -> list[dict]:
    from app.models import Item, Category

    legs = _legs_subquery()
    rows = db.execute(
        select(Category.name, func.coalesce(func.sum(legs.c.signed_qty), 0))
        .select_from(Item)
        .join(Category, Category.id == Item.category_id)
        .outerjoin(legs, legs.c.item_id == Item.id)
        .group_by(Category.name)
    ).all()
    return [{"category": name, "on_hand": int(total)} for name, total in rows]


def on_hand_breakdown_by_location(db: Session) -> list[dict]:
    from app.models import Location

    legs = _legs_subquery()
    rows = db.execute(
        select(Location.name, func.coalesce(func.sum(legs.c.signed_qty), 0))
        .select_from(Location)
        .outerjoin(legs, legs.c.location_id == Location.id)
        .group_by(Location.name)
    ).all()
    return [{"location": name, "on_hand": int(total)} for name, total in rows]
