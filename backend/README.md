# Backend (FastAPI)

## Local dev

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed        # creates inventory.db with demo data
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Demo logins (from seed)

| Role    | Email                 | Password    | Notes                         |
|---------|-----------------------|-------------|--------------------------------|
| Manager | manager@example.com   | password123 | full access, all locations     |
| Staff   | staff1@example.com    | password123 | assigned to Main Warehouse     |
| Staff   | staff2@example.com    | password123 | assigned to Retail Store A & B |

## Deploying (e.g. Render)

1. Create a Postgres database first (e.g. Supabase) and copy its connection string.
2. Set `DATABASE_URL`, `JWT_SECRET`, and `CORS_ORIGINS` (your frontend's deployed URL) as environment variables on the host.
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Run `python -m app.seed` once (e.g. via a one-off shell/job) to populate demo data.
