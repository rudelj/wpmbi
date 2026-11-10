# ETSI Work Programme Management Unified Suite - End-User Operating Manual & Wiki

> **Official Institutional Operational Manual & Engineering Reference** designed for the ETSI Directorate General, Secretariat General, Technical Officers, Rapporteurs, Delegates, and IT Engineering Teams.

---

## Quick Navigation

1. [Introduction & Operational Purpose](#1-introduction--operational-purpose)
2. [Access & Workstation Environment](#2-access--workstation-environment)
3. [Catalog & Advanced Multi-Criteria Search](#3-catalog--advanced-multi-criteria-search)
4. [The 360° Detailed Deliverable Profile](#4-the-360-detailed-deliverable-profile)
5. [Admin Console: Back-Office Lifecycle Management](#5-admin-console-back-office-lifecycle-management)
6. [Statutory Number Allocation Engine](#6-statutory-number-allocation-engine)
7. [Revisions & Derivation Engine: The 4 Derivation Modes](#7-revisions--derivation-engine-the-4-derivation-modes)
8. [Statutory Schedule & Waterfall Milestones](#8-statutory-schedule--waterfall-milestones)
9. [Radio Frequency Spectrum & EU Mandates](#9-radio-frequency-spectrum--eu-mandates)
10. [Dual-Source Synchronization: portal.etsi.org & DSDB](#10-dual-source-synchronization-portaletsiorg--dsdb)
11. [Certified Institutional KPIs](#11-certified-institutional-kpis)
12. [Institutional ETSI Glossary & Standards Taxonomy](#12-institutional-etsi-glossary--standards-taxonomy)
13. [Technical Architecture, Docker & Engineering FAQ](#13-technical-architecture-docker--engineering-faq)

---

## 1. Introduction & Operational Purpose

The **ETSI Work Programme Management (WPM) Unified Suite** brings together two core institutional systems of the European Telecommunications Standards Institute:
- **Legacy WPM.exe Desktop Suite**: The mission-critical Visual Basic 6 desktop back-office application operated by the ETSI Secretariat General for work item numbering, allocation, parent-child revision tracking, and schedule administration.
- **WPM Web Consultation Portal**: The public and delegate search engine hosted on `portal.etsi.org` for discovering standards, checking procedural milestones, and downloading ratified deliverables.

This unified platform consolidates both into a single modern, resilient web application running natively with Docker, Docker Compose, and a local high-performance SQLite database caching over 70,000 potential ETSI standards.

---

## 2. Access & Workstation Environment

- **Primary Application URL**: [http://localhost:8081](http://localhost:8081)
- **Interactive Documentation Wiki**: [http://localhost:8081/wiki/](http://localhost:8081/wiki/)
- **Default Port**: `8081`
- **Network Modes**:
  - *Offline / Autonomous*: Instant response from local database cache with zero external dependencies.
  - *Intranet / VPN Mode*: Automatic access to master SQL Server database `DSDB` at `172.27.2.40:1433` (`etsibase.etsihq.org`) when on-site in Sophia Antipolis or connected via GlobalProtect VPN.
  - *Public Portal Sync*: Real-time web scraping against `portal.etsi.org` for external live synchronization.

---

## 3. Catalog & Advanced Multi-Criteria Search

From the **Catalog & Search** tab:
- **Instant Search**: Filter across titles, document numbers (e.g. `303645`), Work Item IDs (e.g. `DEN/CYBER-0072`), and scopes.
- **Deliverable Type Filter**: Instant filtering by standard classification:
  - `EN`: European Standard
  - `TS`: Technical Specification
  - `TR`: Technical Report
  - `ES`: ETSI Standard
  - `EG`: ETSI Guide
  - `SR`: Special Report
  - `GS`: Group Specification
- **Technical Body Filter**: Dynamic filtering across all 176 active ETSI Technical Bodies (e.g. `CYBER`, `ERM`, `3GPP`, `DATA`, `EMTEL`, `MEC`, `ATTM`, `DECT`).
- **Milestone Filter**: Filter by lifecycle stage (`Drafting`, `Public Enquiry`, `National Vote`, `Published`, `Stopped`).
- **Closed Deliverables Toggle**: Surface superseded and retired standards on demand.
- **Favorites System**: 1-click star toggle bookmarking deliverables into local storage.
- **Direct Downloads**: 1-click downloads for official publication PDFs and editable Word `.zip` archives.

---

## 4. The 360° Detailed Deliverable Profile

Clicking **Detail** on any deliverable opens an operational drawer presenting complete standardization records:
1. **Core Metadata & Parentage**: Type, edition, standstill obligation, harmonised standard flag, and clickable predecessor parent links.
2. **Project Officers**: Full contact details for assigned Rapporteur and Secretariat Support Officer.
3. **Official Title & Scope**: Comprehensive technical justification and scope remarks.
4. **Waterfall Milestone Stepper**: Step-by-step progress tracking with target deadlines and achieved dates.
5. **Radio Spectrum Allocation**: Operating frequency bands under RED Directive 2014/53/EU.
6. **European Commission Mandates**: Formal EC Standardisation Requests (e.g. `M/585`).
7. **Remarks Ledger**: Permanent audit trail with direct form to log operational notes.

---

## 5. Admin Console: Back-Office Lifecycle Management

The **Admin Console** tab empowers Secretariat officers to manage deliverables with full administrative control:
- **Create New Work Item**: Comprehensive creation modal with validation of numbering series, technical bodies, standstill flags, and project officers.
- **Inline Status Modification**: Fast transition of deliverable lifecycle states (`Drafting`, `Public Enquiry`, `National Vote`, `Published`, `Stopped`).
- **Quick Clone Integration**: Instant transfer of any deliverable into the revision engine.

---

## 6. Statutory Number Allocation Engine

The **Number Allocation** tab modernizes the legacy `frmNextETSINumber` dialog, strictly enforcing ETSI Directives:
- **Standard Deliverables Rule**: Deliverable types `EN`, `TS`, `TR`, `ES`, `EG`, and `SR` require document numbers strictly greater than or equal to 1000 (e.g. `303645`, `103645`).
- **ISG and Legacy ETS Rule**: Industry Specification Group deliverables (`GS`) and legacy standards (`ETS`) require numbers strictly under 1000 (e.g. `024`), scoped to the Technical Body.
- **Automated Free Number Discovery**: Computes the highest allocated document number and proposes free sequential candidate numbers as clickable pills.

---

## 7. Revisions & Derivation Engine: The 4 Derivation Modes

From the **Revisions & Derivation** tab, officers can derive new deliverables using four institutional modes:

1. **Statutory Revision**:
   - Increments minor semantic version (e.g. `v1.1.1` becomes `v1.2.1`).
   - Switches identifier prefix from drafting `D` to revision `R` (e.g. `DEN/CYBER-0072` $\rightarrow$ `REN/CYBER-0072`).
   - **Automatic Parent Retirement Rule**: Predecessor deliverable is automatically retired:
     - `stop_flg` set to `1`.
     - `status` updated to `Stopped - Revised`.
     - Audit note logged: `Automatically stopped due to Revision creation -> REN/...`.
2. **Multi-Part Split**: Creates an independent deliverable part with `-SPLIT` suffix without stopping the parent.
3. **Committee Transfer**: Reassigns deliverable ownership to a new Technical Body.
4. **Standard Duplicate**: Generates an unlinked standalone copy for parallel development.

---

## 8. Statutory Schedule & Waterfall Milestones

The **Statutory Schedule** tab simulates milestone waterfalls based on official ETSI templates:
- **European Standard (EN) Template**:
  - `TB_ADOPT`: Technical Body Adoption of Draft (60 days)
  - `HANDOVER`: Handover to Secretariat (15 days)
  - `PE_START`: Public Enquiry Start (90 days)
  - `PE_CLOSE`: Public Enquiry Close & Comment Resolution (45 days)
  - `VOTE_START`: National Member Vote Start (60 days)
  - `PUBLISH`: Official Publication (15 days)
  - *Total Standard Duration*: 285 calendar days.
- **Technical Specification (TS) Template**:
  - `TB_ADOPT`: Technical Body Adoption of Draft (45 days)
  - `HANDOVER`: Handover to Technical Editor (15 days)
  - `MEMB_APPR`: Technical Body Member Approval (30 days)
  - `PUBLISH`: Publication as Technical Specification (10 days)
  - *Total Standard Duration*: 100 calendar days.

---

## 9. Radio Frequency Spectrum & EU Mandates

The **Spectrum & EU Mandates** tab tracks regulatory compliance:
- **Radio Spectrum Bands**: Spectrum allocations defining low and high frequencies (e.g. 9 kHz – 3000 MHz) and radio service applications under the Radio Equipment Directive 2014/53/EU.
- **Standardisation Requests**: Legal mandates issued by the European Commission under Regulation (EU) 1025/2012 cited in the Official Journal of the European Union (OJEU).

---

## 10. Dual-Source Synchronization: portal.etsi.org & DSDB

The system combines two data sources:
- **Live Portal Web Scraper**: Asynchronous HTTP client targeting `portal.etsi.org/webapp/WorkProgram/Frame_WorkItemList.asp` with regular expression parsing and automated HTML link resolution.
- **ODBC Driver 17 for SQL Server**: Direct connectivity to master database `DSDB` at `172.27.2.40:1433`.
- **Automated Text Sanitation**: Strips parenthetical expressions across all imported records, maintaining clean naming standards.

---

## 11. Certified Institutional KPIs

The dashboard header ribbon provides real-time governance metrics:
- **Active Work Items**: 1 188+ deliverables actively drafted or published.
- **Technical Bodies**: 86+ active committees with deliverables (176 total available).
- **Published Standards**: 807+ officially ratified deliverables.
- **Under Enquiry / Vote**: Standards currently undergoing public scrutiny.
- **Closed / Revised**: 21+ retired and superseded predecessor standards.

---

## 12. Institutional ETSI Glossary & Standards Taxonomy

| Term | Operational Definition |
| :--- | :--- |
| **EN** | European Standard - Carries standstill obligations and member voting. |
| **TS** | Technical Specification - Fast-track industry specification adopted by TBs. |
| **TR** | Technical Report - Informative background and context document. |
| **ES** | ETSI Standard - Approved by the full membership through formal vote. |
| **EG** | ETSI Guide - Guidance on procedural or technical recommendations. |
| **SR** | Special Report - Public report commissioned for special projects. |
| **GS** | Group Specification - Technical standard from an Industry Specification Group. |
| **ETS** | European Telecom Standard - Historical legacy standard predecessor to the EN. |
| **RED** | Radio Equipment Directive 2014/53/EU. |
| **NSO** | National Standards Organization (AFNOR, DIN, BSI, etc.). |
| **Rapporteur** | Designated lead technical drafting officer for a standard. |
| **Technical Officer** | Secretariat staff member overseeing procedural compliance. |

---

## 13. Technical Architecture, Docker & Engineering FAQ

### Technology Stack
- **Backend**: Python 3.11+ / FastAPI / Uvicorn.
- **Database**: SQLite 3 with foreign keys, WAL mode, and conflict resolution.
- **Frontend**: Vanilla ES6 JavaScript, HTML5, Lucide Icons, KaTeX math.
- **Documentation Engine**: MkDocs Material 9.x.

### Docker Deployment
```bash
# Build and start containerized stack on port 8081
docker compose up -d --build

# Verify container health
docker ps

# Check logs
docker compose logs -f
```

### Key API Endpoints
- `GET /api/work-items`: Filtered deliverable search with pagination.
- `GET /api/work-items/{wki_id}`: 360-degree detailed deliverable record.
- `POST /api/work-items`: Create new standardization deliverable.
- `POST /api/work-items/{wki_id}/clone`: Derivation engine (revision, split, transfer, duplicate).
- `GET /api/numbering/next`: Next available document number generator.
- `POST /api/schedule/perfect-plan`: Waterfall milestone simulator.
- `GET /api/technical-bodies`: Complete list of 176 Technical Bodies.
- `POST /api/sync/portal`: Live synchronization with `portal.etsi.org`.
- `GET /api/export`: CSV / JSON data export.
