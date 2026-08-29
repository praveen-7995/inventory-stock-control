# Plan

## How the work was actually done

Per the README's AI usage policy, this project was built end-to-end by Claude (Anthropic's AI
assistant), directed by me in a single continuous working session rather than spread across
multiple days. That's a real difference from how I'd normally pace a project like this, and it
means "sessions" below means phases within one sitting, not separate days. See `ai-prompts.md` for
what was actually asked and corrected along the way, and the closing questions in `SUBMISSION.md`
for how I'm accounting for that when judging my own understanding of the result.

## Order, and why

1. **Backend schema and models first.** Every one of the ten goals is really a statement about the
   ledger and its invariants (never stored on-hand, append-only history, transfers that can't
   overdraw). Getting the data model right first meant every later layer — API, then UI — was just
   exposing something already correct, instead of a UI decision forcing an awkward schema change
   later.
2. **Auth and role/location enforcement next**, before any business-logic endpoints, because almost
   every endpoint after this point needed `get_current_user` / `require_manager` /
   `assert_can_act_at_location` as a dependency. Building it last would have meant retrofitting auth
   checks into already-written handlers.
3. **The movements endpoint** (the ledger write path) before the simpler CRUD endpoints (categories,
   locations), since it's where all the interesting validation lives and where getting the order of
   checks wrong (authorize before or after computing on-hand?) actually matters.
4. **Seed data, then a manual smoke-test pass** against every business rule in the README (role
   enforcement, negative-balance rejection, adjustment reason requirement, alert dismiss/reappear,
   CSV partial-failure import) via curl, before writing a single line of frontend code — cheaper to
   find a backend bug from a curl command than by clicking through a UI built on top of it.
5. **A second, dedicated audit pass** reading the API back against the README's ten goals line by
   line, independent of my own schema/endpoint list, which is what caught the four real bugs
   described in `decisions.md` (default archived filter, transfer authorization, CSV export zero
   rows, missing user-creation endpoint). This step existed *because* the first pass tests the code
   I wrote against my own mental model of the spec, which reliably misses places where my model of
   the spec was itself wrong.
6. **Frontend last**, structured the same way: API client and auth context first (the plumbing every
   page needs), then pages roughly in the order a user would hit them (login → dashboard → items
   list → item detail → alerts/import-export → admin).

## What I cut

- **No automated test suite.** Every business rule was verified manually via curl during
  development (documented in the conversation, not committed as a script), which is real coverage
  but not regression protection. Given more time this is the first thing I'd add — the movement
  validation logic in particular is exactly the kind of thing that should have unit tests, since it
  has many small branches (four kinds × sign rules × role rules × balance checks).
- **No CI pipeline.** Nothing runs the backend or builds the frontend automatically on push.
- **No actual hosted deployment.** I don't have accounts to create a Render service, a Supabase
  project, or a Vercel deployment on the candidate's behalf — both READMEs include exact deploy
  steps, but running them is a step I'm handing back rather than one I skipped by mistake.
- **Refresh tokens.** A single 12-hour access token is enough for a demo shift; real rotation/
  revocation was cut as out of scope for the stated time budget.
