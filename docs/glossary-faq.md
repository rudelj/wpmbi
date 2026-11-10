# ETSI Standards Glossary & FAQ

This glossary details standard acronyms, milestone codes, statutory terminology, and common questions.

---

## Deliverable Types Glossary

| Acronym | Full Statutory Name | Statutory Characteristics |
| :--- | :--- | :--- |
| **EN** | European Standard | Carries national standstill obligations and mandatory member voting. |
| **TS** | Technical Specification | Adopted directly by Technical Bodies for fast industry deployment. |
| **TR** | Technical Report | Informative deliverable containing technical context and background. |
| **ES** | ETSI Standard | Approved by the full membership of ETSI through formal member voting. |
| **EG** | ETSI Guide | Guidance document outlining procedural or technical recommendations. |
| **SR** | Special Report | Public report commissioned for special projects or sector studies. |
| **GS** | Group Specification | Technical deliverable published by an Industry Specification Group. |
| **ETS** | European Telecom Standard | Historical legacy standard predecessor to the modern EN. |

---

## Statutory Waterfall Milestones

| Code | Stage Name | Standard Duration |
| :--- | :--- | :--- |
| **TB_ADOPT** | Technical Body Adoption of Draft | 45 - 60 calendar days |
| **HANDOVER** | Handover to Secretariat | 15 calendar days |
| **PE_START** | Public Enquiry Start | 90 calendar days |
| **PE_CLOSE** | Public Enquiry Close & Comment Resolution | 45 calendar days |
| **MEMB_APPR**| Technical Body Member Approval | 30 calendar days |
| **VOTE_START**| National Vote / Member Vote Start | 60 calendar days |
| **PUBLISH** | Official Publication of Standard | 10 - 15 calendar days |

---

## Institutional Acronyms

| Acronym | Definition |
| :--- | :--- |
| **WPM** | Work Programme Management |
| **DSDB** | Directory Services Database - Master SQL Server database of ETSI |
| **TB** | Technical Body - General term covering TCs, ISGs, and Working Groups |
| **TC** | Technical Committee (e.g. TC CYBER, TC ERM) |
| **ISG** | Industry Specification Group (e.g. ISG ENI, ISG NFV) |
| **3GPP** | 3rd Generation Partnership Project |
| **NSO** | National Standards Organization (e.g. AFNOR, DIN, BSI) |
| **RED** | Radio Equipment Directive 2014/53/EU |
| **OJEU** | Official Journal of the European Union |
| **SRD** | Short Range Devices |
| **EMC** | ElectroMagnetic Compatibility |

---

## Frequently Asked Questions

### Why must standard numbers be greater than or equal to 1000?
ETSI Directives reserve numbers under 1000 for Industry Specification Groups (GS) and historical legacy European Telecommunications Standards (ETS). Standard deliverables (`EN`, `TS`, `TR`, `ES`, `EG`, `SR`) must be numbered 1000 or higher to prevent collisions across the official series (e.g. 101 xxx, 300 xxx, 303 xxx).

### What happens to a predecessor standard when a revision is approved?
When an administrative revision is created, the system automatically sets the predecessor parent's `stop_flg` to `1` and marks its status as `Stopped - Revised`. This guarantees that historical standards are safely retired from the active work programme while remaining searchable in the archive.

### How do I consult retired or superseded standards?
In the **Catalog & Search** tab, check the box labeled **Include Closed Deliverables**. This will display all historical, stopped, and superseded deliverables alongside active ones.

### How often is data synchronized from portal.etsi.org?
The application maintains a high-speed local cache. Clicking **Sync Portal** in the top header triggers an immediate live query to fetch the latest published and in-progress deliverables directly from `portal.etsi.org`.
