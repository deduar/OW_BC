# OW_BC – Bank Reconciliation Assistant

A **multi-user bank reconciliation assistant** that:

- Imports **bank statements** (PDF/CSV/XLS/XLSX) from multiple banks
- Imports **administrative reports** (e.g., Fuerza Movil Excel files)
- Normalizes and matches transactions automatically using:
  - `Referencia` substring matching (most important)
  - Amount matching
  - Date proximity (within tolerance)
  - Description similarity
- Provides a **review UI** for manual reconciliation
- Exports **audit reports** (CSV)
- Runs as a **two-tier web app** (frontend + backend) with **PostgreSQL**, deployed with **Docker Compose**

---

## Quick Start

```bash
./setup.sh
```

This script will:
1. Create a `.env` file from `.env.example` (if it doesn't exist)
2. Start the database, backend, and frontend services
3. Run the initial database migrations

Access:
- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs

---

## Architecture

### Frontend
- React + TypeScript + Vite
- User registration/login/logout
- File uploads for bank statements and admin reports
- Reconciliation workspace (Matched / Suggested / Unmatched tabs)
- Manual confirm/reject for suggestions
- CSV export

### Backend
- Python FastAPI (REST API)
- Multi-tenancy (one tenant per user in MVP)
- File parsing: CSV, XLS, XLSX, PDF, HTML (Banesco format)
- Matching engine with configurable weights
- Audit logging

### Database
- PostgreSQL
- Stores: users, tenants, sessions, uploads, transactions, matches, audit logs

### Deployment
- Docker Compose orchestrates: frontend, backend, db
- Environment variables for configuration

---

## Features

### Smart Duplicate Detection
- Files are identified by content hash (SHA256)
- Uploading the same file twice returns "already_processed" instead of re-parsing
- Reconciliation runs reuse previous matches when the same files are selected

### Matching Engine
The matching algorithm prioritizes:
1. **`Referencia` substring match** (highest weight) - finds admin reference within bank reference field
2. Amount exact match
3. Date proximity
4. Description similarity

### Reconciliation Workflow
1. Upload bank statement(s) and admin report
2. Select files and click "Start Matching"
3. Review matches:
   - **Matched** (auto-confirmed, score >= threshold)
   - **Suggested** (needs manual confirm/reject)
   - **Unmatched** (no candidates found)
4. Confirm or reject suggestions
5. Export results to CSV

---

## Sample Data

Located in `data/example/01/`:

| File | Type | Description |
|------|------|-------------|
| `Movimientos Banesco.xls` | Bank | HTML-formatted bank statement |
| `pagos FuerzaMovil.xlsx` | Admin | Payment report from Fuerza Movil |

---

## Development

### Backend
```bash
docker compose build backend
docker compose up -d backend
```

View logs:
```bash
docker logs ow_bc-backend-1 -f
```

### Frontend
```bash
cd frontend && npm run dev
```

### Database Access
```bash
docker exec -i ow_bc-db-1 psql -U owbc -d owbc
```

### Common Commands

Run migrations:
```bash
docker exec ow_bc-backend-1 alembic upgrade head
```

Create migration:
```bash
docker exec ow_bc-backend-1 alembic revision --autogenerate -m "description"
```

Reset database (development only):
```bash
docker exec -i ow_bc-db-1 psql -U owbc -d owbc -c "
DELETE FROM match;
DELETE FROM banktransaction;
DELETE FROM adminentry;
DELETE FROM fileupload;
DELETE FROM reconciliationrun;
"
```

---

## Security Notes

- PostgreSQL is not exposed externally (internal network only)
- Server-side sessions with HttpOnly cookies
- Strict CORS configuration
- File upload validation and size limits
- Tenant isolation enforced at API level

---

## Project Structure

```
OW_BC/
├── backend/
│   ├── app/
│   │   ├── parsers/       # File parsing (CSV, XLS, XLSX, PDF, HTML)
│   │   ├── routers/       # API endpoints
│   │   ├── matching/      # Matching engine
│   │   ├── schemas/       # Pydantic models
│   │   ├── models.py      # SQLModel models
│   │   └── utils/         # Normalization utilities
│   ├── migrations/        # Alembic migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── Workspace.tsx # Main reconciliation UI
│   │   ├── RunDetails.tsx # Match review UI
│   │   └── ...
│   └── nginx.conf
├── data/
│   └── example/          # Sample files
├── docker-compose.yml
└── README.md
```
