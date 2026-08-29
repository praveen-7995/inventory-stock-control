"""
Seeds enough demo data to show the system doing something real:
- 1 manager, 2 staff (each assigned to a different location)
- 3 locations, 5 categories, ~12 items
- A few weeks of receipts/issues/transfers/adjustments so the dashboard
  charts and low-stock alerts have something to show, including at least
  one item that is deliberately below its reorder level.

Run with: python -m app.seed
"""
import datetime as dt
import random

from app.database import SessionLocal, Base, engine
from app.models import (
    User, Role, Location, LocationAssignment, Category, Item,
    StockMovement, MovementKind, HistoryEvent, ItemHistoryEntry,
)
from app.auth import hash_password
from app.stock import on_hand_total_for_item, on_hand_by_location_for_item

random.seed(7)


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).first():
            print("Database already has data - skipping seed.")
            return

        manager = User(email="manager@example.com", hashed_password=hash_password("password123"),
                        name="Priya Manager", role=Role.manager)
        staff1 = User(email="staff1@example.com", hashed_password=hash_password("password123"),
                      name="Alex Warehouse", role=Role.staff)
        staff2 = User(email="staff2@example.com", hashed_password=hash_password("password123"),
                      name="Sam Retail", role=Role.staff)
        db.add_all([manager, staff1, staff2])
        db.flush()

        main_wh = Location(name="Main Warehouse")
        retail_a = Location(name="Retail Store A")
        retail_b = Location(name="Retail Store B")
        db.add_all([main_wh, retail_a, retail_b])
        db.flush()

        db.add_all([
            LocationAssignment(user_id=staff1.id, location_id=main_wh.id),
            LocationAssignment(user_id=staff2.id, location_id=retail_a.id),
            LocationAssignment(user_id=staff2.id, location_id=retail_b.id),
        ])

        categories = [Category(name=n) for n in ["Beverages", "Snacks", "Cleaning", "Stationery", "Hardware"]]
        db.add_all(categories)
        db.flush()
        cat_by_name = {c.name: c for c in categories}

        items_data = [
            ("BEV-001", "Sparkling Water 500ml", "Beverages", "case", 20),
            ("BEV-002", "Cold Brew Coffee 1L", "Beverages", "bottle", 15),
            ("SNK-001", "Trail Mix 200g", "Snacks", "bag", 30),
            ("SNK-002", "Granola Bars (box of 12)", "Snacks", "box", 10),
            ("CLN-001", "All-Purpose Cleaner 1L", "Cleaning", "bottle", 12),
            ("CLN-002", "Paper Towels (6-pack)", "Cleaning", "pack", 8),
            ("STA-001", "Ballpoint Pens (box of 50)", "Stationery", "box", 5),
            ("STA-002", "Notebooks A5", "Stationery", "each", 25),
            ("HW-001", "Cable Ties (100-pack)", "Hardware", "pack", 6),
            ("HW-002", "LED Bulbs 9W", "Hardware", "each", 15),
            ("HW-003", "Duct Tape 48mm", "Hardware", "roll", 10),
            ("BEV-003", "Orange Juice 1L", "Beverages", "bottle", 18),
        ]

        items = []
        for sku, name, cat, uom, reorder in items_data:
            item = Item(sku=sku, name=name, unit_of_measure=uom, reorder_level=reorder,
                        category_id=cat_by_name[cat].id, created_by_id=manager.id)
            db.add(item)
            items.append(item)
        db.flush()

        for item in items:
            db.add(ItemHistoryEntry(item_id=item.id, event_type=HistoryEvent.created,
                                     new_value=f"{item.sku} / {item.name}", changed_by_id=manager.id))

        db.add(ItemHistoryEntry(
            item_id=items[0].id, event_type=HistoryEvent.note,
            note="Supplier confirmed weekly delivery on Mondays.", changed_by_id=manager.id,
        ))

        now = dt.datetime.now(dt.timezone.utc)

        # 8 weeks of receipts into the warehouse + issues/transfers out to
        # stores. Balances are tracked in-process so we never accidentally
        # generate demo data that violates the app's own "never negative"
        # invariant.
        balances = {item.id: {main_wh.id: 0, retail_a.id: 0, retail_b.id: 0} for item in items}

        for week in range(8, 0, -1):
            week_start = now - dt.timedelta(weeks=week)
            for item in items:
                bal = balances[item.id]
                if random.random() < 0.85:
                    qty = random.randint(20, 60)
                    db.add(StockMovement(
                        item_id=item.id, kind=MovementKind.receipt, quantity=qty,
                        location_id=main_wh.id, recorded_by_id=staff1.id,
                        created_at=week_start + dt.timedelta(days=random.randint(0, 2)),
                    ))
                    bal[main_wh.id] += qty
                if random.random() < 0.6 and bal[main_wh.id] > 0:
                    dest = random.choice([retail_a, retail_b])
                    transfer_qty = min(random.randint(5, 15), bal[main_wh.id])
                    db.add(StockMovement(
                        item_id=item.id, kind=MovementKind.transfer, quantity=transfer_qty,
                        from_location_id=main_wh.id, to_location_id=dest.id, recorded_by_id=manager.id,
                        created_at=week_start + dt.timedelta(days=random.randint(2, 4)),
                    ))
                    bal[main_wh.id] -= transfer_qty
                    bal[dest.id] += transfer_qty
                issue_loc = random.choice([retail_a, retail_b])
                if random.random() < 0.7 and bal[issue_loc.id] > 0:
                    issue_qty = min(random.randint(1, 6), bal[issue_loc.id])
                    db.add(StockMovement(
                        item_id=item.id, kind=MovementKind.issue, quantity=issue_qty,
                        location_id=issue_loc.id, recorded_by_id=staff2.id,
                        created_at=week_start + dt.timedelta(days=random.randint(4, 6)),
                    ))
                    bal[issue_loc.id] -= issue_qty

        db.flush()

        # Push two items at/below their reorder level on purpose, so alerts
        # have something real to show, by issuing down whatever is sitting
        # at the warehouse.
        for item in items[:2]:
            bal = balances[item.id]
            total = sum(bal.values())
            target = max(item.reorder_level - 3, 0)
            issue_qty = min(bal[main_wh.id], max(total - target, 0))
            if issue_qty > 0:
                db.add(StockMovement(
                    item_id=item.id, kind=MovementKind.issue, quantity=issue_qty,
                    location_id=main_wh.id, recorded_by_id=staff1.id, created_at=now - dt.timedelta(days=1),
                ))

        # One adjustment with a reason, to demonstrate that rule.
        db.add(StockMovement(
            item_id=items[3].id, kind=MovementKind.adjustment, quantity=-3,
            location_id=main_wh.id, reason="Damaged in storage - discarded 3 units",
            recorded_by_id=manager.id, created_at=now - dt.timedelta(days=2),
        ))

        db.commit()
        print("Seed complete.")
        print("Manager login: manager@example.com / password123")
        print("Staff logins:  staff1@example.com / password123 (Main Warehouse)")
        print("               staff2@example.com / password123 (Retail Store A & B)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
