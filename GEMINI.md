# GEMINI.md - OW_BC Project Context

This file serves as the primary instructional context for Gemini CLI interactions within the `OW_BC` repository. It outlines the project's purpose, architecture, development workflows, and key conventions.

---

## 🚀 Project Overview

**OW_BC (Bank Reconciliation Assistant)** is a multi-user tool designed to automate the reconciliation of bank statements (PDF, CSV, XLS, XLSX) with administrative reports (e.g., Fuerza Movil Excel files).

### 🛠 Tech Stack
- **Backend:** Python 3.12 + FastAPI (REST API).
- **Frontend:** React + TypeScript + Vite (Current implementation is an Nginx placeholder).
- **Database:** PostgreSQL 16.
- **Infrastructure:** Docker Compose (multi-stage builds).
- **Workflow:** Spec-driven development using **OpenSpec**.

### 🏗 Architecture
- **Two-Tier Web App:** Separate backend and frontend containers communicating via an internal Docker network.
- **Multi-Tenancy:** Strict data isolation using a `tenant_id` (1:1 with user for the MVP).
- **Matching Engine:** Rule-based scoring (amount, date ±2 days, description similarity, and `Referencia` substring logic).

---

## 🛠 Building and Running

### Prerequisites
- Docker and Docker Compose.
- Python 3.12 (for local backend development).

### Key Commands
- **Initial Setup:**
  ```bash
  cp .env.example .env
  ```
- **Start All Services:**
  ```bash
  docker compose up --build -d
  ```
- **Run Development Commands (inside container):**
  ```bash
  docker compose exec backend <command>
  # Example for Alembic:
  docker compose exec backend alembic init migrations
  ```
- **Run Database Migrations (Planned):**
  ```bash
  docker compose --profile migrate run --rm migrate
  ```
- **Access Points:**
  - **Frontend:** `http://localhost:3000`
  - **Backend API Docs:** `http://localhost:8000/docs`
  - **Health Check:** `http://localhost:8000/healthz`

---

## 📜 Development Conventions

### 1. Spec-Driven Workflow (OpenSpec)
The project follows a rigorous spec-driven process. All changes must be documented in `openspec/changes/`.
- `proposal.md`: Problem statement and goals.
- `design.md`: Technical architecture and decisions.
- `tasks.md`: Implementation checklist.
- `/opsx:apply`: (Planned tool) to guide implementation from `tasks.md`.

### 2. Multi-Tenancy & Security
- **Data Isolation:** Every database entity must be scoped by `tenant_id`. No cross-tenant data leakage is allowed.
- **Authentication:** Session/JWT managed via `HttpOnly` cookies.
- **Validation:** Strict server-side validation for file uploads (size, type) and API inputs.

### 3. Data Parsing Standards
- **Locale:** ES (Spanish) locale for amounts (e.g., `1.234,56` where `.` is thousands and `,` is decimals).
- **Dates:** Primarily `DD/MM/YYYY` or `DD-MM-YYYY`.
- **References:** `Referencia` token normalization (digits-only) for substring matching.

### 4. Repository Structure
- `backend/`: FastAPI application code.
- `frontend/`: React application (placeholder setup).
- `data/example/`: Realistic sample data for testing parsers and matching logic.
- `openspec/`: Design documents and capability specifications.
- `docs/`: Supplemental project documentation.

---

## 📍 Current Status
The project is in the **setup/foundation phase**.
- [x] Repository structure and Docker Compose.
- [x] Basic FastAPI backend with health check.
- [x] Frontend placeholder (Nginx).
- [ ] Database schema and multi-tenancy foundation (Next steps).
- [ ] Authentication implementation.
- [ ] File ingestion and matching logic.

*Note: Refer to `openspec/changes/bank-reconciliation-multi-tenant/tasks.md` for the current progress and pending tasks.*
