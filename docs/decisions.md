# Decisions

## Decision 1

- **Chose:** On-hand quantity is never stored anywhere — it's always computed by summing the
  `stock_movements` ledger (`app/stock.py`).
- **Rejected:** A `current_quantity` column on `items` (or on a per-item-per-location table),
  updated whenever a movement is recorded.
- **Why:** The brief is explicit that on-hand must never be stored or edited directly, and the
  reason is real: a cached counter and an append-only ledger *will* drift apart the moment any
  write path forgets to update both (a bulk import, a bug, a manual DB fix). Deriving it from the
  ledger means there is only one source of truth, at the cost of summing rows on every read — an
  acceptable trade at this scale (see schema.md).

## Decision 2

- **Chose:** A transfer is one `stock_movements` row with both `from_location_id` and
  `to_location_id` set.
- **Rejected:** Two rows — a synthetic "issue" at the source and a synthetic "receipt" at the
  destination.
- **Why:** Two rows would need to be written atomically anyway (a transfer must never partially
  apply), so the two-row version buys nothing operationally, but it does lose information: a report
  built from two independent issue/receipt rows can no longer tell "this issue was actually half of
  a transfer" without extra bookkeeping. One row keeps the ledger's semantics matching the real-world
  event exactly.

## Decision 3

- **Chose:** Staff can record a transfer if they're assigned to *either* the source or the
  destination location, not necessarily both.
- **Rejected:** Requiring assignment to both ends of the transfer.
- **Why — and later reversed:** My first pass required both. Testing it against a realistic scenario
  (a warehouse worker shipping stock out to a store they don't personally staff) made it obvious that
  requiring both assignments would make the most common transfer in the business impossible for
  staff to record at all, forcing every transfer through a manager. The brief's own scenario is a
  business with a warehouse and multiple stores, which is exactly the shape this breaks. I changed
  the rule to require assignment to at least one side, on the theory that the person physically
  present at either end is the one who'd actually be entering the transfer.

## Decision 4

- **Chose:** Archived items are excluded from the default `/items` listing unless the caller
  explicitly passes `archived=true`.
- **Rejected:** Always returning every item and letting the frontend filter archived ones out.
- **Why — and later reversed:** My first pass left the `archived` filter defaulting to "no filter,"
  which technically satisfied "you can filter by archived status" but violated the more specific
  requirement one line above it — "archiving removes an item from day-to-day lists." I caught this
  auditing the API against the brief goal-by-goal rather than against my own schema, which is the
  actual gap: an endpoint can be internally consistent and still miss the point of the feature it's
  implementing.

## Decision 5

- **Chose:** SQLite for local development, Postgres in production, switched purely by
  `DATABASE_URL` — no code path branches on which one is active except the SQLite-only
  `connect_args` in `app/database.py`.
- **Rejected:** Requiring Postgres (via Docker) for local dev too, to avoid any dev/prod
  divergence.
- **Why:** Zero-setup local dev (`pip install && python -m app.seed && uvicorn ...`, no Docker,
  no separate DB service to run) mattered more for a project meant to be picked up and evaluated
  quickly than eliminating a small surface of divergence. The cost is real — the schema section
  notes that database-level constraint enforcement had to target the lowest common denominator
  between the two engines — but it's a bounded, understood cost, not an open-ended one.

## Decision 6

- **Chose:** Categories and locations are their own tables with a foreign key from `items`, managed
  through dedicated create endpoints, not free text fields on the item.
- **Rejected:** A plain `category` string column on `items`.
- **Why:** The brief states this directly — categories are a short list managers maintain, not free
  text typed per item — and a foreign key is the only structure that actually prevents "Beverages,"
  "beverages," and "Beverage" from silently becoming three different categories over time.
