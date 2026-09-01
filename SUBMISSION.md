# Submission

Fill this in and commit it. This is the first file we open.

## Links

- **GitHub repository:** https://github.com/praveen-7995/inventory-stock-control
- **Live application:** Not deployed yet

## Notes for the reviewer

The application can be run locally using the instructions in `RUNNING_LOCALLY.md`.

The repository contains the complete React frontend, FastAPI backend, documentation, seed data, and demo credentials.

The application has been tested locally using the seeded demo data and the main inventory workflows.

## Demo credentials

| Role | Email | Password |
|---|---|---|
| Manager | praveennaik7995@gmail.com | password123 |
| Staff | staff1@example.com | password123 |
| Staff | staff2@example.com | password123 |

Created by `backend/app/seed.py`.

The Manager has full access to all locations. Staff1 is assigned to Main Warehouse only. Staff2 is assigned to Retail Store A and B.

## Stack

| Layer | What was used | Why |
|---|---|---|
| Frontend | React 19 + Vite, React Router, Recharts | Fast development with a lightweight frontend stack and dashboard charting support. |
| Backend | FastAPI + SQLAlchemy 2.0, JWT authentication using python-jose, bcrypt/passlib | Fast API development, automatic OpenAPI documentation, and structured database access. |
| Database | SQLite for local development / PostgreSQL for production | SQLite provides zero-setup local development, while the same application can use PostgreSQL through `DATABASE_URL`. |
| Hosting | Not deployed yet | The application is currently configured for local development. |

## Goal checklist

*The following checklist reflects my review and testing of the implemented application. The main workflows were tested locally against a running backend. The reviewer can re-run the application using `RUNNING_LOCALLY.md` and verify the workflows through the API and frontend.*

| # | Goal | Status | Notes |
|---|---|---|---|
| 1 | Accounts, roles, permissions | Done | Login/JWT authentication, manager-only actions, user creation, and location-based staff permissions are enforced server-side. |
| 2 | Item catalog (CRUD, categories, archive/restore) | Done | Categories are managed through a foreign key. Archived items are excluded from the default list while their history is preserved. |
| 3 | Stock movements (receipt/issue/transfer/adjustment) | Done | Receipt, issue, transfer, and adjustment movements are implemented with type-specific validation. |
| 4 | Append-only ledger, on-hand never stored/edited | Done | Movements cannot be edited or deleted. On-hand stock is calculated from the movement ledger rather than stored as a separate editable value. |
| 5 | Location assignment (staff scoped, manager unrestricted) | Done | Managers manage staff assignments. Staff movement permissions are restricted based on their assigned locations. |
| 6 | Server-side search/filter/sort/pagination | Done | Search, filtering, sorting, and pagination are handled by the backend. |
| 7 | Bulk CSV import/export | Done | CSV import provides per-row success/failure reporting, and stock export includes item/location combinations including zero-balance rows. |
| 8 | Dashboard metrics | Done | Dashboard includes active items, reorder information, movement metrics, category/location breakdowns, and receipt/issue trends. |
| 9 | Immutable audit history per item | Done | Item creation, field changes, archive/restore actions, and notes are recorded in the audit history. |
| 10 | Low-stock alerts with dismiss/reappear | Done | Low-stock alerts support manager dismissal and reappear when the stock condition becomes relevant again. |

## How much time did you actually spend?

Approximately 10 hours, including reviewing the assignment requirements, understanding the backend and frontend, running the application locally, testing the main workflows, reviewing the documentation, and preparing the repository for submission.

## What would you do next, with another 12 hours?

I would prioritize adding a comprehensive automated test suite for the backend, especially for authentication and permissions, stock-balance validation, transfers, adjustments, CSV imports, and low-stock alerts.

I would also add GitHub Actions for continuous integration, improve frontend validation and error handling, and deploy the application using PostgreSQL for production.

## What are you least happy with in this codebase, and why?

I am least happy with the lack of a comprehensive automated test suite. The main business rules were manually verified, but automated tests would make future changes safer and help catch regressions more reliably.

If I continued the project, adding backend unit tests and API integration tests would be one of my first priorities.