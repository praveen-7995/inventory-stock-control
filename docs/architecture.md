# Architecture

## Moving pieces

Two deployables, talking over plain HTTPS/JSON:

1. **Backend** — FastAPI (Python) + SQLAlchemy ORM, backed by SQLite locally and
   Postgres in production (same `DATABASE_URL`-driven code path either way).
   Stateless: every request carries a JWT in the `Authorization` header, so any
   number of backend instances could sit behind a load balancer with no shared
   session state.
2. **Frontend** — a React SPA (Vite build) that talks to the backend exclusively
   through `src/api.js`, a thin fetch wrapper. No server-side rendering, no
   backend-for-frontend layer — the SPA calls the API directly.

There is no message queue, cache, or background worker. At this scale (a
single business, a handful of locations, human-paced stock movements) a
request/response API is enough; see schema.md for what would force a
different shape.

## Where each piece runs

- Backend: any host that can run a long-lived Python process behind a port
  (Render, Fly.io, a plain VM). Needs one env var pointing at Postgres
  (`DATABASE_URL`), a `JWT_SECRET`, and `CORS_ORIGINS` set to the frontend's
  deployed origin.
- Database: managed Postgres (e.g. Supabase). Nothing backend-specific lives
  in the DB beyond what SQLAlchemy creates from `app/models.py`.
- Frontend: a static host (Vercel/Netlify/anything that serves a `dist/`
  folder). `VITE_API_URL` is baked in at build time.

## Request path: recording a transfer

This is the most involved write path, so it's the representative one.

1. Staff member on the item detail page fills in the "record a movement"
   form (kind=transfer, quantity, from/to location) and submits.
2. `api.createMovement` POSTs JSON to `/movements` with the JWT attached.
3. `get_current_user` decodes the JWT, loads the `User` row.
4. `movements.create_movement` loads the `Item`, runs `_validate_movement`
   (shape checks: quantity sign, required fields for this kind).
5. `assert_can_act_on_transfer` checks the user is a manager, or is assigned
   to at least one of the two locations — a 403 short-circuits everything
   below if not.
6. `on_hand_by_location_for_item` sums the ledger for that item at the
   source location; if the transfer would take it negative, the whole
   request is refused with a 400 — nothing is written.
7. A single `StockMovement` row is inserted (transfers are one row with
   `from_location_id`/`to_location_id`, not two rows — see decisions.md).
8. `_refresh_alert_state` re-checks whether this movement pushed on-hand
   back above the reorder level, clearing a stale dismissal if so.
9. The transaction commits; the response includes the recorder's name
   (denormalised into the response, not the row) for the ledger UI.
10. The frontend re-fetches the item, its movement list, and its history
    in parallel and re-renders.

Every other write (receipt, issue, adjustment, item edit, archive) follows
the same shape: validate → authorize → check the derived on-hand invariant
→ write → commit. Reads never touch anything but derived data (see
schema.md's note on why on-hand is never stored).

## What I decided not to build

- **No refresh tokens / token rotation.** A 12-hour JWT expiry is enough for
  a demo and for a single shift; a real deployment would want short-lived
  access tokens plus a refresh flow, but that's meaningfully more surface
  area (revocation, rotation, storage) for a take-home.
- **No soft-delete or hard-delete of items at all** — only archive/restore.
  The brief is explicit that history must never be destroyable, and the
  simplest way to guarantee that is to never expose a delete path in the
  first place.
- **No websocket/live-push for alerts.** The sidebar polls `/alerts` every
  30 seconds instead of pushing. Good enough for a handful of concurrent
  users; wouldn't be for hundreds.
- **No email/notification system for low-stock alerts** — the brief asks for
  alerts to be visible in the app, not delivered out-of-band. Adding that
  later is additive, not a rearchitecture.
- **No multi-tenant/organisation layer.** One deployment = one business,
  matching the brief's scenario. Every table would need a `tenant_id` and
  every query a tenant filter to change that.
