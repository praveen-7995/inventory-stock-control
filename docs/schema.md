# Schema

## Tables

**users** — `id, email (unique), hashed_password, name, role (manager|staff), is_active, created_at`

**locations** — `id, name (unique), created_at`

**location_assignments** — `id, user_id → users, location_id → locations, created_at`, unique on
`(user_id, location_id)`. Pure join table for the staff↔location many-to-many.

**categories** — `id, name (unique), created_at`

**items** — `id, sku (unique), name, description, unit_of_measure, reorder_level, category_id →
categories, is_archived, alert_dismissed, created_at, created_by_id → users`

**stock_movements** — `id, item_id → items, kind (receipt|issue|transfer|adjustment), quantity,
location_id → locations (nullable), from_location_id → locations (nullable), to_location_id →
locations (nullable), reason (nullable), recorded_by_id → users, created_at`. Check constraint:
`quantity != 0`. No `updated_at` — rows are never updated.

**item_history_entries** — `id, item_id → items, event_type (created|field_change|note|archived|
restored), field_name, old_value, new_value, note, changed_by_id → users, created_at`. Same
never-updated shape as the ledger.

## Relationships

- `users` ↔ `locations` — many-to-many, through `location_assignments`.
- `categories` → `items` — one-to-many. Deliberately *not* free text on the item (see decisions.md):
  a foreign key is the only way to guarantee "categories are a short list managers maintain."
- `items` → `stock_movements` — one-to-many, append-only.
- `items` → `item_history_entries` — one-to-many, append-only.
- `locations` is referenced three separate ways from one `stock_movements` row (`location_id` for
  single-location movements, `from_location_id`/`to_location_id` for transfers) rather than three
  separate tables, because a transfer is one event, not two.

## What the database enforces vs. what the app enforces

Database-level: uniqueness (SKU, email, category/location names, assignment pairs), foreign key
integrity, `quantity != 0`. These are the invariants that must hold no matter what code path writes
the row, including a future script or migration — the kind of thing a bug should never be able to
violate.

Application-level: everything relationship-dependent — role checks, location-assignment checks,
"a transfer can't overdraw the source location," "an adjustment needs a reason," "an archived item
can't take new movements," "on-hand is derived, never stored." None of these are single-row
constraints a `CHECK` clause could express cleanly; they all require reading other rows first
(the running ledger balance, the user's assignments), which is squarely application logic, and
SQLite (the dev database) doesn't support the same constraint surface Postgres does, so pushing
more into the DB layer would mean two different enforcement paths for dev vs. prod.

## What's deliberately denormalised

- **`on_hand_total` is never denormalised** — it's the one thing I was careful to *not* cache,
  since a stored running balance that can drift from the ledger is exactly the bug the brief calls
  out. Every read sums `stock_movements` fresh (see `app/stock.py`).
- **`recorded_by_name` / `changed_by_name` in API responses** are denormalised at the response layer
  (a join at read time), not stored — this is a read-model convenience, not a schema decision.
- **Category and location names are looked up, not embedded** in movement/history rows — only the
  IDs are stored, so renaming a category doesn't require rewriting history. This is the opposite of
  denormalisation, and deliberately so: history has to reflect reality at read time using current
  names, since nothing in the brief asks for a point-in-time snapshot of the category's name.

## What breaks first at 100x the data

`app/stock.py`'s aggregation queries (`GROUP BY item_id` / `GROUP BY location_id` over a `UNION ALL`
of the ledger) scale fine — they're just indexed sums. The thing that actually breaks first is the
items-list endpoint: it currently loads every row matching the filters into Python (`query.all()`)
and does sorting/pagination/the at-or-below-reorder filter in application code, not SQL, specifically
so that reorder-based filtering and on-hand-based sorting could share the same derived-quantity
helper as the rest of the app. That's an explicit, documented trade-off at seed-data scale (dozens of
items) — at 100x the catalog size it would need to become a real SQL query (a materialised on-hand
view, or computing on-hand in the same query via a lateral join) instead of a Python list comprehension
over every row that matched the WHERE clause.
