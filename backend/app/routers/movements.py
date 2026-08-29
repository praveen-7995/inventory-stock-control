from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import StockMovement, MovementKind, Item, Location, User
from app.schemas import MovementCreate, MovementOut
from app.deps import get_current_user, assert_can_act_at_location
from app.stock import on_hand_by_location_for_item, on_hand_total_for_item

router = APIRouter(prefix="/movements", tags=["movements"])


def _refresh_alert_state(db: Session, item: Item) -> None:
    """
    Goal #10: once dismissed, an alert must stay dismissed only until stock
    rises back above the reorder level. As soon as it does, clear the
    dismissal so a later drop back to/below reorder shows up again.
    """
    if item.alert_dismissed and on_hand_total_for_item(db, item.id) > item.reorder_level:
        item.alert_dismissed = False


def _validate_movement(db: Session, payload: MovementCreate, item: Item) -> None:
    if item.is_archived:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot record movements against an archived item")

    if payload.quantity == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Quantity must be non-zero")

    if payload.kind in (MovementKind.receipt, MovementKind.issue):
        if payload.quantity <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Quantity must be positive for receipt/issue")
        if not payload.location_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "location_id is required")
        if payload.from_location_id or payload.to_location_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "from/to location only apply to transfers")

    elif payload.kind == MovementKind.adjustment:
        if not payload.reason or not payload.reason.strip():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Adjustments must include a reason")
        if not payload.location_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "location_id is required")

    elif payload.kind == MovementKind.transfer:
        if payload.quantity <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Quantity must be positive for transfers")
        if not payload.from_location_id or not payload.to_location_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "from_location_id and to_location_id are required")
        if payload.from_location_id == payload.to_location_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Source and destination must differ")
        if payload.location_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "location_id does not apply to transfers; use from/to")


@router.post("", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def create_movement(payload: MovementCreate, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    item = db.get(Item, payload.item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")

    _validate_movement(db, payload, item)

    # Server-side role/location enforcement (goal #1 and #5): staff may only
    # act at locations they're assigned to; managers can act anywhere.
    # Staff may also never record adjustments at all - only receipts,
    # issues, and transfers.
    if payload.kind == MovementKind.adjustment and current_user.role.value != "manager":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only managers can record adjustments")

    if payload.kind == MovementKind.transfer:
        assert_can_act_at_location(db, current_user, payload.from_location_id)
        assert_can_act_at_location(db, current_user, payload.to_location_id)
        for loc_id in (payload.from_location_id, payload.to_location_id):
            if not db.get(Location, loc_id):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown location_id {loc_id}")
    else:
        assert_can_act_at_location(db, current_user, payload.location_id)
        if not db.get(Location, payload.location_id):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown location_id {payload.location_id}")

    # A transfer is a single indivisible operation: refuse it outright if it
    # would drive the source location negative. It never partially applies.
    if payload.kind == MovementKind.transfer:
        current_at_source = on_hand_by_location_for_item(db, item.id, payload.from_location_id)
        if current_at_source - payload.quantity < 0:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Transfer refused: only {current_at_source} on hand at source location",
            )
    elif payload.kind == MovementKind.issue:
        current_at_location = on_hand_by_location_for_item(db, item.id, payload.location_id)
        if current_at_location - payload.quantity < 0:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Issue refused: only {current_at_location} on hand at that location",
            )
    elif payload.kind == MovementKind.adjustment and payload.quantity < 0:
        current_at_location = on_hand_by_location_for_item(db, item.id, payload.location_id)
        if current_at_location + payload.quantity < 0:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Adjustment refused: would drive on-hand below zero (currently {current_at_location})",
            )

    movement = StockMovement(
        item_id=item.id, kind=payload.kind, quantity=payload.quantity,
        location_id=payload.location_id if payload.kind != MovementKind.transfer else None,
        from_location_id=payload.from_location_id if payload.kind == MovementKind.transfer else None,
        to_location_id=payload.to_location_id if payload.kind == MovementKind.transfer else None,
        reason=payload.reason, recorded_by_id=current_user.id,
    )
    db.add(movement)
    db.flush()

    _refresh_alert_state(db, item)

    db.commit()
    db.refresh(movement)

    return MovementOut(
        id=movement.id, item_id=movement.item_id, kind=movement.kind, quantity=movement.quantity,
        location_id=movement.location_id, from_location_id=movement.from_location_id,
        to_location_id=movement.to_location_id, reason=movement.reason,
        recorded_by_id=movement.recorded_by_id, recorded_by_name=current_user.name,
        created_at=movement.created_at,
    )


@router.get("/item/{item_id}", response_model=list[MovementOut])
def list_movements_for_item(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    movements = (
        db.query(StockMovement)
        .filter(StockMovement.item_id == item_id)
        .order_by(StockMovement.created_at.asc())
        .all()
    )
    return [
        MovementOut(
            id=m.id, item_id=m.item_id, kind=m.kind, quantity=m.quantity,
            location_id=m.location_id, from_location_id=m.from_location_id, to_location_id=m.to_location_id,
            reason=m.reason, recorded_by_id=m.recorded_by_id,
            recorded_by_name=db.get(User, m.recorded_by_id).name,
            created_at=m.created_at,
        )
        for m in movements
    ]
