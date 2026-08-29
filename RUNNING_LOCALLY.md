# Running this locally

Two servers: the FastAPI backend on port 8000, the React frontend on port 5173.

## 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed              # creates inventory.db with demo data
uvicorn app.main:app --reload
```

Backend is now at http://localhost:8000 — visit http://localhost:8000/docs for interactive API docs.

## 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env            # already points at http://localhost:8000
npm run dev
```

Frontend is now at http://localhost:5173.

## Demo logins

| Role    | Email                 | Password    | Notes                           |
|---------|-----------------------|-------------|----------------------------------|
| Manager | praveennaik7995@gmail.com | password123 | full access, all locations   |
| Staff   | staff1@example.com    | password123 | assigned to Main Warehouse       |
| Staff   | staff2@example.com    | password123 | assigned to Retail Store A & B   |

## Resetting demo data

The seed script only runs if the database is empty. To start over:

```bash
cd backend
rm inventory.db
python -m app.seed
```

(Restart `uvicorn` afterwards if it was already running, since SQLite connections don't pick up a
replaced file cleanly.)

## What's not included

This checkpoint has not been deployed anywhere and `SUBMISSION.md` is intentionally left for you to
fill in once you've actually hosted it and reviewed the code — see `docs/plan.md` and
`docs/ai-prompts.md` for why.
