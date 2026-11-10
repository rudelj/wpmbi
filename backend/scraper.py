import logging
import httpx
from typing import Optional, Tuple, List, Dict, Any
from .models import SearchQuery, SearchResponse, WorkItemSummary, WorkItemDetail
from .parser import parse_work_item_list, parse_work_item_detail
from .db import save_work_items_to_cache, search_cached_items

logger = logging.getLogger("etsi_wkp.scraper")

ETSI_PORTAL_BASE = "https://portal.etsi.org"
ETSI_WORK_PROGRAM_FRAME = f"{ETSI_PORTAL_BASE}/webapp/WorkProgram/Frame_WorkItemList.asp"
ETSI_REPORT_WORK_ITEM = f"{ETSI_PORTAL_BASE}/webapp/WorkProgram/Report_WorkItem.asp"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
}

# Pre-indexed Technical Bodies from ETSI Work Programme
TECHNICAL_BODIES_CATALOG = [
    {"id": "369;3GPP", "code": "3GPP", "name": "3GPP - Third Generation Partnership Project"},
    {"id": "858;ARF", "code": "ARF", "name": "ARF - Augmented Reality Framework"},
    {"id": "689;ATTM", "code": "ATTM", "name": "ATTM - Access, Terminals, Transmission and Multiplexing"},
    {"id": "6;BOARD", "code": "BOARD", "name": "BOARD - Board"},
    {"id": "287;BRAN", "code": "BRAN", "name": "BRAN - Broadband Radio Access Networks"},
    {"id": "92;BROADCAST", "code": "BROADCAST", "name": "BROADCAST - EBU/CENELEC/ETSI on Broadcasting"},
    {"id": "786;CABLE", "code": "CABLE", "name": "CABLE - Integrated broadband cable telecommunication networks"},
    {"id": "943;CCS", "code": "CCS", "name": "CCS - Critical Communications Systems"},
    {"id": "854;CIM", "code": "CIM", "name": "CIM - cross-cutting Context Information Management"},
    {"id": "824;CYBER", "code": "CYBER", "name": "CYBER - Cyber Security"},
    {"id": "922;DATA", "code": "DATA", "name": "DATA - Data Solutions"},
    {"id": "19;DECT", "code": "DECT", "name": "DECT - Digital Enhanced Cordless Telecommunications"},
    {"id": "28;EE", "code": "EE", "name": "EE - Environmental Engineering"},
    {"id": "696;eHEALTH", "code": "eHEALTH", "name": "eHEALTH - eHEALTH"},
    {"id": "658;EMTEL", "code": "EMTEL", "name": "EMTEL - Emergency Communications"},
    {"id": "857;ENI", "code": "ENI", "name": "ENI - Experiential Networked Intelligence"},
    {"id": "286;ERM", "code": "ERM", "name": "ERM - EMC and Radio Spectrum Matters"},
    {"id": "607;ESI", "code": "ESI", "name": "ESI - Electronic Signatures and Trust Infrastructures"},
    {"id": "78;GA", "code": "GA", "name": "GA - General Assembly"},
    {"id": "80;HF", "code": "HF", "name": "HF - Human Factors"},
    {"id": "715;INT", "code": "INT", "name": "INT - Core Network and Interoperability Testing"},
    {"id": "912;ISAC", "code": "ISAC", "name": "ISAC - Integrated Sensing And Communications"},
    {"id": "702;ITS", "code": "ITS", "name": "ITS - Intelligent Transport Systems"},
    {"id": "608;LI", "code": "LI", "name": "LI - Lawful Interception"},
    {"id": "920;MAT", "code": "MAT", "name": "MAT - Multiple Access Techniques"},
    {"id": "826;MEC", "code": "MEC", "name": "MEC - Multi-access Edge Computing"},
    {"id": "520;MSG", "code": "MSG", "name": "MSG - Mobile Standards Group"},
    {"id": "97;MTS", "code": "MTS", "name": "MTS - Methods for Testing & Specification"},
    {"id": "949;NET", "code": "NET", "name": "NET - Federated Network, Edge, Cloud, and AI Technologies"},
    {"id": "789;NFV", "code": "NFV", "name": "NFV - Network Functions Virtualisation"},
    {"id": "283;OCG", "code": "OCG", "name": "OCG - Operational Co-ordination Group"},
    {"id": "773;OEU", "code": "OEU", "name": "OEU - Operational energy Efficiency for Users"},
    {"id": "787;oneM2M", "code": "oneM2M", "name": "oneM2M - oneM2M"},
    {"id": "911;OSL", "code": "OSL", "name": "OSL - OpenSlice"},
    {"id": "723;QKD", "code": "QKD", "name": "QKD - Quantum Key Distribution"},
    {"id": "927;QT", "code": "QT", "name": "QT - Quantum Technologies"},
    {"id": "713;RRS", "code": "RRS", "name": "RRS - Reconfigurable Radio Systems"},
    {"id": "549;RT", "code": "RT", "name": "RT - Railway telecommunications"},
    {"id": "362;SAFETY", "code": "SAFETY", "name": "SAFETY - Safety"},
    {"id": "160;SAGE", "code": "SAGE", "name": "SAGE - Security Algorithms Group of Experts"},
    {"id": "913;SAI", "code": "SAI", "name": "SAI - Securing Artificial Intelligence TC"},
    {"id": "162;SES", "code": "SES", "name": "SES - Satellite Earth Stations & Systems"},
    {"id": "534;SET", "code": "SET", "name": "SET - Secure Element Technologies"},
    {"id": "804;SmartBAN", "code": "SmartBAN", "name": "SmartBAN - Smart Body Area Network"},
    {"id": "275;STQ", "code": "STQ", "name": "STQ - Speech and multimedia Transmission Quality"},
    {"id": "218;TCCE", "code": "TCCE", "name": "TCCE - TETRA and Critical Communications Evolution"},
    {"id": "908;THz", "code": "THz", "name": "THz - TeraHertz technology"},
    {"id": "242;USER", "code": "USER", "name": "USER - User Group"},
    {"id": "862;ZSM", "code": "ZSM", "name": "ZSM - Zero-touch network and Service Management"}
]

STANDARD_TYPES_CATALOG = [
    {"code": "'EN'", "label": "EN - European Standard"},
    {"code": "'TS'", "label": "TS - Technical Specification"},
    {"code": "'TR'", "label": "TR - Technical Report"},
    {"code": "'ES'", "label": "ES - ETSI Standard"},
    {"code": "'EG'", "label": "EG - ETSI Guide"},
    {"code": "'GS'", "label": "GS - Group Specification"},
    {"code": "'GR'", "label": "GR - Group Report"},
    {"code": "'SR'", "label": "SR - Special Report"},
    {"code": "'ETS'", "label": "ETS - European Telecommunication Standard"},
    {"code": "'I-ETS'", "label": "I-ETS - Interim ETS"},
    {"code": "'TBR'", "label": "TBR - Technical Basis for Regulation"}
]

MILESTONES_CATALOG = [
    {"code": "4", "label": "Published"},
    {"code": "3", "label": "Approval Stage"},
    {"code": "2", "label": "Drafting Stage"},
    {"code": "1", "label": "New Work Item"},
    {"code": "5", "label": "Withdrawal Stage"},
    {"code": "6", "label": "Withdrawn"},
    {"code": "7", "label": "Historical"},
    {"code": "8", "label": "Stopped"},
    {"code": "9", "label": "Transferred"},
    {"code": "10", "label": "Under Construction"}
]

async def query_live_work_items(query: SearchQuery) -> Tuple[int, List[WorkItemSummary]]:
    """Execute live HTTP GET against ETSI portal Frame_WorkItemList.asp."""
    # Build query parameters matching legacy ASP requirements
    params: Dict[str, Any] = {
        "SearchPage": "TRUE",
        "qSORT": query.sort_by or "HIGHVERSION",
        "qINCLUDE_SUB_TB": "True" if query.include_sub_tb else "False",
        "qREPORT_TYPE": "SUMMARY",
        "optDisplay": "ALL" if query.display_limit >= 100 else str(query.display_limit),
    }

    if query.doc_number:
        params["qETSI_NUMBER"] = query.doc_number.strip()
    elif query.q_text and query.q_text.strip().isdigit():
        params["qETSI_NUMBER"] = query.q_text.strip()

    if query.doc_type:
        val = query.doc_type if query.doc_type.startswith("'") else f"'{query.doc_type}'"
        params["qETSI_STANDARD_TYPE"] = val

    if query.all_versions:
        params["qETSI_ALL"] = "TRUE"

    if query.technical_body:
        tb_val = query.technical_body.strip()
        # Find ID if just code was passed
        if ";" not in tb_val:
            for item in TECHNICAL_BODIES_CATALOG:
                if item["code"].lower() == tb_val.lower():
                    tb_val = item["id"]
                    break
        params["qTB_ID"] = tb_val

    if query.milestone:
        params["qMILESTONE"] = str(query.milestone)

    if query.include_moved_on:
        params["qINCLUDE_MOVED_ON"] = "True"

    logger.info("Calling ETSI Portal Frame_WorkItemList with params: %s", params)

    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True, headers=DEFAULT_HEADERS) as client:
            resp = await client.get(ETSI_WORK_PROGRAM_FRAME, params=params)
            resp.raise_for_status()
            
            total_found, items = parse_work_item_list(resp.text)
            
            # Post-filter if free text query was supplied and not numeric
            if query.q_text and not query.q_text.strip().isdigit():
                term = query.q_text.lower().strip()
                filtered = [
                    it for it in items 
                    if term in it.title.lower() or term in it.doc_number.lower() or (it.reference and term in it.reference.lower())
                ]
                total_found = len(filtered)
                items = filtered
                
            # Cache items in background SQLite
            if items:
                save_work_items_to_cache(items)
                
            return total_found, items
    except Exception as e:
        logger.error("Live ETSI portal query failed (%s), falling back to local SQLite cache", e)
        cached = search_cached_items(
            q=query.q_text or query.doc_number,
            doc_type=query.doc_type,
            tb=query.technical_body,
            limit=query.display_limit
        )
        return len(cached), cached

async def get_live_work_item_detail(wki_id: str) -> Optional[WorkItemDetail]:
    """Retrieve detailed metadata for a single Work Item via Report_WorkItem.asp."""
    url = f"{ETSI_REPORT_WORK_ITEM}?WKI_ID={wki_id}"
    try:
        async with httpx.AsyncClient(timeout=12.0, verify=False, follow_redirects=True, headers=DEFAULT_HEADERS) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return parse_work_item_detail(resp.text, wki_id)
    except Exception as e:
        logger.error("Failed to fetch detail for WKI %s: %s", wki_id, e)
        # Check SQLite cache
        cached = search_cached_items(q=wki_id, limit=1)
        if cached:
            c = cached[0]
            return WorkItemDetail(
                wki_id=c.wki_id,
                doc_number=c.doc_number,
                reference=c.reference,
                technical_body=c.technical_body,
                current_status=c.status,
                status_date=c.status_date,
                latest_version=c.version,
                title=c.title,
                pdf_url=c.pdf_url,
                word_url=c.word_url
            )
        return None
