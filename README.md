## OW_BC – Bank Reconciliation Assistant

This project implements a **multi-user bank reconciliation assistant** that:

- Imports **bank statements** (PDF/CSV/XLS/XLSX) from multiple banks.
- Imports **administrative reports** (e.g. Fuerza Movil Excel files).
- Normalizes and matches transactions automatically (amount, date window, description, and `Referencia` substring logic).
- Provides a **review UI** for manual reconciliation and exports **audit reports**.
- Runs as a **two-tier web app** (frontend + backend) with a **PostgreSQL** database, deployed with **Docker Compose**.

All functional and technical details are captured in **OpenSpec** under `openspec/changes/bank-reconciliation-multi-tenant/` using a spec‑driven workflow.

---

## Architecture Overview

- **Frontend**
  - React + TypeScript + Vite (SPA).
  - Handles:
    - User registration/login/logout.
    - File uploads for bank statements and administrative reports.
    - Reconciliation workspace (matched / suggested / unmatched).
    - Manual confirm/reject flows and export downloads.

- **Backend**
  - Python **FastAPI** (REST API).
  - Responsibilities:
    - Auth (registration, login, logout, session management).
    - Multi-tenancy enforcement (tenant == user in MVP).
    - File uploads and storage (bank + admin reports).
    - Parsing & normalization (CSV/XLS/XLSX/PDF).
    - Matching engine (amount, date ±2 days, description similarity, `Referencia` substring).
    - Reconciliation workflow and audit logging.
    - Export generation (at least CSV).

- **Database**
  - **PostgreSQL**.
  - Stores:
    - Users, tenants, sessions.
    - Upload metadata and import jobs.
    - Normalized transactions and administrative entries.
    - Match candidates, reconciliations, and audit events.

- **Deployment & Ops**
  - `docker-compose.yml` (to be implemented) orchestrates:
    - `frontend` (built static assets served via a lightweight web server).
    - `backend` (FastAPI app container).
    - `db` (PostgreSQL with persistent volume).
    - Optional `migrate` job for DB migrations.
  - Configuration via environment variables / `.env` (DB credentials, secrets, CORS origin, upload limits).

---

## Spec‑Driven Development

This repo uses **OpenSpec** with the `spec-driven` schema.

Active change:

- `openspec/changes/bank-reconciliation-multi-tenant/`
  - `proposal.md` – Why and what changes.
  - `design.md` – How (architecture, tech choices, risks).
  - `specs/**/spec.md` – Capability specs:
    - `user-auth`, `multi-tenancy`, `bank-file-ingestion`, `admin-report-ingestion`,
      `transaction-normalization`, `matching-engine`, `reconciliation-review`,
      `audit-and-export`, `deployment-compose`, `security-baseline`.
  - `tasks.md` – Implementation checklist (used by `/opsx:apply`).

**Workflow:**

1. Propose and refine specs under `openspec/changes/...`.
2. Run `/opsx:apply` to start implementation guided by `tasks.md`.
3. Implement backend/frontend/infra according to specs.

---

## Running the Project (planned)

> Note: Implementation is not yet complete; these steps describe the intended flow once the core services are in place.

1. **Clone the repo** and move into the project:
   - `git clone <repo-url>`
   - `cd OW_BC`

2. **Create a `.env` file** based on `.env.example` (to be added during implementation), including:
   - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
   - `DB_HOST`, `DB_PORT`
   - `AUTH_SECRET_KEY`
   - `CORS_ORIGIN`
   - Upload size limits and other settings.

3. **Run with Docker Compose**:
   - `docker compose up --build`
   - This should start:
     - PostgreSQL
     - Backend FastAPI
     - Frontend React app

4. **Access the app**:
   - Frontend: `http://localhost:3000` (or configured port)
   - Backend API docs (FastAPI): `http://localhost:8000/docs`

---

## Data Samples

Realistic sample data is under `data/example/`:

- Bank CSVs (`julio provincial dl.CSV`).
- Bank XLS (`Movimientos Banesco.xls`).
- Bank PDFs (`Banesco_cte...pdf`).
- Fuerza Movil administrative reports (`pagos FuerzaMovil.xlsx`, `FuerzaMovil 2025 Don Lucho.xlsx`).

These samples are used to drive parsing, normalization, and matching logic (especially `Referencia` substring matching between Fuerza Movil and bank records).

---

## Development Notes

- **Backend**
  - FastAPI + SQLAlchemy/SQLModel + Alembic (migrations).
  - Unit tests for:
    - Normalization (ES numbers, dates, descriptions, `Referencia`).
    - Matching engine scoring and `Referencia` substring rule.
    - Multi-tenancy enforcement (no cross-tenant leakage).

- **Frontend**
  - React + TypeScript + Vite.
  - Emphasis on:
    - Clear upload flows and statuses.
    - Transparent reconciliation UI (scores, explanations).

- **Security**
  - Authenticated access for all tenant data.
  - Server-side sessions stored in DB, exposed via HttpOnly, Secure cookie.
  - Strict CORS, security headers, rate limiting, and upload validation.

