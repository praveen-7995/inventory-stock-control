import csv
import io

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, Category, Location, StockMovement, MovementKind, User, HistoryEvent, ItemHistoryEntry
from app.schemas import ImportReport, ImportRowResult
from app.deps import require_manager, get_current_user
from app.stock import on_hand_by_item_and_location, on_hand_totals_by_item

router = APIRouter(tags=["import-export"])


def _read_csv(file: UploadFile) -> list[dict]:
    raw = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))
    return list(reader)


@router.post("/import/items", response_model=ImportReport)
def import_items(file: UploadFile = File(...), db: Session = Depends(get_db),
                  current_user: User = Depends(require_manager)):
    """
    Expected columns: sku, name, description, unit_of_measure, reorder_level, category
    Every valid row is imported even if other rows in the same file fail.
    """
    rows = _read_csv(file)
    results: list[ImportRowResult] = []
    imported = 0

    categories_by_name = {c.name.lower(): c for c in db.query(Category).all()}
    existing_skus = {i.sku for i in db.query(Item.sku).all()}

    for idx, row in enumerate(rows, start=2):  # row 1 is the header
        try:
            sku = (row.get("sku") or "").strip()
            name = (row.get("name") or "").strip()
            uom = (row.get("unit_of_measure") or "").strip()
            category_name = (row.get("category") or "").strip()
            reorder_raw = (row.get("reorder_level") or "0").strip()

            if not sku:
                raise ValueError("sku is required")
            if sku in existing_skus:
                raise ValueError(f"sku '{sku}' already exists")
            if not name:
                raise ValueError("name is required")
            if not uom:
                raise ValueError("unit_of_measure is required")
            category = categories_by_name.get(category_name.lower())
            if not category:
                raise ValueError(f"unknown category '{category_name}'")
            try:
                reorder_level = int(reorder_raw)
                if reorder_level < 0:
                    raise ValueError()
            except ValueError:
                raise ValueError(f"reorder_level '{reorder_raw}' must be a non-negative integer")

            item = Item(
                sku=sku, name=name, description=(row.get("description") or "").strip() or None,
                unit_of_measure=uom, reorder_level=reorder_level, category_id=category.id,
                created_by_id=current_user.id,
            )
            db.add(item)
            db.flush()
            db.add(ItemHistoryEntry(
                item_id=item.id, event_type=HistoryEvent.created,
                new_value=f"{item.sku} / {item.name} (bulk import)", changed_by_id=current_user.id,
            ))
            existing_skus.add(sku)
            imported += 1
            results.append(ImportRowResult(row=idx, status="ok"))
        except Exception as exc:
            results.append(ImportRowResult(row=idx, status="error", message=str(exc)))

    db.commit()
    return ImportReport(total_rows=len(rows), imported=imported, failed=len(rows) - imported, results=results)


@router.post("/import/receipts", response_model=ImportReport)
def import_receipts(file: UploadFile = File(...), db: Session = Depends(get_db),
                     current_user: User = Depends(require_manager)):
    """
    Expected columns: sku, location, quantity
    Each valid row becomes one receipt movement. Bad rows are reported and
    skipped; good rows in the same file still go through.
    """
    rows = _read_csv(file)
    results: list[ImportRowResult] = []
    imported = 0

    items_by_sku = {i.sku: i for i in db.query(Item).all()}
    locations_by_name = {l.name.lower(): l for l in db.query(Location).all()}

    for idx, row in enumerate(rows, start=2):
        try:
            sku = (row.get("sku") or "").strip()
            location_name = (row.get("location") or "").strip()
            qty_raw = (row.get("quantity") or "").strip()

            item = items_by_sku.get(sku)
            if not item:
                raise ValueError(f"unknown sku '{sku}'")
            if item.is_archived:
                raise ValueError(f"item '{sku}' is archived")
            location = locations_by_name.get(location_name.lower())
            if not location:
                raise ValueError(f"unknown location '{location_name}'")
            try:
                quantity = int(qty_raw)
                if quantity <= 0:
                    raise ValueError()
            except ValueError:
                raise ValueError(f"quantity '{qty_raw}' must be a positive integer")

            db.add(StockMovement(
                item_id=item.id, kind=MovementKind.receipt, quantity=quantity,
                location_id=location.id, recorded_by_id=current_user.id,
            ))
            imported += 1
            results.append(ImportRowResult(row=idx, status="ok"))
        except Exception as exc:
            results.append(ImportRowResult(row=idx, status="error", message=str(exc)))

    db.commit()

    # Any item that received stock might now be above its reorder level;
    # clear stale dismissals the same way a single movement would.
    on_hand_map = on_hand_totals_by_item(db)
    for item in items_by_sku.values():
        if item.alert_dismissed and on_hand_map.get(item.id, 0) > item.reorder_level:
            item.alert_dismissed = False
    db.commit()

    return ImportReport(total_rows=len(rows), imported=imported, failed=len(rows) - imported, results=results)


@router.get("/export/stock")
def export_stock(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Current stock position: every item's on-hand quantity by location, as CSV."""
    items = db.query(Item).all()
    locations = db.query(Location).order_by(Location.name).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["sku", "item_name", "category", "location", "on_hand"])

    for item in items:
        per_location = on_hand_by_item_and_location(db, item.id)
        for location in locations:
            qty = per_location.get(location.id, 0)
            if qty == 0:
                continue
            writer.writerow([item.sku, item.name, item.category.name, location.name, qty])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=stock_position.csv"},
    )
