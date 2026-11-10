import re
from typing import List, Dict, Any, Tuple, Optional
from bs4 import BeautifulSoup
from .models import WorkItemSummary, WorkItemDetail

BASE_PORTAL_URL = "https://portal.etsi.org"

def normalize_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    # Fix backslashes in Windows file URLs from ETSI legacy code
    cleaned = url.replace("\\", "/")
    if cleaned.startswith("/"):
        return f"{BASE_PORTAL_URL}{cleaned}"
    if cleaned.startswith("./"):
        return f"{BASE_PORTAL_URL}/webapp/WorkProgram/{cleaned[2:]}"
    if cleaned.startswith("../"):
        return f"{BASE_PORTAL_URL}/webapp/WorkProgram/{cleaned[3:]}"
    return cleaned

def parse_work_item_list(html_content: str) -> Tuple[int, List[WorkItemSummary]]:
    """Parse Frame_WorkItemList.asp HTML response into structured list of WorkItemSummary."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Extract total count: "Found <b> 177 </b> Items..."
    total_found = 0
    found_match = re.search(r"Found\s*<\s*b\s*>\s*([\d,]+)\s*<\s*/b\s*>\s*Items", html_content, re.IGNORECASE)
    if found_match:
        total_found = int(found_match.group(1).replace(",", ""))
    else:
        # Fallback check
        alt_match = re.search(r"Found\s+([\d,]+)\s+Items", soup.get_text(), re.IGNORECASE)
        if alt_match:
            total_found = int(alt_match.group(1).replace(",", ""))

    items: List[WorkItemSummary] = []
    
    # Work item rows contain links to Report_WorkItem.asp?WKI_ID=xxx
    # We find table rows with these links
    processed_wki_ids = set()
    
    for tr in soup.find_all("tr"):
        report_link = tr.find("a", href=re.compile(r"Report_WorkItem\.asp\?WKI_ID=(\d+)", re.IGNORECASE))
        if not report_link:
            continue
            
        wki_match = re.search(r"WKI_ID=(\d+)", report_link["href"], re.IGNORECASE)
        if not wki_match:
            continue
            
        wki_id = wki_match.group(1)
        if wki_id in processed_wki_ids:
            continue
        processed_wki_ids.add(wki_id)
        
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue
            
        # TD 0: Index and status image
        is_finalized = bool(tr.find("img", src=re.compile(r"finalized\.gif", re.IGNORECASE)))
        
        # TD 1: Identification info (Doc number, version, reference, technical body)
        td_ident = tds[1] if len(tds) >= 2 else tr
        ident_text = " ".join(td_ident.stripped_strings)
        
        doc_number = report_link.get_text(strip=True)
        doc_type = doc_number.split()[0] if doc_number else None
        
        # Version
        version = None
        ver_match = re.search(r"Ver\.\s*([\d\.]+)", ident_text, re.IGNORECASE)
        if ver_match:
            version = ver_match.group(1)
            
        # Reference
        reference = None
        ref_match = re.search(r"Ref\.\s*([A-Za-z0-9_\-\/]+)", ident_text, re.IGNORECASE)
        if ref_match:
            reference = ref_match.group(1)
            
        # Technical Body
        technical_body = None
        tb_id = None
        tb_link = td_ident.find("a", href=re.compile(r"tb\.aspx\?TBID=(\d+)", re.IGNORECASE))
        if tb_link:
            technical_body = tb_link.get_text(strip=True)
            tb_id_match = re.search(r"TBID=(\d+)", tb_link["href"], re.IGNORECASE)
            if tb_id_match:
                tb_id = tb_id_match.group(1)
        else:
            tb_match = re.search(r"Technical Body:\s*([A-Za-z0-9_\-]+)", ident_text, re.IGNORECASE)
            if tb_match:
                technical_body = tb_match.group(1)
                
        # TD 2: Title & subtitle
        td_title = tds[2] if len(tds) >= 3 else None
        full_title = ""
        subtitle = None
        if td_title:
            sub_tag = td_title.find("font", color=re.compile(r"#?708090", re.IGNORECASE))
            if sub_tag:
                subtitle = sub_tag.get_text(strip=True)
            full_title = td_title.get_text(separator=" ", strip=True)
            if subtitle and subtitle in full_title:
                full_title = full_title.replace(subtitle, "").strip()
        
        # Clean title
        full_title = re.sub(r"\s+", " ", full_title).strip()
        
        # TD 3: Status and direct download links
        status = None
        status_date = None
        pdf_url = None
        word_url = None
        
        if len(tds) >= 4:
            td_status = tds[3]
            status_text = " ".join(td_status.stripped_strings)
            
            # Date in status e.g. "Publication (2024-09-24)"
            date_match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", status_text)
            if date_match:
                status_date = date_match.group(1)
                status = re.sub(r"\(\d{4}-\d{2}-\d{2}\)", "", status_text).strip()
            else:
                status = status_text.strip()
                
            pdf_link = td_status.find("a", href=re.compile(r"\.pdf", re.IGNORECASE))
            if pdf_link:
                pdf_url = normalize_url(pdf_link.get("href"))
                
            word_link = td_status.find("a", href=re.compile(r"LogonRedirection\.asp", re.IGNORECASE))
            if word_link:
                word_url = normalize_url(word_link.get("href"))
                
        detail_url = f"{BASE_PORTAL_URL}/webapp/WorkProgram/Report_WorkItem.asp?WKI_ID={wki_id}"
        
        items.append(WorkItemSummary(
            wki_id=wki_id,
            doc_number=doc_number,
            doc_type=doc_type,
            version=version,
            reference=reference,
            technical_body=technical_body,
            tb_id=tb_id,
            title=full_title or doc_number,
            subtitle=subtitle,
            status=status or "Published" if is_finalized else "Active",
            status_date=status_date,
            pdf_url=pdf_url,
            word_url=word_url,
            detail_url=detail_url,
            is_finalized=is_finalized
        ))
        
    if total_found == 0 and items:
        total_found = len(items)
        
    return total_found, items

def parse_work_item_detail(html_content: str, wki_id: str) -> WorkItemDetail:
    """Parse Report_WorkItem.asp HTML into WorkItemDetail object."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Helper to find cell text next to a label
    def get_text_after_label(label_pattern: str) -> Optional[str]:
        label_cell = soup.find(lambda tag: tag.name in ["td", "th"] and re.search(label_pattern, tag.get_text(), re.IGNORECASE))
        if label_cell:
            next_td = label_cell.find_next_sibling("td")
            if next_td:
                return " ".join(next_td.stripped_strings)
        return None

    # Work Item Ref & Doc number
    reference = None
    doc_number = None
    ref_match = re.search(r"Details of '([^']+)' Work Item", soup.get_text())
    if ref_match:
        reference = ref_match.group(1).strip()
        
    # Technical body
    tb_name = None
    tb_url = None
    tb_link = soup.find("a", href=re.compile(r"tb\.aspx\?TBID=", re.IGNORECASE))
    if tb_link:
        tb_name = tb_link.get_text(strip=True)
        tb_url = normalize_url(tb_link.get("href"))
        
    # Status
    current_status = None
    status_date = None
    status_link = soup.find("a", href=re.compile(r"Report_Schedule\.asp\?WKI_ID=", re.IGNORECASE))
    if status_link:
        raw_status = status_link.get_text(strip=True)
        m = re.search(r"\((\d{4}-\d{2}-\d{2})\)", raw_status)
        if m:
            status_date = m.group(1)
            current_status = raw_status.replace(m.group(0), "").strip()
        else:
            current_status = raw_status

    # Direct links
    pdf_url = None
    pdf_link = soup.find("a", href=re.compile(r"\.pdf", re.IGNORECASE))
    if pdf_link:
        pdf_url = normalize_url(pdf_link.get("href"))
        
    word_url = None
    word_link = soup.find("a", href=re.compile(r"LogonRedirection\.asp", re.IGNORECASE))
    if word_link:
        word_url = normalize_url(word_link.get("href"))
        
    # People (Rapporteur & Technical Officer)
    rapporteur_name = None
    rapporteur_pers_id = None
    tech_officer_name = None
    tech_officer_pers_id = None
    
    pers_links = soup.find_all("a", href=re.compile(r"ListPersDetails\.asp\?PersId=(\d+)", re.IGNORECASE))
    if len(pers_links) >= 1:
        rapporteur_name = pers_links[0].get_text(strip=True)
        m = re.search(r"PersId=(\d+)", pers_links[0]["href"])
        if m:
            rapporteur_pers_id = m.group(1)
            
    if len(pers_links) >= 2:
        tech_officer_name = pers_links[1].get_text(strip=True)
        m = re.search(r"PersId=(\d+)", pers_links[1]["href"])
        if m:
            tech_officer_pers_id = m.group(1)
            
    # Standstill
    standstill_link = soup.find("a", href=re.compile(r"StandstillResults\.asp", re.IGNORECASE))
    standstill_url = normalize_url(standstill_link.get("href")) if standstill_link else None

    # Title extraction
    title = ""
    title_cell = soup.find(lambda tag: tag.name == "td" and "Title" in tag.get_text())
    if title_cell:
        content_cell = title_cell.find_next_sibling("td")
        if content_cell:
            title = " ".join(content_cell.stripped_strings)

    # Version, creation date, cover date
    version = None
    creation_date = None
    cover_date = None
    
    # Try pattern matching on whole text
    full_text = soup.get_text()
    date_matches = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", full_text)
    if date_matches:
        if len(date_matches) >= 1 and not status_date:
            status_date = date_matches[0]
        if len(date_matches) >= 2:
            cover_date = date_matches[1]
        if len(date_matches) >= 3:
            creation_date = date_matches[2]
            
    # History timeline extraction (contributions, revisions, decisions)
    history_events: List[Dict[str, str]] = []
    for line in full_text.splitlines():
        line = line.strip()
        if any(keyword in line for keyword in ["Draft contributed", "proposal in contribution", "TB adoption of WI", "WI proposed to TB"]):
            history_events.append({"event": line})

    # If doc_number was not directly found in the header, look for standard type
    doc_num_match = re.search(r"\b(EN|TS|TR|ES|EG|GS|GR|SR)\s+(\d{3}\s*\d{3}|\d{5,6})\b", full_text)
    if doc_num_match:
        doc_number = doc_num_match.group(0)
    else:
        doc_number = reference or f"WKI-{wki_id}"

    return WorkItemDetail(
        wki_id=wki_id,
        doc_number=doc_number,
        reference=reference,
        technical_body=tb_name,
        tb_url=tb_url,
        current_status=current_status or "Published",
        status_date=status_date,
        latest_version=version or "Current",
        cover_date=cover_date,
        creation_date=creation_date,
        standstill="Available" if standstill_url else "None",
        standstill_url=standstill_url,
        rapporteur_name=rapporteur_name,
        rapporteur_pers_id=rapporteur_pers_id,
        technical_officer_name=tech_officer_name,
        technical_officer_pers_id=tech_officer_pers_id,
        title=title or doc_number,
        pdf_url=pdf_url,
        word_url=word_url,
        history_events=history_events[:20]
    )
