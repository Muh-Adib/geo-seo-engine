import os
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from db.session import get_db, SessionLocal
from db.models import Brand, Service, LocationTarget, Article
from generators.geo_writer import ProgrammaticGEOWriter
from generators.link_injector import LinkInjector
from core.bridge_client import WordPressBridgeClient
import mcp.server as mcp_tools

logger = logging.getLogger("seo_web_app")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Unicam Programmatic Local SEO & GEO Engine",
    description="Multi-Tenant 10-Brand Automated Content Engine for Local SEO & Generative Engine Optimization",
    version="1.0.0"
)

templates = Jinja2Templates(directory="web/templates")
if os.path.exists("web/static"):
    app.mount("/static", StaticFiles(directory="web/static"), name="static")

geo_writer = ProgrammaticGEOWriter()
link_injector = LinkInjector()
bridge_client = WordPressBridgeClient()

# Request Models
class PreviewRequest(BaseModel):
    brand_id: str
    service_id: str
    location_region: str
    city_name: Optional[str] = None

class PublishRequest(BaseModel):
    brand_id: str
    service_id: str
    location_region: str
    city_name: Optional[str] = None
    status: str = "publish"
    username: Optional[str] = None
    password: Optional[str] = None
    login_path: Optional[str] = "/pawon/"

class BulkMatrixRequest(BaseModel):
    brand_id: str
    service_id: str
    location_region: str
    cities: List[str]
    auto_publish: bool = False

class SheetImportRequest(BaseModel):
    sheet_url: Optional[str] = None
    csv_content: Optional[str] = None

class GeminiAccountRequest(BaseModel):
    email: Optional[str] = None
    credential: str
    auth_type: str = "api_key"

class CreateBrandRequest(BaseModel):
    name: str
    domain_url: str
    hq_location: str = "Yogyakarta, Indonesia"
    default_language: str = "en"
    revision_guarantee: str = "Free 2x revision guarantee"
    master_output_spec: str = "Uncompressed 4K master files"
    service_name: Optional[str] = None
    target_region: Optional[str] = None
    cities: Optional[List[str]] = None

@app.get("/", response_class=HTMLResponse)
def dashboard_view(request: Request, db: Session = Depends(get_db)):
    brands = db.query(Brand).all()
    articles_count = db.query(Article).count()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "brands": [b.to_dict() for b in brands],
            "total_articles": articles_count
        }
    )

@app.get("/api/brands")
def list_brands(db: Session = Depends(get_db)):
    brands = db.query(Brand).all()
    return {"brands": [b.to_dict() for b in brands]}

@app.post("/api/brands")
def create_brand(req: CreateBrandRequest, db: Session = Depends(get_db)):
    """Allows user to setup brands one by one."""
    import re
    brand_id = re.sub(r'[^a-z0-9]+', '', req.name.lower())[:20]
    if not brand_id:
        raise HTTPException(status_code=400, detail="Invalid brand name")
    
    existing = db.query(Brand).filter(Brand.id == brand_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Brand already exists")

    brand = Brand(
        id=brand_id,
        name=req.name,
        slug=re.sub(r'[^a-z0-9]+', '-', req.name.lower()).strip('-'),
        platform="WORDPRESS",
        domain_url=req.domain_url.rstrip('/'),
        wp_endpoint_url=f"{req.domain_url.rstrip('/')}/wp-json/seo-engine/v1/publish",
        hq_location=req.hq_location,
        default_language=req.default_language,
        revision_guarantee=req.revision_guarantee,
        master_output_spec=req.master_output_spec,
        cta_tagline=f"🎥 Elevate your visual content with {req.name}."
    )
    db.add(brand)
    db.flush()

    # Optional initial service
    if req.service_name:
        srv_id = f"{brand_id}-{re.sub(r'[^a-z0-9]+', '-', req.service_name.lower())[:25].strip('-')}"
        srv = Service(
            id=srv_id,
            brand_id=brand_id,
            name=req.service_name,
            pillar_url=f"{req.domain_url.rstrip('/')}/services/{re.sub(r'[^a-z0-9]+', '-', req.service_name.lower())}",
            anchor_variations=json.dumps([req.service_name]),
            target_personas=json.dumps(["Marketing Directors", "Founders"]),
            target_industries=json.dumps(["Commercial", "Enterprise"]),
            base_tags=json.dumps([req.service_name.lower(), f"{req.name.lower()} studio"])
        )
        db.add(srv)

    # Optional initial location
    if req.target_region:
        loc_id = f"{brand_id}-{re.sub(r'[^a-z0-9]+', '-', req.target_region.lower())}"
        loc = LocationTarget(
            id=loc_id,
            brand_id=brand_id,
            region_name=req.target_region,
            sub_cities=json.dumps(req.cities or [req.target_region]),
            location_tags=json.dumps([f"{c} studio" for c in (req.cities or [req.target_region])])
        )
        db.add(loc)

    db.commit()
    return {"success": True, "brand": brand.to_dict()}

@app.delete("/api/brands/{brand_id}")
def delete_brand(brand_id: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    db.delete(brand)
    db.commit()
    return {"success": True, "deleted": brand_id}

# Gemini Multi-Account Endpoints
@app.get("/api/gemini/accounts")
def get_gemini_accounts():
    return geo_writer.gemini.get_accounts_summary()

@app.post("/api/gemini/connect-antigravity")
def connect_antigravity():
    acc = geo_writer.gemini.auth.auto_connect_antigravity()
    if acc:
        return {"success": True, "account": acc}
    raise HTTPException(status_code=404, detail="No active Antigravity/Gemini Desktop session detected on this machine.")

@app.post("/api/gemini/add-account")
def add_gemini_account(req: GeminiAccountRequest):
    res = geo_writer.gemini.add_account(
        email=req.email or "user@google.com",
        credential=req.credential,
        auth_type=req.auth_type
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@app.delete("/api/gemini/accounts/{account_id}")
def remove_gemini_account(account_id: str):
    removed = geo_writer.gemini.remove_account(account_id)
    return {"success": removed}

@app.post("/api/reset-database")
def reset_database(db: Session = Depends(get_db)):
    """Clears all brands, services, locations, articles to give a clean onboarding state."""
    db.query(Article).delete()
    db.query(LocationTarget).delete()
    db.query(Service).delete()
    db.query(Brand).delete()
    db.commit()
    return {"success": True, "message": "Database reset to 0 brands. Ready for brand-by-brand onboarding."}

@app.get("/api/brands/{brand_id}/context")
def get_brand_context(brand_id: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    services = db.query(Service).filter(Service.brand_id == brand_id).all()
    locations = db.query(LocationTarget).filter(LocationTarget.brand_id == brand_id).all()
    return {
        "brand": brand.to_dict(),
        "services": [s.to_dict() for s in services],
        "locations": [loc.to_dict() for loc in locations]
    }

@app.post("/api/preview")
def generate_preview(req: PreviewRequest):
    result = mcp_tools.tool_preview_seo_article(
        brand_id=req.brand_id,
        service_id=req.service_id,
        location_region=req.location_region,
        city_name=req.city_name
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.post("/api/publish")
def publish_article(req: PublishRequest):
    credentials = None
    if req.username and req.password:
        credentials = {
            "username": req.username,
            "password": req.password,
            "login_path": req.login_path or "/pawon/"
        }
    
    result = mcp_tools.tool_publish_to_site(
        brand_id=req.brand_id,
        service_id=req.service_id,
        location_region=req.location_region,
        city_name=req.city_name,
        status=req.status,
        login_credentials=credentials
    )
    return result

@app.post("/api/generate-bulk")
def generate_bulk(req: BulkMatrixRequest):
    result = mcp_tools.tool_generate_bulk_matrix(
        brand_id=req.brand_id,
        service_id=req.service_id,
        location_region=req.location_region,
        cities=req.cities,
        auto_publish=req.auto_publish
    )
    return result

@app.post("/api/import-sheet")
def import_sheet(req: SheetImportRequest, db: Session = Depends(get_db)):
    """Imports matrix bank data from a Google Sheet URL or CSV content."""
    from importers.sheet_importer import SpreadsheetImporter
    importer = SpreadsheetImporter()
    try:
        if req.sheet_url:
            csv_text = importer.fetch_google_sheet_csv(req.sheet_url)
        elif req.csv_content:
            csv_text = req.csv_content
        else:
            raise HTTPException(status_code=400, detail="Either sheet_url or csv_content must be provided.")
        
        result = importer.parse_and_sync(csv_text, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/download-template")
def download_template():
    """Serves the matrix template CSV for spreadsheet data entry."""
    from fastapi.responses import FileResponse
    return FileResponse("data/matrix_template.csv", media_type="text/csv", filename="matrix_template.csv")

@app.get("/api/articles")
def list_articles(limit: int = 50, db: Session = Depends(get_db)):
    articles = db.query(Article).order_by(Article.created_at.desc()).limit(limit).all()
    return {"articles": [a.to_dict() for a in articles]}

@app.get("/api/diagnostics/system")
def system_diagnostics(db: Session = Depends(get_db)):
    brands_count = db.query(Brand).count()
    articles_count = db.query(Article).count()
    services_count = db.query(Service).count()
    openrouter_configured = bool(os.getenv("OPENROUTER_API_KEY"))
    
    return {
        "status": "operational",
        "brands_loaded": brands_count,
        "services_configured": services_count,
        "articles_registered": articles_count,
        "openrouter_connected": openrouter_configured,
        "default_model": os.getenv("OPENROUTER_MODEL", "openrouter/free")
    }

@app.post("/api/diagnostics/wp-test")
def test_wp_connection(brand_id: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    endpoint = brand.wp_endpoint_url
    if not endpoint:
        return {"status": "unconfigured", "message": "No bridge endpoint configured for this brand yet."}
    
    health_url = endpoint.replace("/publish", "/health")
    try:
        import requests
        resp = requests.get(health_url, headers={"X-SEO-Engine-Key": brand.api_secret_key}, timeout=5)
        if resp.status_code == 200:
            return {"status": "online", "details": resp.json()}
        return {"status": "error", "code": resp.status_code, "text": resp.text[:200]}
    except Exception as e:
        return {"status": "offline", "error": str(e)}

@app.post("/api/diagnostics/session-test")
def test_session_auth(domain_url: str, username: str = "admin", password: str = "", login_path: str = "/wp-login.php"):
    nonce = bridge_client.login_and_get_nonce(domain_url, username, password, login_path)
    if nonce:
        return {"success": True, "nonce": nonce, "message": f"Successfully authenticated via {login_path}"}
    return {"success": False, "error": "Login failed or nonce could not be extracted"}
