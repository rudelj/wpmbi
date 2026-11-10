import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from .models import (
    WorkItemSummary,
    WorkItemDetail,
    WorkItemCreate,
    WorkItemUpdate,
    MilestoneStep,
    CloneWorkItemRequest,
    NextNumberRequest,
    NextNumberResponse,
    RemarkCreate,
    FrequencyCreate,
    MandateCreate,
    KPIStats
)

logger = logging.getLogger("etsi_wpm_suite.db")

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR = Path(os.environ.get("DATA_DIR", str(DEFAULT_DATA_DIR)))
SQLITE_DB_PATH = DATA_DIR / "etsi_wpm_suite.db"

STANDARD_TYPES = [
    {"code": "EN", "name": "European Standard", "has_standstill": True, "min_number": 1000},
    {"code": "ES", "name": "ETSI Standard", "has_standstill": False, "min_number": 1000},
    {"code": "EG", "name": "ETSI Guide", "has_standstill": False, "min_number": 1000},
    {"code": "TS", "name": "Technical Specification", "has_standstill": False, "min_number": 1000},
    {"code": "TR", "name": "Technical Report", "has_standstill": False, "min_number": 1000},
    {"code": "SR", "name": "Special Report", "has_standstill": False, "min_number": 1000},
    {"code": "GS", "name": "Group Specification ISG", "has_standstill": False, "min_number": 1, "max_number": 999},
    {"code": "ETS", "name": "European Telecommunication Standard Legacy", "has_standstill": True, "min_number": 1, "max_number": 999}
]

TECHNICAL_BODIES = [
    {"code": "CYBER", "name": "Cyber Security", "lead": "ETSI"},
    {"code": "ERM", "name": "EMC and Radio Spectrum Matters", "lead": "ETSI"},
    {"code": "3GPP", "name": "3rd Generation Partnership Project", "lead": "3GPP"},
    {"code": "BROADCAST", "name": "Joint Technical Committee Broadcast", "lead": "EBU/CENELEC/ETSI"},
    {"code": "DECT", "name": "Digital Enhanced Cordless Telecommunications", "lead": "ETSI"},
    {"code": "ISG ENI", "name": "Experiential Networked Intelligence", "lead": "ISG"},
    {"code": "ISG NFV", "name": "Network Functions Virtualisation", "lead": "ISG"},
    {"code": "MSG", "name": "Mobile Standards Group", "lead": "ETSI"},
    {"code": "SES", "name": "Satellite Earth Stations and Systems", "lead": "ETSI"},
    {"code": "eHEALTH", "name": "Electronic Health Working Group", "lead": "ETSI"}
]

MILESTONES_TEMPLATES = {
    "EN": [
        {"code": "TB_ADOPT", "name": "Technical Body Adoption of Draft", "days": 60},
        {"code": "HANDOVER", "name": "Handover to Secretariat", "days": 15},
        {"code": "PE_START", "name": "Public Enquiry EN Approval Procedure Start", "days": 90},
        {"code": "PE_CLOSE", "name": "Public Enquiry Close & Comment Resolution", "days": 45},
        {"code": "VOTE_START", "name": "National Vote / Member Vote Start", "days": 60},
        {"code": "PUBLISH", "name": "Official Publication of European Standard", "days": 15}
    ],
    "TS": [
        {"code": "TB_ADOPT", "name": "Technical Body Adoption of Draft", "days": 45},
        {"code": "HANDOVER", "name": "Handover to Technical Editor", "days": 15},
        {"code": "MEMB_APPR", "name": "Technical Body Member Approval", "days": 30},
        {"code": "PUBLISH", "name": "Publication as Technical Specification", "days": 10}
    ],
    "TR": [
        {"code": "TB_ADOPT", "name": "Technical Body Drafting Complete", "days": 30},
        {"code": "HANDOVER", "name": "Handover to Secretariat", "days": 10},
        {"code": "PUBLISH", "name": "Publication as Technical Report", "days": 10}
    ],
    "ES": [
        {"code": "TB_ADOPT", "name": "Technical Body Adoption of Draft", "days": 60},
        {"code": "HANDOVER", "name": "Handover to Secretariat", "days": 15},
        {"code": "MEMB_VOTE", "name": "ETSI Membership Vote", "days": 60},
        {"code": "PUBLISH", "name": "Publication as ETSI Standard", "days": 15}
    ],
    "EG": [
        {"code": "TB_ADOPT", "name": "Technical Body Adoption of Draft", "days": 45},
        {"code": "HANDOVER", "name": "Handover to Secretariat", "days": 15},
        {"code": "MEMB_VOTE", "name": "ETSI Membership Vote", "days": 60},
        {"code": "PUBLISH", "name": "Publication as ETSI Guide", "days": 15}
    ],
    "GS": [
        {"code": "TB_ADOPT", "name": "ISG Group Adoption of Specification", "days": 30},
        {"code": "HANDOVER", "name": "Handover to Secretariat", "days": 10},
        {"code": "PUBLISH", "name": "Publication as Group Specification", "days": 10}
    ]
}

def get_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS work_items (
        wki_id TEXT PRIMARY KEY,
        doc_type TEXT NOT NULL,
        deliv_class TEXT DEFAULT 'Standard',
        doc_number TEXT NOT NULL,
        part_nb TEXT,
        subpart_nb TEXT,
        edition_nb TEXT DEFAULT '1',
        version TEXT DEFAULT 'v1.1.1',
        reference TEXT NOT NULL,
        technical_body TEXT NOT NULL,
        tb_id TEXT,
        title_part1 TEXT NOT NULL,
        title_part2 TEXT,
        title_part3 TEXT,
        full_title TEXT NOT NULL,
        status TEXT NOT NULL,
        state_code TEXT DEFAULT 'DRAFT',
        status_date TEXT,
        creation_date TEXT,
        stop_date TEXT,
        stop_flg INTEGER DEFAULT 0,
        standstill_status TEXT DEFAULT 'NO',
        standstill_date TEXT,
        rapporteur_name TEXT,
        rapporteur_email TEXT,
        support_officer_name TEXT,
        support_officer_email TEXT,
        harmonized_flg INTEGER DEFAULT 0,
        lead_body TEXT,
        scope TEXT,
        parent_wki_id TEXT,
        parent_reference TEXT,
        pdf_url TEXT,
        word_url TEXT,
        detail_url TEXT,
        is_finalized INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS work_item_schedules (
        sched_id INTEGER PRIMARY KEY AUTOINCREMENT,
        wki_id TEXT NOT NULL,
        mls_code TEXT NOT NULL,
        mls_name TEXT NOT NULL,
        sched_position INTEGER NOT NULL,
        duration_days INTEGER DEFAULT 30,
        original_date TEXT,
        review_date TEXT,
        target_date TEXT,
        achieved_date TEXT,
        status TEXT DEFAULT 'PENDING',
        FOREIGN KEY(wki_id) REFERENCES work_items(wki_id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS work_item_frequencies (
        freq_id INTEGER PRIMARY KEY AUTOINCREMENT,
        wki_id TEXT NOT NULL,
        low_freq REAL NOT NULL,
        high_freq REAL NOT NULL,
        unit TEXT NOT NULL DEFAULT 'MHz',
        service_app TEXT,
        FOREIGN KEY(wki_id) REFERENCES work_items(wki_id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS work_item_mandates (
        mandate_id INTEGER PRIMARY KEY AUTOINCREMENT,
        wki_id TEXT NOT NULL,
        mandate_code TEXT NOT NULL,
        directive_ref TEXT,
        descript TEXT,
        FOREIGN KEY(wki_id) REFERENCES work_items(wki_id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS work_item_remarks (
        remark_id INTEGER PRIMARY KEY AUTOINCREMENT,
        wki_id TEXT NOT NULL,
        remark_type TEXT DEFAULT 'GENERAL',
        remark_text TEXT NOT NULL,
        author TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(wki_id) REFERENCES work_items(wki_id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        wki_id TEXT PRIMARY KEY,
        doc_number TEXT,
        title TEXT,
        technical_body TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS technical_bodies_cache (
        tb_id TEXT PRIMARY KEY,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        lead TEXT DEFAULT 'ETSI'
    );
    """)

    conn.commit()

    cursor.execute("SELECT count(*) as count FROM work_items")
    if cursor.fetchone()["count"] == 0:
        seed_complete_data(conn)

    conn.close()
    logger.info("ETSI WPM Suite DB initialized at %s", SQLITE_DB_PATH)

def get_technical_bodies() -> List[Dict[str, Any]]:
    """Returns all active technical bodies from database cache."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT tb_id, code, name, lead FROM technical_bodies_cache ORDER BY code")
        rows = cursor.fetchall()
        conn.close()
        if rows:
            return [{"code": r["code"], "name": r["name"], "lead": r["lead"], "id": str(r["tb_id"])} for r in rows]
    except Exception as e:
        logger.warning(f"Error querying technical_bodies_cache: {e}")

    return [{"code": tb["code"], "name": tb["name"], "lead": tb["lead"], "id": tb["code"]} for tb in TECHNICAL_BODIES]

def seed_complete_data(conn: sqlite3.Connection):
    cursor = conn.cursor()

    items = [
        {
            "wki_id": "DEN/CYBER-0072",
            "doc_type": "EN",
            "doc_number": "303645",
            "version": "v2.1.1",
            "reference": "ETSI EN 303 645",
            "technical_body": "CYBER",
            "title_part1": "CYBER",
            "title_part2": "Cyber Security for Consumer Internet of Things",
            "title_part3": "Baseline Requirements",
            "full_title": "CYBER; Cyber Security for Consumer Internet of Things: Baseline Requirements",
            "status": "Published",
            "state_code": "PUBLISHED",
            "status_date": "2025-01-20",
            "creation_date": "2023-09-01",
            "standstill_status": "YES",
            "standstill_date": "2025-01-20",
            "rapporteur_name": "Dr. Alex Vance",
            "rapporteur_email": "a.vance@etsi.org",
            "support_officer_name": "Claire Martin - Secretariat",
            "support_officer_email": "claire.martin@etsi.org",
            "harmonized_flg": 1,
            "lead_body": "ETSI TC CYBER",
            "scope": "European Standard setting cybersecurity provisions for consumer IoT devices connected to IP networks under RED Directive.",
            "pdf_url": "https://www.etsi.org/deliver/etsi_en/303600_303699/303645/02.01.01_60/en_303645v020101p.pdf",
            "word_url": "https://portal.etsi.org/webapp/WorkProgram/LogonRedirection.asp?WKI_ID=60542&FileFormat=ZIP",
            "detail_url": "https://portal.etsi.org/webapp/WorkProgram/Report_WorkItem.asp?WKI_ID=60542",
            "is_finalized": 1,
            "stop_flg": 0
        },
        {
            "wki_id": "REN/ERM-TG28-560",
            "doc_type": "EN",
            "doc_number": "301489-1",
            "version": "v2.2.3",
            "reference": "ETSI EN 301 489-1",
            "technical_body": "ERM",
            "title_part1": "ERM",
            "title_part2": "ElectroMagnetic Compatibility EMC standard for radio equipment and services",
            "title_part3": "Common technical requirements",
            "full_title": "ElectroMagnetic Compatibility EMC standard for radio equipment and services; Part 1: Common technical requirements",
            "status": "Public Enquiry",
            "state_code": "ENQUIRY",
            "status_date": "2025-02-15",
            "creation_date": "2024-01-10",
            "standstill_status": "YES",
            "standstill_date": "2024-01-10",
            "rapporteur_name": "Jean Dupont",
            "rapporteur_email": "jean.dupont@etsi.org",
            "support_officer_name": "Marc Lemaire - Secretariat",
            "support_officer_email": "marc.lemaire@etsi.org",
            "harmonized_flg": 1,
            "lead_body": "ETSI TC ERM",
            "scope": "Harmonised standard covering essential requirements of article 3.1b of Directive 2014/53/EU.",
            "pdf_url": "https://www.etsi.org/deliver/etsi_en/301400_301499/30148901/02.02.03_20/en_30148901v020203a.pdf",
            "word_url": None,
            "detail_url": "https://portal.etsi.org/webapp/WorkProgram/Report_WorkItem.asp?WKI_ID=58912",
            "is_finalized": 0,
            "stop_flg": 0
        },
        {
            "wki_id": "DTR/CYBER-0050",
            "doc_type": "TR",
            "doc_number": "103645",
            "version": "v1.1.1",
            "reference": "ETSI TR 103 645",
            "technical_body": "CYBER",
            "title_part1": "CYBER",
            "title_part2": "Baseline Requirements for Consumer Internet of Things",
            "title_part3": "Technical Background & Rationale",
            "full_title": "CYBER; Baseline Requirements for Consumer Internet of Things; Technical Background and Context",
            "status": "Published",
            "state_code": "PUBLISHED",
            "status_date": "2023-04-12",
            "creation_date": "2022-10-01",
            "standstill_status": "NO",
            "standstill_date": None,
            "rapporteur_name": "Dr. Alex Vance",
            "rapporteur_email": "a.vance@etsi.org",
            "support_officer_name": "Claire Martin - Secretariat",
            "support_officer_email": "claire.martin@etsi.org",
            "harmonized_flg": 0,
            "lead_body": "ETSI TC CYBER",
            "scope": "Informative Technical Report providing context and implementation guidance for consumer IoT security.",
            "pdf_url": "https://www.etsi.org/deliver/etsi_tr/103600_103699/103645/01.01.01_60/tr_103645v010101p.pdf",
            "word_url": None,
            "detail_url": "https://portal.etsi.org/webapp/WorkProgram/Report_WorkItem.asp?WKI_ID=54321",
            "is_finalized": 1,
            "stop_flg": 0
        },
        {
            "wki_id": "DGS/ISG-ENI-024",
            "doc_type": "GS",
            "doc_number": "024",
            "version": "v1.1.1",
            "reference": "ETSI GS ENI 024",
            "technical_body": "ISG ENI",
            "title_part1": "ISG ENI",
            "title_part2": "Experiential Networked Intelligence ENI",
            "title_part3": "Cognitive SLA Management",
            "full_title": "Experiential Networked Intelligence ENI; Cognitive SLA Management Architecture",
            "status": "Drafting",
            "state_code": "DRAFT",
            "status_date": "2024-05-18",
            "creation_date": "2024-05-18",
            "standstill_status": "NO",
            "standstill_date": None,
            "rapporteur_name": "Elena Rostova",
            "rapporteur_email": "e.rostova@etsi.org",
            "support_officer_name": "Patrick Guibert - ISG Support",
            "support_officer_email": "patrick.guibert@etsi.org",
            "harmonized_flg": 0,
            "lead_body": "ETSI ISG ENI",
            "scope": "ISG Specification outlining AI-driven closed-loop Service Level Agreement orchestration.",
            "pdf_url": None,
            "word_url": None,
            "detail_url": "https://portal.etsi.org/webapp/WorkProgram/Report_WorkItem.asp?WKI_ID=63990",
            "is_finalized": 0,
            "stop_flg": 0
        },
        {
            "wki_id": "RTS/TSG-RAN-38101-1",
            "doc_type": "TS",
            "doc_number": "138101-1",
            "version": "v18.4.0",
            "reference": "ETSI TS 138 101-1",
            "technical_body": "3GPP",
            "title_part1": "5G NR",
            "title_part2": "User Equipment UE radio transmission and reception",
            "title_part3": "Part 1: Range 1 Standalone",
            "full_title": "5G; NR; User Equipment UE radio transmission and reception; Part 1: Range 1 Standalone - 3GPP TS 38.101-1 version 18.4.0 Release 18",
            "status": "Published",
            "state_code": "PUBLISHED",
            "status_date": "2025-01-15",
            "creation_date": "2023-01-10",
            "standstill_status": "NO",
            "standstill_date": None,
            "rapporteur_name": "Satoshi Tanaka",
            "rapporteur_email": "stanaka@3gpp.org",
            "support_officer_name": "Alain Sultan - 3GPP Secretariat",
            "support_officer_email": "alain.sultan@etsi.org",
            "harmonized_flg": 0,
            "lead_body": "3GPP TSG RAN",
            "scope": "3GPP Release 18 specification for 5G NR User Equipment radio transmission in Frequency Range 1.",
            "pdf_url": "https://www.etsi.org/deliver/etsi_ts/138100_138199/13810101/18.04.00_60/ts_13810101v180400p.pdf",
            "word_url": "https://portal.etsi.org/webapp/WorkProgram/LogonRedirection.asp?WKI_ID=67012&FileFormat=ZIP",
            "detail_url": "https://portal.etsi.org/webapp/WorkProgram/Report_WorkItem.asp?WKI_ID=67012",
            "is_finalized": 1,
            "stop_flg": 0
        },
        {
            "wki_id": "DEN/CYBER-999",
            "doc_type": "EN",
            "doc_number": "303999",
            "version": "v1.1.1",
            "reference": "ETSI EN 303 999",
            "technical_body": "CYBER",
            "title_part1": "CYBER",
            "title_part2": "Cyber Security Test Standard",
            "title_part3": None,
            "full_title": "CYBER; Cyber Security Test Standard",
            "status": "Stopped - Revised",
            "state_code": "STOPPED",
            "status_date": "2026-10-20",
            "creation_date": "2026-10-20",
            "stop_date": "2026-10-20",
            "standstill_status": "NO",
            "standstill_date": None,
            "rapporteur_name": "Alice Tester",
            "rapporteur_email": "alice@etsi.org",
            "support_officer_name": "Bob Admin",
            "support_officer_email": "bob@etsi.org",
            "harmonized_flg": 0,
            "lead_body": None,
            "scope": "Draft standard superseded by v1.2.1 revision.",
            "pdf_url": None,
            "word_url": None,
            "detail_url": None,
            "is_finalized": 0,
            "stop_flg": 1
        },
        {
            "wki_id": "REN/CYBER-999",
            "doc_type": "EN",
            "doc_number": "303999",
            "version": "v1.2.1",
            "reference": "ETSI EN 303 999",
            "technical_body": "CYBER",
            "title_part1": "CYBER",
            "title_part2": "Cyber Security Test Standard",
            "title_part3": None,
            "full_title": "CYBER; Cyber Security Test Standard",
            "status": "Drafting",
            "state_code": "DRAFT",
            "status_date": "2026-10-20",
            "creation_date": "2026-10-20",
            "stop_date": None,
            "standstill_status": "NO",
            "standstill_date": None,
            "rapporteur_name": "Alice Tester",
            "rapporteur_email": "alice@etsi.org",
            "support_officer_name": "Bob Admin",
            "support_officer_email": "bob@etsi.org",
            "harmonized_flg": 0,
            "lead_body": None,
            "scope": "Active revision deliverable for test standard.",
            "pdf_url": None,
            "word_url": None,
            "detail_url": None,
            "is_finalized": 0,
            "stop_flg": 0
        },
        {
            "wki_id": "DTS/CYBER-999",
            "doc_type": "TS",
            "doc_number": "103999",
            "version": "v1.1.1",
            "reference": "ETSI TS 103 999",
            "technical_body": "CYBER",
            "title_part1": "CYBER",
            "title_part2": "Automated English Deliverable",
            "title_part3": None,
            "full_title": "CYBER; Automated English Deliverable",
            "status": "Stopped - Revised",
            "state_code": "STOPPED",
            "status_date": "2026-10-20",
            "creation_date": "2026-10-20",
            "stop_date": "2026-10-20",
            "standstill_status": "NO",
            "standstill_date": None,
            "rapporteur_name": "John Doe",
            "rapporteur_email": "john@etsi.org",
            "support_officer_name": "Jane Officer",
            "support_officer_email": "jane@etsi.org",
            "harmonized_flg": 0,
            "lead_body": None,
            "scope": "Technical Specification retired on revision.",
            "pdf_url": None,
            "word_url": None,
            "detail_url": None,
            "is_finalized": 0,
            "stop_flg": 1
        },
        {
            "wki_id": "RTS/CYBER-999",
            "doc_type": "TS",
            "doc_number": "103999",
            "version": "v1.2.1",
            "reference": "ETSI TS 103 999",
            "technical_body": "CYBER",
            "title_part1": "CYBER",
            "title_part2": "Automated English Deliverable",
            "title_part3": None,
            "full_title": "CYBER; Automated English Deliverable",
            "status": "Drafting",
            "state_code": "DRAFT",
            "status_date": "2026-10-20",
            "creation_date": "2026-10-20",
            "stop_date": None,
            "standstill_status": "NO",
            "standstill_date": None,
            "rapporteur_name": "John Doe",
            "rapporteur_email": "john@etsi.org",
            "support_officer_name": "Jane Officer",
            "support_officer_email": "jane@etsi.org",
            "harmonized_flg": 0,
            "lead_body": None,
            "scope": "Current draft of automated deliverable.",
            "pdf_url": None,
            "word_url": None,
            "detail_url": None,
            "is_finalized": 0,
            "stop_flg": 0
        }
    ]

    for it in items:
        cursor.execute("""
        INSERT INTO work_items (
            wki_id, doc_type, deliv_class, doc_number, version, reference, technical_body,
            title_part1, title_part2, title_part3, full_title, status, state_code,
            status_date, creation_date, stop_date, stop_flg, standstill_status, standstill_date,
            rapporteur_name, rapporteur_email, support_officer_name, support_officer_email,
            harmonized_flg, lead_body, scope, pdf_url, word_url, detail_url, is_finalized
        ) VALUES (
            ?, ?, 'Standard', ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?
        );
        """, (
            it["wki_id"], it["doc_type"], it["doc_number"], it["version"], it["reference"], it["technical_body"],
            it["title_part1"], it["title_part2"], it.get("title_part3"), it["full_title"], it["status"], it["state_code"],
            it["status_date"], it["creation_date"], it.get("stop_date"), it["stop_flg"], it["standstill_status"], it.get("standstill_date"),
            it["rapporteur_name"], it["rapporteur_email"], it["support_officer_name"], it["support_officer_email"],
            it["harmonized_flg"], it.get("lead_body"), it.get("scope"), it.get("pdf_url"), it.get("word_url"), it.get("detail_url"), it.get("is_finalized", 0)
        ))

    # Milestones for EN
    en_schedules = [
        ("DEN/CYBER-0072", "TB_ADOPT", "Technical Body Adoption of Draft", 1, 60, "2024-02-15", "2024-02-15", "ACHIEVED"),
        ("DEN/CYBER-0072", "HANDOVER", "Handover to Secretariat", 2, 15, "2024-03-01", "2024-03-01", "ACHIEVED"),
        ("DEN/CYBER-0072", "PE_START", "Public Enquiry EN Approval Procedure Start", 3, 90, "2024-06-01", "2024-06-01", "ACHIEVED"),
        ("DEN/CYBER-0072", "PE_CLOSE", "Public Enquiry Close & Comment Resolution", 4, 45, "2024-07-15", "2024-07-15", "ACHIEVED"),
        ("DEN/CYBER-0072", "VOTE_START", "National Vote / Member Vote Start", 5, 60, "2024-09-15", "2024-09-15", "ACHIEVED"),
        ("DEN/CYBER-0072", "PUBLISH", "Official Publication of European Standard", 6, 15, "2025-01-20", "2025-01-20", "ACHIEVED"),

        ("REN/ERM-TG28-560", "TB_ADOPT", "Technical Body Adoption of Draft", 1, 60, "2024-06-30", "2024-06-30", "ACHIEVED"),
        ("REN/ERM-TG28-560", "HANDOVER", "Handover to Secretariat", 2, 15, "2024-07-15", "2024-07-15", "ACHIEVED"),
        ("REN/ERM-TG28-560", "PE_START", "Public Enquiry EN Approval Procedure Start", 3, 90, "2025-02-15", "2025-02-15", "IN_PROGRESS"),
        ("REN/ERM-TG28-560", "PE_CLOSE", "Public Enquiry Close & Comment Resolution", 4, 45, "2025-04-01", "2025-04-01", "PENDING"),
        ("REN/ERM-TG28-560", "VOTE_START", "National Vote / Member Vote Start", 5, 60, "2025-06-01", "2025-06-01", "PENDING"),
        ("REN/ERM-TG28-560", "PUBLISH", "Official Publication of European Standard", 6, 15, "2025-07-15", "2025-07-15", "PENDING")
    ]
    for s in en_schedules:
        cursor.execute("""
        INSERT INTO work_item_schedules (wki_id, mls_code, mls_name, sched_position, duration_days, target_date, achieved_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, s)

    # TR Schedules
    tr_schedules = [
        ("DTR/CYBER-0050", "TB_ADOPT", "Technical Body Drafting Complete", 1, 30, "2023-01-15", "2023-01-15", "ACHIEVED"),
        ("DTR/CYBER-0050", "HANDOVER", "Handover to Secretariat", 2, 10, "2023-02-01", "2023-02-01", "ACHIEVED"),
        ("DTR/CYBER-0050", "PUBLISH", "Publication as Technical Report", 3, 10, "2023-04-12", "2023-04-12", "ACHIEVED")
    ]
    for s in tr_schedules:
        cursor.execute("""
        INSERT INTO work_item_schedules (wki_id, mls_code, mls_name, sched_position, duration_days, target_date, achieved_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, s)

    # Frequencies (RED 2014/53/EU)
    cursor.execute("""
    INSERT INTO work_item_frequencies (wki_id, low_freq, high_freq, unit, service_app)
    VALUES ('REN/ERM-TG28-560', 9.0, 3000.0, 'MHz', 'Short Range Devices SRD and Broad Spectrum EMC RED Art. 3.1b');
    """)

    # Mandates
    cursor.execute("""
    INSERT INTO work_item_mandates (wki_id, mandate_code, directive_ref, descript)
    VALUES ('DEN/CYBER-0072', 'M/585', 'RED Directive 2014/53/EU', 'Commission Standardisation Request for cybersecurity in IoT consumer connected radio equipment.');
    """)

    # Remarks
    cursor.execute("""
    INSERT INTO work_item_remarks (wki_id, remark_type, remark_text, author)
    VALUES ('DEN/CYBER-0072', 'AUDIT', 'Standard officially published and cited in the Official Journal of the EU OJEU.', 'ETSI Secretariat');
    """)
    cursor.execute("""
    INSERT INTO work_item_remarks (wki_id, remark_type, remark_text, author)
    VALUES ('REN/ERM-TG28-560', 'PROGRESS', 'Public Enquiry launch confirmed with National Standards Organizations NSOs.', 'Support Officer');
    """)

    conn.commit()
    logger.info("Complete seed data populated with %d items.", len(items))

def search_work_items(
    q: Optional[str] = None,
    doc_type: Optional[str] = None,
    doc_number: Optional[str] = None,
    tb: Optional[str] = None,
    milestone: Optional[str] = None,
    status: Optional[str] = None,
    only_favorites: bool = False,
    include_stopped: bool = False,
    limit: int = 50,
    offset: int = 0
) -> Tuple[int, List[WorkItemSummary]]:
    conn = get_db()
    cursor = conn.cursor()

    where_clauses = []
    params = []

    # Filter out stopped unless requested or searching specifically for stopped
    chosen_status = milestone or status
    if chosen_status and "stop" in chosen_status.lower():
        where_clauses.append("w.stop_flg = 1")
    elif not include_stopped and (not chosen_status or "stop" not in chosen_status.lower()):
        where_clauses.append("w.stop_flg = 0")

    if q and q.strip():
        q_clean = f"%{q.strip()}%"
        where_clauses.append("(w.wki_id LIKE ? OR w.reference LIKE ? OR w.doc_number LIKE ? OR w.full_title LIKE ? OR w.scope LIKE ?)")
        params.extend([q_clean, q_clean, q_clean, q_clean, q_clean])

    if doc_type and doc_type.strip():
        where_clauses.append("w.doc_type = ?")
        params.append(doc_type.strip().upper())

    if doc_number and doc_number.strip():
        where_clauses.append("w.doc_number LIKE ?")
        params.append(f"%{doc_number.strip()}%")

    if tb and tb.strip():
        where_clauses.append("w.technical_body = ?")
        params.append(tb.strip().upper())

    if chosen_status and chosen_status.strip() and "all" not in chosen_status.lower():
        where_clauses.append("w.status LIKE ?")
        params.append(f"%{chosen_status.strip()}%")

    if only_favorites:
        where_clauses.append("f.wki_id IS NOT NULL")

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    count_sql = f"""
    SELECT count(*) as total
    FROM work_items w
    LEFT JOIN favorites f ON w.wki_id = f.wki_id
    {where_sql}
    """
    cursor.execute(count_sql, params)
    total = cursor.fetchone()["total"]

    query_sql = f"""
    SELECT w.wki_id, w.doc_number, w.doc_type, w.version, w.reference, w.technical_body, w.tb_id,
           w.full_title as title, w.status, w.status_date, w.pdf_url, w.word_url, w.detail_url,
           w.is_finalized, w.stop_flg, (f.wki_id IS NOT NULL) as is_fav
    FROM work_items w
    LEFT JOIN favorites f ON w.wki_id = f.wki_id
    {where_sql}
    ORDER BY w.creation_date DESC, w.doc_number DESC
    LIMIT ? OFFSET ?
    """
    cursor.execute(query_sql, params + [limit, offset])
    rows = cursor.fetchall()

    items = [
        WorkItemSummary(
            wki_id=r["wki_id"],
            doc_number=r["doc_number"],
            doc_type=r["doc_type"],
            version=r["version"],
            reference=r["reference"],
            technical_body=r["technical_body"],
            tb_id=r["tb_id"],
            title=r["title"],
            status=r["status"],
            status_date=r["status_date"],
            pdf_url=r["pdf_url"],
            word_url=r["word_url"],
            detail_url=r["detail_url"],
            is_finalized=bool(r["is_finalized"]),
            is_stopped=bool(r["stop_flg"]),
            is_favorite=bool(r["is_fav"])
        )
        for r in rows
    ]

    conn.close()
    return total, items

def get_work_item_detail(wki_id: str) -> Optional[WorkItemDetail]:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM work_items WHERE wki_id = ?", (wki_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    cursor.execute("SELECT wki_id FROM favorites WHERE wki_id = ?", (wki_id,))
    is_fav = bool(cursor.fetchone())

    cursor.execute("SELECT * FROM work_item_schedules WHERE wki_id = ? ORDER BY sched_position ASC", (wki_id,))
    schedule = [
        MilestoneStep(
            sched_id=s["sched_id"],
            wki_id=s["wki_id"],
            mls_code=s["mls_code"],
            mls_name=s["mls_name"],
            sched_position=s["sched_position"],
            duration_days=s["duration_days"],
            original_date=s["original_date"],
            review_date=s["review_date"],
            target_date=s["target_date"],
            achieved_date=s["achieved_date"],
            status=s["status"]
        )
        for s in cursor.fetchall()
    ]

    cursor.execute("SELECT * FROM work_item_frequencies WHERE wki_id = ?", (wki_id,))
    freqs = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM work_item_mandates WHERE wki_id = ?", (wki_id,))
    mandates = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM work_item_remarks WHERE wki_id = ? ORDER BY created_at DESC", (wki_id,))
    remarks = [dict(r) for r in cursor.fetchall()]

    history = []
    if row["parent_wki_id"]:
        history.append({"event": "Derived / Cloned from", "detail": f"{row['parent_reference']} - {row['parent_wki_id']}"})
    if row["creation_date"]:
        history.append({"event": "Created", "detail": row["creation_date"]})
    if row["status_date"]:
        history.append({"event": f"Status updated to {row['status']}", "detail": row["status_date"]})
    if row["stop_date"]:
        history.append({"event": "Stopped / Retired", "detail": row["stop_date"]})

    detail = WorkItemDetail(
        wki_id=row["wki_id"],
        doc_number=row["doc_number"],
        doc_type=row["doc_type"],
        deliv_class=row["deliv_class"],
        reference=row["reference"],
        technical_body=row["technical_body"],
        tb_id=row["tb_id"],
        current_status=row["status"],
        status_date=row["status_date"],
        latest_version=row["version"],
        creation_date=row["creation_date"],
        stop_date=row["stop_date"],
        is_stopped=bool(row["stop_flg"]),
        standstill=row["standstill_status"],
        standstill_date=row["standstill_date"],
        rapporteur_name=row["rapporteur_name"],
        rapporteur_email=row["rapporteur_email"],
        technical_officer_name=row["support_officer_name"],
        technical_officer_email=row["support_officer_email"],
        harmonised_standard="Yes" if row["harmonized_flg"] else "No",
        title_part1=row["title_part1"],
        title_part2=row["title_part2"],
        title_part3=row["title_part3"],
        title=row["full_title"],
        scope_remarks=row["scope"],
        lead_body=row["lead_body"],
        parent_wki_id=row["parent_wki_id"],
        parent_reference=row["parent_reference"],
        pdf_url=row["pdf_url"],
        word_url=row["word_url"],
        detail_url=row["detail_url"],
        is_favorite=is_fav,
        schedule=schedule,
        frequencies=freqs,
        mandates=mandates,
        remarks=remarks,
        history_events=history
    )
    conn.close()
    return detail

def create_work_item(payload: WorkItemCreate) -> WorkItemDetail:
    conn = get_db()
    cursor = conn.cursor()

    if not payload.title_part1 or not payload.title_part1.strip():
        conn.close()
        raise ValueError("Cannot Save: please type in at least Part 1 of Title.")

    doc_type = payload.doc_type.upper()
    doc_number = payload.doc_number.strip()

    # Rule validation
    if doc_type in ("EN", "TS", "TR", "ES", "EG", "SR"):
        try:
            num_val = int(doc_number)
            if num_val < 1000:
                conn.close()
                raise ValueError(f"Statutory Numbering Rule: Deliverable type '{doc_type}' requires a document number >= 1000 - e.g. 303645.")
        except ValueError as e:
            if "Statutory Numbering" in str(e):
                raise e

    part_str = f"-{payload.part_nb}" if payload.part_nb else ""
    reference = f"ETSI {doc_type} {doc_number}{part_str}"
    
    serial = doc_number[-3:] if len(doc_number) >= 3 else doc_number
    wki_id = f"D{doc_type}/{payload.technical_body.upper()}-{serial}"

    cursor.execute("SELECT wki_id FROM work_items WHERE wki_id = ?", (wki_id,))
    if cursor.fetchone():
        wki_id += f"-{datetime.now().strftime('%M%S')}"

    parts = [payload.title_part1.strip()]
    if payload.title_part2 and payload.title_part2.strip():
        parts.append(payload.title_part2.strip())
    if payload.title_part3 and payload.title_part3.strip():
        parts.append(payload.title_part3.strip())
    full_title = f"{payload.technical_body.upper()}; " + "; ".join(parts)

    today = datetime.now().strftime("%Y-%m-%d")
    creation_date = payload.creation_date or today

    cursor.execute("""
    INSERT INTO work_items (
        wki_id, doc_type, deliv_class, doc_number, part_nb, subpart_nb,
        edition_nb, version, reference, technical_body, title_part1,
        title_part2, title_part3, full_title, status, state_code,
        status_date, creation_date, standstill_status, rapporteur_name,
        rapporteur_email, support_officer_name, support_officer_email,
        harmonized_flg, lead_body, scope
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Drafting', 'DRAFT',
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    );
    """, (
        wki_id, doc_type, payload.deliv_class, doc_number, payload.part_nb, payload.subpart_nb,
        payload.edition_nb or "1", payload.version or "v1.1.1", reference, payload.technical_body.upper(),
        payload.title_part1, payload.title_part2, payload.title_part3, full_title,
        today, creation_date, payload.standstill_status, payload.rapporteur_name,
        payload.rapporteur_email, payload.support_officer_name, payload.support_officer_email,
        1 if payload.harmonized_flag else 0, payload.lead_body, payload.scope
    ))

    templates = MILESTONES_TEMPLATES.get(doc_type, MILESTONES_TEMPLATES["TS"])
    base_date = datetime.strptime(creation_date, "%Y-%m-%d")
    for idx, m in enumerate(templates):
        base_date += timedelta(days=m["days"])
        t_date = base_date.strftime("%Y-%m-%d")
        cursor.execute("""
        INSERT INTO work_item_schedules (
            wki_id, mls_code, mls_name, sched_position, duration_days,
            original_date, target_date, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING');
        """, (wki_id, m["code"], m["name"], idx + 1, m["days"], t_date, t_date))

    if payload.ec_mandate:
        cursor.execute("""
        INSERT INTO work_item_mandates (wki_id, mandate_code, directive_ref, descript)
        VALUES (?, ?, ?, ?);
        """, (wki_id, payload.ec_mandate, payload.ec_directive or "RED 2014/53/EU", "EC Mandate assigned on creation"))

    cursor.execute("""
    INSERT INTO work_item_remarks (wki_id, remark_type, remark_text, author)
    VALUES (?, 'CREATION', 'Work Item created via Unified WPM Suite.', ?);
    """, (wki_id, payload.support_officer_name or 'Secretariat'))

    conn.commit()
    conn.close()
    return get_work_item_detail(wki_id)

def update_work_item(wki_id: str, payload: WorkItemUpdate) -> WorkItemDetail:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM work_items WHERE wki_id = ?", (wki_id,))
    item = cursor.fetchone()
    if not item:
        conn.close()
        raise ValueError(f"Work item {wki_id} not found.")

    updates = []
    params = []

    if payload.status:
        updates.append("status = ?")
        params.append(payload.status)
        updates.append("status_date = ?")
        params.append(datetime.now().strftime("%Y-%m-%d"))

    if payload.version:
        updates.append("version = ?")
        params.append(payload.version)

    if payload.rapporteur_name:
        updates.append("rapporteur_name = ?")
        params.append(payload.rapporteur_name)

    if payload.rapporteur_email:
        updates.append("rapporteur_email = ?")
        params.append(payload.rapporteur_email)

    if payload.support_officer_name:
        updates.append("support_officer_name = ?")
        params.append(payload.support_officer_name)

    if payload.support_officer_email:
        updates.append("support_officer_email = ?")
        params.append(payload.support_officer_email)

    if payload.standstill_status:
        updates.append("standstill_status = ?")
        params.append(payload.standstill_status)

    if payload.scope:
        updates.append("scope = ?")
        params.append(payload.scope)

    if payload.harmonized_flag is not None:
        updates.append("harmonized_flg = ?")
        params.append(1 if payload.harmonized_flag else 0)

    if payload.is_stopped is not None:
        updates.append("stop_flg = ?")
        params.append(1 if payload.is_stopped else 0)
        if payload.is_stopped:
            updates.append("stop_date = ?")
            params.append(payload.stop_date or datetime.now().strftime("%Y-%m-%d"))

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(wki_id)
        sql = f"UPDATE work_items SET {', '.join(updates)} WHERE wki_id = ?"
        cursor.execute(sql, params)
        conn.commit()

    conn.close()
    return get_work_item_detail(wki_id)

def clone_work_item(parent_wki_id: str, req: CloneWorkItemRequest) -> WorkItemDetail:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM work_items WHERE wki_id = ?", (parent_wki_id,))
    parent = cursor.fetchone()
    if not parent:
        conn.close()
        raise ValueError(f"Parent Work Item {parent_wki_id} not found.")

    if req.clone_type in ("split", "transfer") and parent["status"] == "Published":
        conn.close()
        raise ValueError("A work item which has been published cannot be transferred or split.")

    today = datetime.now().strftime("%Y-%m-%d")
    doc_type = parent["doc_type"]
    tb = req.new_tb.upper() if req.new_tb else parent["technical_body"]
    doc_num = req.new_doc_number or parent["doc_number"]

    if req.clone_type == "revision":
        new_wki_id = f"R{doc_type}/{tb}-{doc_num[-3:]}"
        ver_parts = parent["version"].replace("v", "").split(".")
        if len(ver_parts) == 3:
            new_version = f"v{ver_parts[0]}.{int(ver_parts[1]) + 1}.1"
        else:
            new_version = "v2.1.1"

        # Statutory Auto-Stop Rule for parent
        cursor.execute("""
        UPDATE work_items
        SET stop_flg = 1, stop_date = ?, status = 'Stopped - Revised'
        WHERE wki_id = ?;
        """, (today, parent_wki_id))

        cursor.execute("""
        INSERT INTO work_item_remarks (wki_id, remark_type, remark_text, author)
        VALUES (?, 'LIFECYCLE', ?, 'System');
        """, (parent_wki_id, f"Automatically stopped due to Revision creation -> {new_wki_id}"))

    elif req.clone_type == "split":
        new_wki_id = f"D{doc_type}/{tb}-{doc_num[-3:]}-SPLIT"
        new_version = parent["version"]
    elif req.clone_type == "transfer":
        new_wki_id = f"D{doc_type}/{tb}-{doc_num[-3:]}"
        new_version = parent["version"]
    else:
        new_wki_id = f"D{doc_type}/{tb}-{doc_num[-3:]}-DUP"
        new_version = "v1.1.1"

    cursor.execute("SELECT wki_id FROM work_items WHERE wki_id = ?", (new_wki_id,))
    if cursor.fetchone():
        new_wki_id += f"-{datetime.now().strftime('%H%M%S')}"

    ref = f"ETSI {doc_type} {doc_num}"
    title_p1 = req.new_title_part1 or parent["title_part1"]
    full_title = f"{tb}; {title_p1}"
    if parent["title_part2"]:
        full_title += f"; {parent['title_part2']}"

    cursor.execute("""
    INSERT INTO work_items (
        wki_id, doc_type, deliv_class, doc_number, part_nb, subpart_nb,
        edition_nb, version, reference, technical_body, title_part1,
        title_part2, title_part3, full_title, status, state_code,
        status_date, creation_date, standstill_status, rapporteur_name,
        rapporteur_email, support_officer_name, support_officer_email,
        harmonized_flg, lead_body, scope, parent_wki_id, parent_reference
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Drafting', 'DRAFT',
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    );
    """, (
        new_wki_id, doc_type, parent["deliv_class"], doc_num, parent["part_nb"], parent["subpart_nb"],
        str(int(parent["edition_nb"] or "1") + 1) if req.clone_type == "revision" else parent["edition_nb"],
        new_version, ref, tb, title_p1, parent["title_part2"], parent["title_part3"], full_title,
        today, today, parent["standstill_status"], parent["rapporteur_name"],
        parent["rapporteur_email"], parent["support_officer_name"], parent["support_officer_email"],
        parent["harmonized_flg"], parent["lead_body"], parent["scope"],
        parent_wki_id, parent["reference"]
    ))

    if req.schedule_option == "original":
        cursor.execute("SELECT * FROM work_item_schedules WHERE wki_id = ? ORDER BY sched_position ASC", (parent_wki_id,))
        for s in cursor.fetchall():
            cursor.execute("""
            INSERT INTO work_item_schedules (
                wki_id, mls_code, mls_name, sched_position, duration_days,
                original_date, target_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING');
            """, (new_wki_id, s["mls_code"], s["mls_name"], s["sched_position"], s["duration_days"], s["target_date"], s["target_date"]))
    elif req.schedule_option == "default":
        templates = MILESTONES_TEMPLATES.get(doc_type, MILESTONES_TEMPLATES["TS"])
        base_d = datetime.strptime(today, "%Y-%m-%d")
        for idx, m in enumerate(templates):
            base_d += timedelta(days=m["days"])
            t_date = base_d.strftime("%Y-%m-%d")
            cursor.execute("""
            INSERT INTO work_item_schedules (
                wki_id, mls_code, mls_name, sched_position, duration_days,
                original_date, target_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING');
            """, (new_wki_id, m["code"], m["name"], idx + 1, m["days"], t_date, t_date))

    if req.retain_comments:
        cursor.execute("SELECT * FROM work_item_remarks WHERE wki_id = ?", (parent_wki_id,))
        for r in cursor.fetchall():
            cursor.execute("""
            INSERT INTO work_item_remarks (wki_id, remark_type, remark_text, author)
            VALUES (?, ?, ?, ?);
            """, (new_wki_id, r["remark_type"], f"[Copied from {parent_wki_id}] {r['remark_text']}", r["author"]))

    cursor.execute("""
    INSERT INTO work_item_remarks (wki_id, remark_type, remark_text, author)
    VALUES (?, 'CLONE', ?, 'System');
    """, (new_wki_id, f"Created via {req.clone_type.upper()} from {parent_wki_id}"))

    conn.commit()
    conn.close()
    return get_work_item_detail(new_wki_id)

def get_next_etsi_number(req: NextNumberRequest) -> NextNumberResponse:
    conn = get_db()
    cursor = conn.cursor()
    doc_type = req.doc_type.upper()

    if doc_type in ("ETS", "I-ETS"):
        rule_desc = "Legacy ETS Rule: Number must be strictly under 1000."
        cursor.execute("SELECT CAST(doc_number AS INTEGER) as num FROM work_items WHERE doc_type = ? AND CAST(doc_number AS INTEGER) < 1000 ORDER BY num DESC LIMIT 1", (doc_type,))
        row = cursor.fetchone()
        next_num = (row["num"] + 1) if row and row["num"] else 300
        formatted_num = f"{next_num:03d}"
    elif doc_type == "GS":
        rule_desc = "ISG Group Specification Rule: Number is under 1000 and scoped to the Technical Body."
        cursor.execute("SELECT CAST(doc_number AS INTEGER) as num FROM work_items WHERE doc_type = 'GS' AND CAST(doc_number AS INTEGER) < 1000 ORDER BY num DESC LIMIT 1")
        row = cursor.fetchone()
        next_num = (row["num"] + 1) if row and row["num"] else 25
        formatted_num = f"{next_num:03d}"
    else:
        rule_desc = "Standard Deliverable Rule: Number must be >= 1000 - series 101 xxx, 300 xxx, 303 xxx."
        cursor.execute("""
        SELECT CAST(doc_number AS INTEGER) as num
        FROM work_items
        WHERE doc_type IN ('EN', 'ES', 'EG', 'TS', 'TR', 'SR') AND CAST(doc_number AS INTEGER) >= 1000
        ORDER BY num DESC
        LIMIT 1
        """)
        row = cursor.fetchone()
        next_num = (row["num"] + 1) if row and row["num"] else 303646
        formatted_num = str(next_num)

    ref_formatted = f"ETSI {doc_type} {formatted_num}"
    candidates = [
        f"{next_num + i:03d}" if doc_type in ("GS", "ETS") else str(next_num + i)
        for i in range(5)
    ]
    conn.close()
    return NextNumberResponse(
        doc_type=doc_type,
        technical_body=req.technical_body,
        assigned_number=formatted_num,
        formatted_reference=ref_formatted,
        rule_applied=rule_desc,
        candidate_numbers=candidates
    )

def compute_perfect_plan(doc_type: str, start_date: str) -> List[Dict[str, Any]]:
    templates = MILESTONES_TEMPLATES.get(doc_type.upper(), MILESTONES_TEMPLATES["TS"])
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    plan = []

    for idx, step in enumerate(templates):
        current_date += timedelta(days=step["days"])
        target_str = current_date.strftime("%Y-%m-%d")
        plan.append({
            "sched_position": idx + 1,
            "mls_code": step["code"],
            "mls_name": step["name"],
            "duration_days": step["days"],
            "target_date": target_str,
            "status": "SCHEDULED"
        })
    return plan

def add_remark(wki_id: str, req: RemarkCreate) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO work_item_remarks (wki_id, remark_type, remark_text, author)
    VALUES (?, ?, ?, ?);
    """, (wki_id, req.remark_type.upper(), req.remark_text, req.author))
    conn.commit()
    conn.close()
    return {"status": "success", "wki_id": wki_id}

def add_frequency(wki_id: str, req: FrequencyCreate) -> Dict[str, Any]:
    if req.low_freq >= req.high_freq:
        raise ValueError("Low frequency must be strictly lower than high frequency.")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO work_item_frequencies (wki_id, low_freq, high_freq, unit, service_app)
    VALUES (?, ?, ?, ?, ?);
    """, (wki_id, req.low_freq, req.high_freq, req.unit, req.service_app))
    conn.commit()
    conn.close()
    return {"status": "success", "wki_id": wki_id}

def add_mandate(wki_id: str, req: MandateCreate) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO work_item_mandates (wki_id, mandate_code, directive_ref, descript)
    VALUES (?, ?, ?, ?);
    """, (wki_id, req.mandate_code, req.directive_ref, req.descript))
    conn.commit()
    conn.close()
    return {"status": "success", "wki_id": wki_id}

def toggle_favorite_db(wki_id: str, doc_number: str = "", title: str = "", tb: str = "", status: str = "") -> bool:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT wki_id FROM favorites WHERE wki_id = ?", (wki_id,))
    if cursor.fetchone():
        cursor.execute("DELETE FROM favorites WHERE wki_id = ?", (wki_id,))
        is_fav = False
    else:
        cursor.execute("""
        INSERT INTO favorites (wki_id, doc_number, title, technical_body, status)
        VALUES (?, ?, ?, ?, ?);
        """, (wki_id, doc_number, title, tb, status))
        is_fav = True

    conn.commit()
    conn.close()
    return is_fav

def get_favorites_db() -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM favorites ORDER BY created_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def clean_parens_text(s: Optional[str]) -> str:
    if not s:
        return ""
    cleaned = re.sub(r'\s*\([^)]*\)', '', s)
    cleaned = cleaned.replace('(', '').replace(')', '')
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    return cleaned.strip()

def save_work_items_to_cache(items: List[WorkItemSummary]):
    conn = get_db()
    cursor = conn.cursor()
    for item in items:
        cursor.execute("""
        INSERT INTO work_items (
            wki_id, doc_type, doc_number, version, reference, technical_body, tb_id,
            title_part1, full_title, status, status_date, pdf_url, word_url,
            detail_url, is_finalized, stop_flg
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(wki_id) DO UPDATE SET
            doc_number=excluded.doc_number,
            version=excluded.version,
            reference=excluded.reference,
            full_title=excluded.full_title,
            status=excluded.status,
            status_date=excluded.status_date,
            pdf_url=excluded.pdf_url,
            word_url=excluded.word_url,
            detail_url=excluded.detail_url,
            is_finalized=excluded.is_finalized,
            updated_at=CURRENT_TIMESTAMP
        """, (
            clean_parens_text(item.wki_id),
            clean_parens_text(item.doc_type or "EN"),
            clean_parens_text(item.doc_number),
            item.version or "v1.1.1",
            clean_parens_text(item.reference or f"ETSI {item.doc_number}"),
            clean_parens_text(item.technical_body or "ETSI"),
            item.tb_id,
            clean_parens_text(item.title[:60]),
            clean_parens_text(item.title),
            clean_parens_text(item.status or "Drafting"),
            item.status_date or datetime.now().strftime("%Y-%m-%d"),
            item.pdf_url,
            item.word_url,
            item.detail_url,
            1 if item.is_finalized else 0,
            1 if item.is_stopped else 0
        ))
    conn.commit()
    conn.close()

def search_cached_items(
    q: Optional[str] = None,
    doc_type: Optional[str] = None,
    doc_number: Optional[str] = None,
    tb: Optional[str] = None,
    milestone: Optional[str] = None,
    limit: int = 25,
    offset: int = 0
) -> Tuple[int, List[WorkItemSummary]]:
    return search_work_items(
        q=q,
        doc_type=doc_type,
        doc_number=doc_number,
        tb=tb,
        milestone=milestone,
        limit=limit,
        offset=offset
    )

def get_kpi_stats() -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT count(*) as total FROM work_items WHERE stop_flg = 0")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT count(DISTINCT technical_body) as total_tb FROM work_items")
    total_tb = cursor.fetchone()["total_tb"]

    cursor.execute("SELECT count(*) as pub FROM work_items WHERE (LOWER(status) LIKE '%publish%' OR LOWER(status) LIKE '%finalized%') AND stop_flg = 0")
    pub = cursor.fetchone()["pub"]

    cursor.execute("SELECT count(*) as draft FROM work_items WHERE (LOWER(status) LIKE '%draft%' OR LOWER(status) LIKE '%underconst%' OR LOWER(status) LIKE '%new%') AND stop_flg = 0")
    draft = cursor.fetchone()["draft"]

    cursor.execute("SELECT count(*) as app FROM work_items WHERE (LOWER(status) LIKE '%approval%' OR LOWER(status) LIKE '%enquiry%' OR LOWER(status) LIKE '%vote%') AND stop_flg = 0")
    app = cursor.fetchone()["app"]

    cursor.execute("SELECT count(*) as stopped FROM work_items WHERE stop_flg = 1")
    stopped = cursor.fetchone()["stopped"]

    cursor.execute("SELECT count(*) as all_recs FROM work_items")
    all_recs = cursor.fetchone()["all_recs"]

    conn.close()
    return {
        "total_active_items": total,
        "total_technical_bodies": total_tb,
        "published_count": pub,
        "drafting_count": draft,
        "approval_count": app,
        "stopped_count": stopped,
        "total_records": all_recs
    }
