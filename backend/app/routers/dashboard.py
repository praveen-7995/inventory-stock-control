import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, StockMovement, MovementKind, User
from app.schemas import DashboardOut
from app.deps import get_current_user
from app.stock import (
    on_hand_totals_by_item, on_hand_breakdown_by_category, on_hand_breakdown_by_location,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    now = dt.datetime.now(dt.timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - dt.timedelta(days=7)

    active_items = db.query(func.count(Item.id)).filter(Item.is_archived.is_(False)).scalar()

    on_hand_map = on_hand_totals_by_item(db)
    items_by_id = {i.id: i for i in db.query(Item).filter(Item.is_archived.is_(False)).all()}
    at_or_below = sum(
        1 for item_id, item in items_by_id.items()
        if on_hand_map.get(item_id, 0) <= item.reorder_level
    )

    movements_today = (
        db.query(func.count(StockMovement.id))
        .filter(StockMovement.created_at >= today_start)
        .scalar()
    )

    distinct_this_week = (
        db.query(func.count(func.distinct(StockMovement.item_id)))
        .filter(StockMovement.created_at >= week_start)
        .scalar()
    )

    weekly = []
    for i in range(7, -1, -1):
        bucket_end = now - dt.timedelta(weeks=i)
        bucket_start = bucket_end - dt.timedelta(weeks=1)
        receipts = (
            db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
            .filter(
                StockMovement.kind == MovementKind.receipt,
                StockMovement.created_at >= bucket_start,
                StockMovement.created_at < bucket_end,
            )
            .scalar()
        )
        issues = (
            db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
            .filter(
                StockMovement.kind == MovementKind.issue,
                StockMovement.created_at >= bucket_start,
                StockMovement.created_at < bucket_end,
            )
            .scalar()
        )
        weekly.append({
            "week_ending": bucket_end.date().isoformat(),
            "receipts": int(receipts or 0),
            "issues": int(issues or 0),
        })

    return DashboardOut(
        active_items=active_items or 0,
        items_at_or_below_reorder=at_or_below,
        movements_today=movements_today or 0,
        distinct_items_moved_this_week=distinct_this_week or 0,
        on_hand_by_category=on_hand_breakdown_by_category(db),
        on_hand_by_location=on_hand_breakdown_by_location(db),
        weekly_receipt_issue_volume=weekly,
    )
