# Submission

Fill this in and commit it. This is the first file we open.

## Links

- **GitHub repository:** <TODO — push this repo to a public GitHub repo and paste the URL>
- **Live application:** <TODO — deploy backend + frontend and paste the live URL>

## Notes for the reviewer

<TODO — fill in once deployed, e.g. if your host sleeps when idle and the first request is slow>

## Demo credentials

| Role    | Email                       | Password    |
|---------|------------------------------|-------------|
| Manager | praveennaik7995@gmail.com    | password123 |
| Staff   | staff1@example.com           | password123 |
| Staff   | staff2@example.com           | password123 |

(Created by `backend/app/seed.py` — Manager (Praveen Naik) has full access to all locations. Staff1
is assigned to Main Warehouse only. Staff2 is assigned to Retail Store A and B.)

## Stack

| Layer    | What was used                          | Why |
|----------|-----------------------------------------|-----|
| Frontend | React 19 + Vite, React Router, Recharts | Fast dev server, no build config needed, Recharts for the dashboard charts without a heavy charting dependency. |
| Backend  | FastAPI + SQLAlchemy 2.0, JWT auth (python-jose), bcrypt (passlib) | Async-capable, automatic OpenAPI docs at `/docs`, and SQLAlchemy's query builder made the ledger-aggregation logic in `app/stock.py` straightforward to express and keep in one place. |
| Database | SQLite (local dev) / Postgres (production, via `DATABASE_URL`) | Zero-setup local dev; same code path works against Postgres by changing one env var — see `docs/decisions.md` Decision 5. |
| Hosting  | <TODO — fill in once deployed, e.g. Render for backend + Supabase for Postgres + Vercel for frontend> | |

## Goal checklist

*The rows below are Claude's technical verification — every rule was exercised live against a running
instance via curl/API calls (see the conversation history for the actual commands and responses).
This is not a substitute for your own review — please re-run these checks yourself (or at least a
sample of them) before treating this table as your honest self-assessment, since "honestly" here
means your own confidence, not a passing test suite.*

| # | Goal | Status | Notes |
|---|------|--------|-------|
| 1 | Accounts, roles, permissions | Done | Login/JWT, manager-only item/location/adjustment/user creation, staff blocked from acting outside assigned locations — all enforced server-side, verified with 403s on every restricted action. |
| 2 | Item catalog (CRUD, categories, archive/restore) | Done | Categories are a managed FK, not free text. Archiving excludes an item from the default list but preserves full history; restore brings it back. |
| 3 | Stock movements (receipt/issue/transfer/adjustment) | Done | All four kinds implemented with kind-specific validation (adjustment requires a reason, transfer requires two distinct locations, etc). |
| 4 | Append-only ledger, on-hand never stored/edited | Done | No PATCH/DELETE endpoint exists on movements at all (confirmed 404). On-hand is always summed live from the ledger (`app/stock.py`), never cached. Transfers/issues/negative adjustments are rejected outright if they'd drive a location negative. |
| 5 | Location assignment (staff scoped, manager unrestricted) | Done | Manager-only assignment management; staff transfers require assignment to at least one side of the transfer (source or destination) — see `docs/decisions.md` Decision 3 for why this isn't "both sides." |
| 6 | Server-side search/filter/sort/pagination | Done | All computed in the backend; the browser only ever receives the current page. |
| 7 | Bulk CSV import/export | Done | Items and receipts import with per-row success/failure reporting — valid rows import even when others in the same file fail. Export includes every item/location pair, including zero-balance rows. |
| 8 | Dashboard metrics | Done | Active items, at/below-reorder count, movements today, distinct items moved this week, category/location breakdowns, 8-week receipt/issue chart. |
| 9 | Immutable audit history per item | Done | Creation, field changes (with old/new value and who), archive/restore, and notes are all logged; no edit/delete endpoint exists on history entries (confirmed 404). |
| 10 | Low-stock alerts with dismiss/reappear | Done | Manager-only dismiss; verified live that a dismissed alert reappears once stock rises above reorder level and then drops again. |

## How much time did you actually spend?

<TODO — this has to be your real number, including the time you spend actually reading and testing
the code per the study plan, not just the build time>

## What would you do next, with another 12 hours?

<TODO — your own answer. `docs/plan.md` and `docs/architecture.md` list what was cut (no automated
test suite, no CI, no refresh tokens) if you want a starting point, but say what *you'd* prioritize>

## What are you least happy with in this codebase, and why?

<TODO — your own answer. This is the one they'll probably follow up on in an interview, so it's worth
actually having an opinion here rather than a safe non-answer>
