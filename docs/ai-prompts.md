# AI prompts

This project was developed with the assistance of Claude (Anthropic's AI assistant), following the
README's stated AI usage policy. I used Claude throughout the development process for implementation,
debugging, reviewing requirements, and documentation support. I also reviewed the generated code,
ran the application locally, tested the main workflows, and made decisions about what to accept or
change.

This document records the main prompts and the work that resulted from them.

## Initial project setup and backend implementation

### Prompt

Asked Claude to carefully read the assignment README and documentation templates and help build the
inventory management application using React + FastAPI. I asked it to focus first on the backend and
to implement the required inventory, authentication, locations, movements, dashboard, alerts, and
CSV functionality. I explicitly asked it not to complete `SUBMISSION.md` at this stage.

### What I got

Claude produced the initial FastAPI backend including:

- Authentication and JWT-based authorization
- User and role handling
- Items and categories
- Locations and staff assignments
- Stock movements
- Inventory/ledger calculations
- Dashboard endpoints
- Low-stock alerts
- CSV import/export
- Database models and schemas
- Seed data
- API documentation through FastAPI/OpenAPI

I then ran the backend locally and checked the main API workflows.

### What I did

I reviewed the generated backend structure and tested the important workflows locally,
including authentication, role permissions, stock movements, transfers, adjustments, and
low-stock behavior.

I also checked the project requirements against the actual implementation instead of relying
only on the generated code.

## Backend requirements audit and fixes

### Prompt

Asked Claude to audit the backend against every requirement in the assignment README and identify
anything that was missing or implemented incorrectly.

### What I found

The audit identified several issues that needed to be corrected:

1. Archived items were not excluded from the default item list.
2. Transfer authorization was stricter than the intended requirement because it required staff to
   be assigned to both locations.
3. CSV stock export skipped zero-balance item/location rows.
4. There was no API endpoint for creating staff accounts.

### What I did

I reviewed these findings and asked Claude to fix the identified issues.

After the fixes, I ran the backend again and rechecked the main requirements against a freshly
seeded database. During this process, I noticed that one verification run was using an old SQLite
database rather than a freshly seeded database. I stopped relying on that result, recreated the
database, and repeated the verification.

This was important because the test results could otherwise have looked correct while actually
being based on stale data.

### Result

The backend was rechecked after the fixes, including:

- Role and permission checks
- Transfer validation
- Negative-stock prevention
- Adjustment reason validation
- Archived item behavior
- CSV export behavior
- Staff account creation
- Low-stock alert behavior
- Append-only movement history

## Frontend implementation

### Prompt

After reviewing the backend, asked Claude to build the React frontend and connect it to the
existing FastAPI API.

I asked for the frontend to cover the main application workflows, including authentication,
dashboard, items, item details, stock movements, alerts, CSV import/export, and manager
administration.

### What I got

Claude produced a React SPA using:

- React
- Vite
- React Router
- Recharts
- API integration with the FastAPI backend

The frontend included:

- Login
- Dashboard
- Items list
- Item details
- Stock movement recording
- Movement ledger
- Audit history
- Low-stock alerts
- CSV import/export
- Manager administration

### What I did

I ran the frontend locally and checked that it communicated correctly with the backend.

I also reviewed the API responses and frontend expectations to make sure field names and data
structures matched.

## Frontend authorization and location handling

### What happened

While reviewing the movement and ledger functionality, I identified a problem with how locations
were being presented to users.

The frontend initially used the staff member's assigned locations for all location information.
This meant that a user reviewing a transfer could potentially be unable to see the name of a
destination location simply because they were not assigned to it.

### What I asked Claude to change

I asked Claude to separate:

- Locations that authenticated users can view
- Locations where a staff member is authorized to record movements

Claude changed the implementation so that authenticated users can retrieve location information
needed for viewing records, while `/locations/mine` is used for locations relevant to the user's
movement permissions.

The movement form was also changed so that transfer authorization matches the backend rule:
staff authorization can be based on the source or destination location rather than incorrectly
requiring both.

### What I did

I reviewed this behavior from the perspective of the actual application workflow and verified
that the frontend restrictions matched the backend authorization rules.

## Local testing and debugging

### What I did

I set up the project locally, created the Python virtual environment, installed the backend
dependencies, configured the environment variables, seeded the database, and ran the FastAPI
and React applications.

I tested the main workflows through the running application/API, including:

- Login
- Manager and staff permissions
- Item management
- Stock receipts
- Stock issues
- Transfers
- Adjustments
- Negative stock prevention
- Location assignments
- Search/filter/pagination
- CSV import/export
- Dashboard information
- Audit history
- Low-stock alerts

When an issue appeared during testing, I investigated the actual application behavior and used
Claude to help identify and fix implementation problems.

## Documentation

### Prompt

Asked Claude to help prepare the project documentation based on the implemented application,
including architecture, database schema, design decisions, development plan, and AI usage.

### What I did

I reviewed the generated documentation and adjusted it to match the actual implementation.

I also prepared the local-running instructions and reviewed the repository structure before
pushing the project to GitHub.

## GitHub and repository preparation

### What I did

I created the GitHub repository and pushed the project to:

https://github.com/praveen-7995/inventory-stock-control

I also reviewed the repository before pushing to make sure sensitive local files such as `.env`
and the Python virtual environment were excluded through `.gitignore`.

I checked that the backend, frontend, documentation, README files, and submission document were
included in the repository.

## Submission document

### Prompt

Used Claude to help review and improve the structure of `SUBMISSION.md`, while keeping the final
submission information based on my actual project status and testing.

### What I did

I personally filled/reviewed the submission information, including:

- GitHub repository link
- Local running instructions
- Demo credentials
- Technology stack
- Goal checklist
- Actual development/testing time
- Remaining improvements
- Areas of the codebase I would improve

The application has not been deployed yet, so I have not claimed a live application URL.

## What I did not ask Claude to do

I did not ask Claude to fabricate a development history, invent deployment information, or claim
that the application was deployed when it was not.

I also did not rely solely on Claude's generated test results. I ran the application locally,
reviewed the implementation, checked the main workflows, and corrected issues when they were
found.

The final repository and submission reflect the current state of the project that I actually
reviewed and tested.