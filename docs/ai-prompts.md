# AI prompts

This entire project was built by Claude (Anthropic's AI assistant) at my direction, in a single
continuous conversation, per the README's stated AI usage policy. This log describes what was
actually asked and what came back, at the level of the real prompts, not a cleaned-up retelling.

## Initial build

### Prompt

Asked Claude to read the assignment's README and doc templates carefully, and build the full
application using React + FastAPI, meeting all ten stated goals. Explicitly said to skip filling
in `SUBMISSION.md` for the moment.

### What I got

A complete FastAPI backend in one extended pass: models, auth, all ten goals' worth of endpoints
(items, movements, locations, categories, assignments, dashboard, alerts, CSV import/export), a
seed script, and a manual curl-based smoke test of the trickier rules (role enforcement, transfer
negative-balance rejection, adjustment reason requirement, alert dismiss/reappear). It held up
correctly on first pass for the rules it explicitly tested.

### What I corrected

Nothing at this stage — I asked for a self-audit before accepting the result, described next.

## Auditing the backend against the README

### Prompt

Asked Claude to recheck the backend against the README requirements specifically (not just its own
test coverage) before packaging anything, and to fix what it found.

### What I got

Claude re-read the ten goals line by line against the actual endpoint behavior and found four real
gaps, detailed in `decisions.md`:

1. The items list didn't exclude archived items by default, which technically satisfied "you can
   filter by archived status" while missing "archiving removes an item from day-to-day lists."
2. Transfer authorization required staff to be assigned to *both* the source and destination
   location, which would make the most common real-world transfer (warehouse → a store the worker
   doesn't staff) impossible for any staff member to record.
3. The CSV stock export silently skipped rows where on-hand was zero, which doesn't match "every
   item's on-hand quantity by location."
4. There was no way to actually create a staff account through the API — only the seed script could.

### What I corrected

Asked Claude to fix all four, then re-verify the entire test suite (all ten goals, not just the four
fixes) against a *freshly reseeded* database, since the first re-verification attempt actually ran
against a stale SQLite file left over from earlier testing due to a process-restart ordering bug —
Claude caught that the numbers didn't match what a fresh seed should produce, traced it to the stale
file, and redid the verification properly before packaging the backend checkpoint. This is the
"produced something wrong and had to be corrected" case: the wrong result here wasn't in the
application code, it was in the verification process itself (testing against the wrong database
state), and it would have been easy to accept a false "all green" if the numbers hadn't been
double-checked against what the seed script should actually produce.

## Frontend build

### Prompt

Asked Claude to continue: build the React frontend and fill in the docs, having already reviewed
and approved the backend checkpoint.

### What I got

A full React SPA (login, dashboard with charts, items list, item detail with movement recording/
ledger/audit history, alerts, CSV import/export, and a manager admin panel), wired to the backend
API, that built cleanly with `vite build` and was checked against live backend responses via curl
to confirm the field names the frontend expects match what the API actually returns.

### What I corrected

Two mid-build design issues Claude caught and fixed itself rather than shipping and discovering
later:

- The `/locations` endpoint originally scoped results to a staff member's assigned locations only,
  which broke the item ledger UI's ability to show location *names* for transfers touching a
  location the viewing user isn't assigned to (e.g., a manager reviewing a transfer's destination).
  Viewing a location's name isn't a security concern — only recording a movement there is, and
  that's enforced server-side regardless of what any list endpoint returns — so `/locations` was
  opened up to all authenticated users, with a separate `/locations/mine` endpoint added
  specifically to scope the "record a movement" form's dropdowns to what a given user can actually
  act on.
- The movement-recording form's transfer fields originally reused the same "my locations" list for
  both the "from" and "to" dropdowns, which didn't reflect the backend's actual OR-based
  authorization rule (assigned to source **or** destination). Fixed so "from" is scoped to the
  user's own locations and "to" allows any location, matching the real rule instead of a stricter
  approximation of it.

## What I did not ask Claude to do

I did not ask Claude to fabricate a day-by-day git history, invent a hosting deployment it can't
actually perform, or write `SUBMISSION.md` on my behalf — those are the parts of this exercise that
have to come from me actually reading the code, deploying it, and being able to explain it, which is
the entire point of the "you are accountable for everything in your submission" line in the README.
