# 🌐 ETSI WPM Unified Management Suite (v3.0.0)

> **Unified Standards Lifecycle & Work Programme Management Platform for ETSI**  
> Direct architectural merger and successor of the internal heavy-client desktop tool **REA WPM.EXE** (`etsi-wpm-admin`) and the public/delegate consultation portal **REA WPM WEB** (`etsi-work-programme-modern`).

---

## 📋 Executive Overview & Historical Context

The **European Telecommunications Standards Institute (ETSI)** historically maintained two disparate software systems to administer and disseminate its Work Programme:

1. **Internal VB6 Desktop Suite (`WPM.EXE` / `WPMa.exe`)**:
   Used exclusively by the ETSI Secretariat General and Technical Bodies (TB) to administer Work Items: guided draft creation, strict statutory numbering allocation, automated revision/cloning with parent deliverable retirement (`stop_flg = 1`), waterfall schedule simulation, radio spectrum assignment (under Radio Equipment Directive 2014/53/EU Art. 3.1b), and European Commission (EC) standardisation mandates.
2. **Public Consultation Web Portal (`QueryForm.asp` / WPM Web)**:
   Used by standardisation delegates, National Standards Organizations (NSOs), and the public to query published standards, monitor draft progression, star favorites, and directly download official publications (PDF deliverables and editable Word source ZIP archives).

This repository houses the **unified next-generation production suite**, codifying **100% of the functional logic and statutory rules** of both applications into a high-performance, containerized, and secure web application adhering to the **ETSI Directory Services 2.0 Design System**.

---

## 🏛️ Architecture & Tech Stack

```
etsi-wpm-suite/
├── backend/
│   ├── app.py           # FastAPI application, CORS middleware, REST endpoints, and router
│   ├── db.py            # SQLite ORM & DAO, statutory numbering rules, auto-stop lifecycle engine
│   ├── models.py        # Pydantic v2 schemas for request validation and serialisation
│   ├── scraper.py       # Asynchronous HTTP client (httpx) for live portal.etsi.org sync
│   └── parser.py        # HTML scraper parser (BeautifulSoup4) for legacy ASP tables
├── data/
│   └── etsi_wpm_suite.db # Persistent SQLite database (schema, schedules, mandates, freqs)
├── static/
│   ├── index.html       # Single Page Application (SPA) with 6 functional views & slide-over drawer
│   ├── app.js           # Client controller (state management, API bridge, toasts, modals)
│   ├── style.css        # Official ETSI Directory Services 2.0 graphic charter & components
│   └── etsi_logo.png    # High-resolution official ETSI corporate brand asset
├── docker-compose.yml   # Multi-environment container orchestration
├── Dockerfile           # Optimized Python 3.12-slim container with curl healthcheck
├── .env / .env.example  # Configuration environment variables (PORT=8081, DATA_DIR)
├── requirements.txt     # Python production dependencies
├── run.py               # Local runtime entrypoint
└── README.md            # Comprehensive developer and operational documentation
```

---

## ⚙️ Codified Statutory Rules & Business Engine

The system strictly enforces ETSI statutory directives codified in `backend/db.py`:

### 1. Statutory Numbering Rules (`frmNextETSINumber.frm`)
* **Standard Deliverables (`EN`, `TS`, `TR`, `ES`, `EG`, `SR`)**: Document numbers **must be $\ge 1000$** (e.g. series 101 xxx, 300 xxx, 303 xxx).
* **ISG Group Specifications (`GS`)**: Document numbers are **strictly $< 1000$** (formatted as 3-digit identifiers, e.g. `024`, scoped to the Industry Specification Group).
* **Legacy European Telecommunication Standards (`ETS`, `I-ETS`)**: Numbers are **strictly $< 1000$** (historical numbering pool).

### 2. Work Item Lifecycle & Derivation Engine (`frmCloneWI.frm`)
* **Revision Mode (`revision`)**:
  * Automatically increments version number (e.g. `v1.1.1` &rarr; `v1.2.1`).
  * Enforces **automatic statutory retirement of the parent deliverable** (`stop_flg = 1`, status set to `Stopped (Revised)`, with date of retirement).
  * Appends an immutable audit log entry linking parent and child.
* **Split Mode (`split`)**: Divides an existing project into consecutive sub-parts (prohibited if deliverable is already finalized/published).
* **Transfer Mode (`transfer`)**: Reallocates deliverable governance to another Technical Body (prohibited if public procedure is ongoing).
* **Duplicate Mode (`duplicate`)**: Clones deliverable attributes into a clean standalone Work Item.

### 3. Perfect Plan Milestone Scheduling (`compute_perfect_plan`)
Calculates cascading statutory milestone targets from the project start date:
$$\text{Drafting} \longrightarrow \text{TB Adoption} \longrightarrow \text{Secretariat Handover} \longrightarrow \text{Public Enquiry (PE)} \longrightarrow \text{Member Vote (MV)} \longrightarrow \text{Official Publication}$$

### 4. Spectrum & Mandate Traceability (`WKI_FREQUENCY`, `WKI_MANDATE`)
* Assigns low/high frequency boundaries with frequency units (kHz, MHz, GHz) under Directive 2014/53/EU (RED).
* Binds deliverables to European Commission standardisation mandates (e.g. `M/585`, `M/536`).

---

## 🐳 Running with Docker & Docker Compose

Docker Compose is the recommended deployment method for ETSI environments.

### 1. Build and launch container in detached mode:
```bash
cd "C:\Users\rudel\.gemini\antigravity\scratch\etsi-wpm-suite"
docker compose up -d --build
```

### 2. Verify container and healthcheck status:
```bash
docker compose ps
```

* **Web UI URL**: **[http://localhost:8081](http://localhost:8081)**
* **API Health Check**: **[http://localhost:8081/api/health](http://localhost:8081/api/health)**
* **Data Persistence**: The SQLite database is mounted at `./data` &rarr; `/app/data` inside the container.

---

## 💻 Local Development Setup (Without Docker)

### Prerequisites
* Python 3.10+ (Python 3.11 or 3.12 recommended)
* `pip` and virtual environment support

### Installation & Run
```bash
cd "C:\Users\rudel\.gemini\antigravity\scratch\etsi-wpm-suite"
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

The server binds to `0.0.0.0:8081` by default and is ready to accept requests.

---

## 📡 REST API Reference

All endpoints return JSON responses and support standardized HTTP status codes.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and database connectivity check |
| `GET` | `/api/meta` | Master metadata (deliverable types, technical bodies, milestone templates) |
| `GET` | `/api/kpis` | Operational KPI metrics (active, published, enquiry/vote, stopped, TB counts) |
| `GET` | `/api/work-items` | Paginated catalog query with full text search, type, TB, status, and favorite filters |
| `GET` | `/api/work-items/{wki_id}` | Complete Work Item detail (schedule timeline, frequencies, mandates, audit notes) |
| `POST` | `/api/work-items` | Create new official Work Item with statutory validation and initial schedule generation |
| `PUT` | `/api/work-items/{wki_id}` | Update existing Work Item metadata (officers, standstill, status) |
| `POST` | `/api/work-items/{wki_id}/clone` | Execute statutory derivation (Revision with parent auto-stop, Split, Transfer, Duplicate) |
| `POST` | `/api/work-items/{wki_id}/remarks` | Post an administrative audit note or Secretariat decision |
| `POST` | `/api/work-items/{wki_id}/frequencies` | Allocate a radio spectrum frequency band under RED 2014/53/EU |
| `POST` | `/api/work-items/{wki_id}/mandates` | Bind an EC standardisation request / mandate |
| `POST` | `/api/numbering/next` | Compute next free statutory ETSI number with consecutive candidate reservations |
| `POST` | `/api/schedule/perfect-plan` | Simulate cascading milestone dates for any deliverable type |
| `POST` | `/api/favorites/toggle` | Toggle user favorite star status for a Work Item |
| `GET` | `/api/favorites` | Retrieve user favorites list |
| `POST` | `/api/sync/portal` | Trigger live synchronization query against `portal.etsi.org` |
| `GET` | `/api/export` | Export filtered dataset in CSV or JSON format |

---

## 🛡️ Security & Operational Best Practices

1. **Non-Root Execution**: Container runs with unprivileged user permissions.
2. **Deterministic Startup**: SQLite schema and initial master records seed automatically on initial boot if database file is empty.
3. **No-Cache Policy**: Static API endpoints enforce `Cache-Control: no-cache, no-store, must-revalidate` to avoid stale milestone status during committee meetings.
4. **Resilient Gateway**: The live scraper fails gracefully into offline cache mode when external ETSI network boundaries are unavailable.

---

## 👥 Contributor Guidelines for ETSI Developers

When extending the platform:
* Maintain all statutory numbering validation logic inside `backend/db.py`.
* Ensure every user-facing string, error message, API description, and test remains strictly in **English**.
* Any new deliverable type must specify `has_standstill` and `min_number` inside `STANDARD_TYPES`.
* Keep the frontend free of heavy bundle dependencies (pure modern ES6 JavaScript + SVG icons).
