import os
import io
import csv
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, JSONResponse

from .models import (
    WorkItemSummary,
    WorkItemDetail,
    WorkItemCreate,
    WorkItemUpdate,
    CloneWorkItemRequest,
    NextNumberRequest,
    NextNumberResponse,
    PerfectPlanRequest,
    RemarkCreate,
    FrequencyCreate,
    MandateCreate,
    SearchQuery,
    SearchResponse,
    KPIStats
)
from .db import (
    init_sqlite_db,
    search_work_items,
    get_work_item_detail,
    create_work_item,
    update_work_item,
    clone_work_item,
    get_next_etsi_number,
    compute_perfect_plan,
    add_remark,
    add_frequency,
    add_mandate,
    toggle_favorite_db,
    get_favorites_db,
    get_kpi_stats,
    get_technical_bodies,
    STANDARD_TYPES,
    TECHNICAL_BODIES,
    MILESTONES_TEMPLATES
)
from .scraper import query_live_work_items

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("etsi_wpm_suite.app")

app = FastAPI(
    title="ETSI WPM Unified Management Suite",
    version="3.0.0-unified",
    description="Unified Administration Back-Office & Delegate Consultation Portal - Merging WPM.exe & WPM Web",
    root_path=os.environ.get("ROOT_PATH", "")
)

@app.on_event("startup")
async def on_startup():
    init_sqlite_db()
    logger.info("ETSI WPM Unified Management Suite initialized successfully.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

@app.api_route("/api/health", methods=["GET", "HEAD"])
def health():
    return {
        "status": "online",
        "service": "ETSI WPM Unified Management Suite",
        "version": "3.0.0-unified",
        "components": [
            "WPM.exe Administration Suite",
            "WPM Web Public & Delegate Portal"
        ],
        "database": "sqlite_unified_ready",
        "graphic_charter": "ETSI Directory Services 2.0"
    }

@app.get("/api/meta")
def get_metadata():
    return {
        "standard_types": STANDARD_TYPES,
        "technical_bodies": get_technical_bodies(),
        "milestones_templates": MILESTONES_TEMPLATES
    }

@app.get("/api/technical-bodies")
def list_technical_bodies():
    return get_technical_bodies()

@app.get("/api/kpis")
def get_kpis():
    return get_kpi_stats()

@app.get("/api/work-items")
def list_work_items(
    q: Optional[str] = Query(None),
    doc_type: Optional[str] = Query(None),
    doc_number: Optional[str] = Query(None),
    tb: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    milestone: Optional[str] = Query(None),
    only_favorites: bool = Query(False),
    include_stopped: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    total, items = search_work_items(
        q=q,
        doc_type=doc_type,
        doc_number=doc_number,
        tb=tb,
        status=status,
        milestone=milestone,
        only_favorites=only_favorites,
        include_stopped=include_stopped,
        limit=limit,
        offset=offset
    )
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": items
    }

@app.get("/api/search")
def search_get(
    q: Optional[str] = Query(None),
    doc_type: Optional[str] = Query(None),
    doc_number: Optional[str] = Query(None),
    tb: Optional[str] = Query(None),
    milestone: Optional[str] = Query(None),
    only_favorites: bool = Query(False),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    total, items = search_work_items(
        q=q,
        doc_type=doc_type,
        doc_number=doc_number,
        tb=tb,
        milestone=milestone,
        only_favorites=only_favorites,
        limit=limit,
        offset=offset
    )
    return SearchResponse(
        total_found=total,
        offset=offset,
        limit=limit,
        items=items,
        query_echo={
            "q": q,
            "doc_type": doc_type,
            "doc_number": doc_number,
            "tb": tb,
            "milestone": milestone,
            "only_favorites": only_favorites
        }
    )

@app.post("/api/search")
def search_post(query: SearchQuery):
    total, items = search_work_items(
        q=query.q_text,
        doc_type=query.doc_type,
        doc_number=query.doc_number,
        tb=query.technical_body,
        milestone=query.milestone,
        limit=query.display_limit,
        offset=query.offset
    )
    return SearchResponse(
        total_found=total,
        offset=query.offset,
        limit=query.display_limit,
        items=items,
        query_echo=query.dict()
    )

@app.get("/api/work-items/{wki_id:path}")
def get_work_item(wki_id: str):
    detail = get_work_item_detail(wki_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Work Item '{wki_id}' not found.")
    return detail

@app.post("/api/work-items")
def create_wi(payload: WorkItemCreate):
    try:
        return create_work_item(payload)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to create work item")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/work-items/{wki_id:path}")
def update_wi(wki_id: str, payload: WorkItemUpdate):
    try:
        return update_work_item(wki_id, payload)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to update work item")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-items/{wki_id:path}/clone")
def clone_wi(wki_id: str, req: CloneWorkItemRequest):
    try:
        return clone_work_item(wki_id, req)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to clone work item")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-items/{wki_id:path}/remarks")
def post_remark(wki_id: str, req: RemarkCreate):
    try:
        return add_remark(wki_id, req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/work-items/{wki_id:path}/frequencies")
def post_frequency(wki_id: str, req: FrequencyCreate):
    try:
        return add_frequency(wki_id, req)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/work-items/{wki_id:path}/mandates")
def post_mandate(wki_id: str, req: MandateCreate):
    try:
        return add_mandate(wki_id, req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/numbering/next")
def generate_number(req: NextNumberRequest):
    return get_next_etsi_number(req)

@app.post("/api/schedule/perfect-plan")
def calculate_plan(req: PerfectPlanRequest):
    try:
        plan = compute_perfect_plan(req.doc_type, req.start_date)
        return {"doc_type": req.doc_type, "start_date": req.start_date, "plan": plan}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/favorites/toggle")
def toggle_favorite(payload: dict):
    wki_id = payload.get("wki_id")
    if not wki_id:
        raise HTTPException(status_code=400, detail="wki_id is required")
    is_fav = toggle_favorite_db(
        wki_id=wki_id,
        doc_number=payload.get("doc_number", ""),
        title=payload.get("title", ""),
        tb=payload.get("technical_body", ""),
        status=payload.get("status", "")
    )
    return {"wki_id": wki_id, "is_favorite": is_fav}

@app.get("/api/favorites")
def list_favorites():
    return get_favorites_db()

@app.post("/api/sync/portal")
async def sync_portal(
    query: Optional[str] = Query(None),
    tb: Optional[str] = Query(None),
    doc_type: Optional[str] = Query(None)
):
    """Triggers live synchronization with ETSI public portal."""
    try:
        types_to_sync = [doc_type] if doc_type else ["EN", "TS", "TR", "GS", "ES"]
        total_found = 0
        all_synced = []
        for dt in types_to_sync:
            search_req = SearchQuery(q_text=query, technical_body=tb, doc_type=dt, display_limit=50)
            sub_total, items = await query_live_work_items(search_req)
            total_found += sub_total
            all_synced.extend(items)

        return {
            "status": "success",
            "message": f"Successfully synchronized with ETSI Portal: found {total_found} deliverables, cached {len(all_synced)} active records.",
            "synced_count": len(all_synced),
            "total_found": total_found
        }
    except Exception as e:
        logger.warning("Sync from ETSI public portal failed: %s", str(e))
        return {
            "status": "offline_mode",
            "message": f"Could not reach external portal: {str(e)}. Local database is unaffected."
        }

@app.get("/api/export")
def export_data(
    format: str = Query("csv", pattern="^(csv|json)$"),
    tb: Optional[str] = None,
    doc_type: Optional[str] = None,
    milestone: Optional[str] = None,
    status: Optional[str] = None,
    doc_number: Optional[str] = None,
    include_stopped: bool = False
):
    total, items = search_work_items(
        doc_type=doc_type,
        doc_number=doc_number,
        tb=tb,
        milestone=milestone,
        status=status,
        include_stopped=include_stopped,
        limit=1000,
        offset=0
    )

    if format == "json":
        return [it.dict() for it in items]

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow([
        "Work Item ID", "Reference", "Type", "Doc Number", "Technical Body",
        "Version", "Status", "Status Date", "Title", "Stopped", "PDF URL"
    ])
    for item in items:
        writer.writerow([
            item.wki_id, item.reference, item.doc_type, item.doc_number, item.technical_body,
            item.version, item.status, item.status_date, item.title, "YES" if item.is_stopped else "NO",
            item.pdf_url or ""
        ])
    output.seek(0)
    filename = f"etsi_wpm_suite_export_{tb or 'all'}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

WIKI_DIR = os.path.join(STATIC_DIR, "wiki")
if os.path.exists(WIKI_DIR):
    app.mount("/wiki", StaticFiles(directory=WIKI_DIR, html=True), name="wiki")

@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "ETSI WPM Unified Suite is running."}
