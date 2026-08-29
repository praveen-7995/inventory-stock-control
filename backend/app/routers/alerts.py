from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, User
from app.schemas import AlertOut
from app.deps import get_current_user, require_manager
from app.stock import on_hand_totals_by_item

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    on_hand_map = on_hand_totals_by_item(db)
    items = db.query(Item).filter(Item.is_archived.is_(False)).all()
    alerts = []
    for item in items:
        on_hand = on_hand_map.get(item.id, 0)
        if on_hand <= item.reorder_level and not item.alert_dismissed:
            alerts.append(AlertOut(
                item_id=item.id, sku=item.sku, name=item.name,
                on_hand_total=on_hand, reorder_level=item.reorder_level,
            ))
    return alerts


@router.post("/{item_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_alert(item_id: int, db: Session = Depends(get_db), _: User = Depends(require_manager)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    item.alert_dismissed = True
    db.commit()
