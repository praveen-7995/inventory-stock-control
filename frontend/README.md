# Frontend (React + Vite)

## Local dev

```bash
npm install
cp .env.example .env   # point VITE_API_URL at your backend
npm run dev
```

Runs at http://localhost:5173, expects the backend at the URL in `.env` (defaults to http://localhost:8000).

## Build

```bash
npm run build   # outputs to dist/
```

## Structure

- `src/api.js` — thin fetch wrapper around every backend endpoint.
- `src/context/AuthContext.jsx` — holds the JWT + current user, persisted in `localStorage`.
- `src/components/RouteGuards.jsx` — `RequireAuth` / `RequireManager` route wrappers.
- `src/components/Layout.jsx` — sidebar nav, polls `/alerts` every 30s for the badge count.
- `src/pages/` — one file per screen (Dashboard, ItemsList, ItemDetail, Alerts, ImportExport, Admin).

## Deploying (e.g. Vercel/Netlify)

Set `VITE_API_URL` to your deployed backend's URL as a build-time environment variable, then build and deploy the `dist/` folder as a static site.
