from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, Category, User, HistoryEvent, ItemHistoryEntry
from app.schemas import (
    ItemCreate, ItemUpdate, ItemOut, ItemListResponse, ItemNoteCreate, HistoryOut,
)
from app.deps import get_current_user, require_manager
from app.stock import on_hand_totals_by_item, on_hand_total_for_item

router = APIRouter(prefix="/items", tags=["items"])


def _to_item_out(item: Item, on_hand: int) -> ItemOut:
    return ItemOut(
        id=item.id, sku=item.sku, name=item.name, description=item.description,
        unit_of_measure=item.unit_of_measure, reorder_level=item.reorder_level,
        category_id=item.category_id, category_name=item.category.name,
        is_archived=item.is_archived, on_hand_total=on_hand,
    )


@router.get("", response_model=ItemListResponse)
def list_items(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="matches name or SKU"),
    category_id: Optional[int] = None,
    location_id: Optional[int] = None,
    archived: Optional[bool] = Query(None, description="filter by archived status; defaults to active items only"),
    at_or_below_reorder: bool = Query(False),
    sort_by: str = Query("name", pattern="^(name|on_hand|reorder_level)$"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """
    Every filter/search/sort/pagination happens in the database, not in the
    browser (goal #6). location_id filters to items that have at least one
    ledger movement touching that location; on-hand/reorder sorting and the
    at-or-below-reorder filter both operate on the same derived on-hand
    figure that the rest of the app uses (see app/stock.py).
    """
    on_hand_map = on_hand_totals_by_item(db)

    query = db.query(Item).join(Category)

    if search:
        like = f"%{search.strip()}%"
        query = query.filter(or_(Item.name.ilike(like), Item.sku.ilike(like)))
    if category_id is not None:
        query = query.filter(Item.category_id == category_id)
    # Goal #2: archiving removes an item from day-to-day lists. Unless the
    # caller explicitly asks to see archived items (archived=true) or
    # explicitly asks for everything (archived left as a query string like
    # "" is not supported - the two valid explicit values are true/false),
    # the default view only shows active items.
    if archived is None:
        query = query.filter(Item.is_archived.is_(False))
    else:
        query = query.filter(Item.is_archived == archived)
    if location_id is not None:
        from app.models import StockMovement
        item_ids_at_location = (
            db.query(StockMovement.item_id)
            .filter(
                or_(
                    StockMovement.location_id == location_id,
                    StockMovement.from_location_id == location_id,
                    StockMovement.to_location_id == location_id,
                )
            )
            .distinct()
        )
        query = query.filter(Item.id.in_(item_ids_at_location))

    all_matching = query.all()

    if at_or_below_reorder:
        all_matching = [i for i in all_matching if on_hand_map.get(i.id, 0) <= i.reorder_level]

    reverse = sort_dir == "desc"
    if sort_by == "name":
        all_matching.sort(key=lambda i: i.name.lower(), reverse=reverse)
    elif sort_by == "reorder_level":
        all_matching.sort(key=lambda i: i.reorder_level, reverse=reverse)
    else:  # on_hand
        all_matching.sort(key=lambda i: on_hand_map.get(i.id, 0), reverse=reverse)

    total = len(all_matching)
    start = (page - 1) * page_size
    page_items = all_matching[start:start + page_size]

    return ItemListResponse(
        total=total,
        items=[_to_item_out(i, on_hand_map.get(i.id, 0)) for i in page_items],
    )


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: Session = Depends(get_db), current_user: User = Depends(require_manager)):
    category = db.get(Category, payload.category_id)
    if not category:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown category_id")

    item = Item(
        sku=payload.sku.strip(), name=payload.name.strip(), description=payload.description,
        unit_of_measure=payload.unit_of_measure.strip(), reorder_level=payload.reorder_level,
        category_id=payload.category_id, created_by_id=current_user.id,
    )
    db.add(item)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "SKU already exists")

    db.add(ItemHistoryEntry(
        item_id=item.id, event_type=HistoryEvent.created,
        new_value=f"{item.sku} / {item.name}", changed_by_id=current_user.id,
    ))
    db.commit()
    db.refresh(item)
    return _to_item_out(item, 0)


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    return _to_item_out(item, on_hand_total_for_item(db, item_id))


@router.patch("/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db),
                 current_user: User = Depends(require_manager)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    if item.is_archived:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot edit an archived item; restore it first")

    changes = payload.model_dump(exclude_unset=True)
    for field, new_value in changes.items():
        old_value = getattr(item, field)
        if field == "category_id":
            new_category = db.get(Category, new_value)
            if not new_category:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown category_id")
            if old_value != new_value:
                db.add(ItemHistoryEntry(
                    item_id=item.id, event_type=HistoryEvent.field_change, field_name="category",
                    old_value=item.category.name, new_value=new_category.name,
                    changed_by_id=current_user.id,
                ))
            setattr(item, field, new_value)
        else:
            if old_value != new_value:
                db.add(ItemHistoryEntry(
                    item_id=item.id, event_type=HistoryEvent.field_change, field_name=field,
                    old_value=str(old_value), new_value=str(new_value),
                    changed_by_id=current_user.id,
                ))
            setattr(item, field, new_value)

    db.commit()
    db.refresh(item)
    return _to_item_out(item, on_hand_total_for_item(db, item_id))


@router.post("/{item_id}/archive", response_model=ItemOut)
def archive_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_manager)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    item.is_archived = True
    db.add(ItemHistoryEntry(item_id=item.id, event_type=HistoryEvent.archived, changed_by_id=current_user.id))
    db.commit()
    db.refresh(item)
    return _to_item_out(item, on_hand_total_for_item(db, item_id))


@router.post("/{item_id}/restore", response_model=ItemOut)
def restore_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_manager)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    item.is_archived = False
    db.add(ItemHistoryEntry(item_id=item.id, event_type=HistoryEvent.restored, changed_by_id=current_user.id))
    db.commit()
    db.refresh(item)
    return _to_item_out(item, on_hand_total_for_item(db, item_id))


@router.post("/{item_id}/notes", response_model=HistoryOut, status_code=status.HTTP_201_CREATED)
def add_note(item_id: int, payload: ItemNoteCreate, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    entry = ItemHistoryEntry(
        item_id=item_id, event_type=HistoryEvent.note, note=payload.note.strip(),
        changed_by_id=current_user.id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return HistoryOut(
        id=entry.id, event_type=entry.event_type, field_name=None, old_value=None, new_value=None,
        note=entry.note, changed_by_id=entry.changed_by_id, changed_by_name=current_user.name,
        created_at=entry.created_at,
    )


@router.get("/{item_id}/history", response_model=list[HistoryOut])
def get_history(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    entries = (
        db.query(ItemHistoryEntry)
        .filter(ItemHistoryEntry.item_id == item_id)
        .order_by(ItemHistoryEntry.created_at.asc())
        .all()
    )
    return [
        HistoryOut(
            id=e.id, event_type=e.event_type, field_name=e.field_name,
            old_value=e.old_value, new_value=e.new_value, note=e.note,
            changed_by_id=e.changed_by_id, changed_by_name=e.changed_by_id and db.get(User, e.changed_by_id).name,
            created_at=e.created_at,
        )
        for e in entries
    ]
