import os
import re
import uuid
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
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
    title="GEO SEO Engine",
    description="Autonomous Programmatic Local SEO & Generative Engine Optimization Engine",
    version="2.1.0"
)

templates = Jinja2Templates(directory="web/templates")
if os.path.exists("web/static"):
    app.mount("/static", StaticFiles(directory="web/static"), name="static")

if os.path.exists("output"):
    app.mount("/output", StaticFiles(directory="output"), name="output")

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
    login_path: Optional[str] = "/wp-login.php"

class PublishPreviewRequest(BaseModel):
    brand_id: str
    service_id: str
    location_region: str
    city_name: Optional[str] = None
    title: str
    slug: str
    primary_keyword: str
    meta_description: str
    content_html: str
    tags: List[str]
    featured_image_base64: Optional[str] = None
    featured_image_filename: Optional[str] = None
    status: str = "publish"

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
    api_secret_key: Optional[str] = "unicam-geo-secret-key-2026"
    hq_location: str = "Yogyakarta, Indonesia"
    default_language: str = "id"
    revision_guarantee: str = "Free 2x revision guarantee"
    master_output_spec: str = "Uncompressed 4K master files"
    service_name: Optional[str] = None
    target_region: Optional[str] = None
    cities: Optional[List[str]] = None

class VerifyUrlRequest(BaseModel):
    domain_url: str
    secret_key: Optional[str] = "unicam-geo-secret-key-2026"

# Routes
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

@app.get("/api/download-plugin")
def download_plugin():
    """Provides direct 1-click download of the WordPress Bridge plugin ZIP."""
    zip_path = "wordpress-plugin/unicam-seo-bridge.zip"
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Plugin zip file not found on server")
    return FileResponse(
        path=zip_path,
        filename="unicam-seo-bridge.zip",
        media_type="application/zip"
    )

@app.get("/api/brands")
def list_brands(db: Session = Depends(get_db)):
    brands = db.query(Brand).all()
    return {"brands": [b.to_dict() for b in brands]}

@app.post("/api/brands/verify-url")
def verify_wordpress_url(req: VerifyUrlRequest):
    """Pings WordPress site before adding to verify bridge plugin installation & key."""
    clean_url = req.domain_url.strip().rstrip('/')
    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        clean_url = f"https://{clean_url}"

    health_url = f"{clean_url}/wp-json/seo-engine/v1/health"
    secret = req.secret_key.strip() if req.secret_key else "unicam-geo-secret-key-2026"
    
    try:
        resp = requests.get(
            health_url,
            headers={"X-SEO-Engine-Key": secret, "User-Agent": "GEO-SEO-Engine/2.1"},
            timeout=7
        )
        if resp.status_code == 200:
            return {"success": True, "status": "online", "details": resp.json()}
        elif resp.status_code == 403:
            return {
                "success": False,
                "status": "forbidden",
                "error": "HTTP 403 Forbidden: Secret Key tidak cocok dengan pengaturan di plugin WordPress."
            }
        elif resp.status_code == 404:
            return {
                "success": False,
                "status": "not_found",
                "error": "HTTP 404 Not Found: Plugin Unicam SEO Bridge belum aktif di situs ini. Pasang unicam-seo-bridge.zip terlebih dahulu."
            }
        else:
            return {
                "success": False,
                "status": "error",
                "error": f"HTTP {resp.status_code}: {resp.text[:150]}"
            }
    except Exception as e:
        return {
            "success": False,
            "status": "unreachable",
            "error": f"Tidak dapat menghubungi situs: {str(e)}"
        }

@app.post("/api/brands")
def create_brand(req: CreateBrandRequest, db: Session = Depends(get_db)):
    """Allows user to setup brands one by one with customizable Secret Key."""
    brand_id = re.sub(r'[^a-z0-9]+', '', req.name.lower())[:20]
    if not brand_id:
        raise HTTPException(status_code=400, detail="Invalid brand name")
    
    existing = db.query(Brand).filter(Brand.id == brand_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Brand dengan ID '{brand_id}' sudah ada.")

    clean_domain = req.domain_url.strip().rstrip('/')
    if not clean_domain.startswith("http://") and not clean_domain.startswith("https://"):
        clean_domain = f"https://{clean_domain}"

    secret_key = req.api_secret_key.strip() if req.api_secret_key else "unicam-geo-secret-key-2026"

    brand = Brand(
        id=brand_id,
        name=req.name.strip(),
        slug=re.sub(r'[^a-z0-9]+', '-', req.name.lower()).strip('-'),
        platform="WORDPRESS",
        domain_url=clean_domain,
        wp_endpoint_url=f"{clean_domain}/wp-json/seo-engine/v1/publish",
        api_secret_key=secret_key,
        hq_location=req.hq_location.strip(),
        default_language=req.default_language,
        revision_guarantee=req.revision_guarantee,
        master_output_spec=req.master_output_spec,
        cta_tagline=f"🎥 Elevate your visual content with {req.name.strip()}."
    )
    db.add(brand)
    db.flush()

    # Initial service if provided
    if req.service_name:
        clean_srv = req.service_name.strip()
        srv_id = f"{brand_id}-{re.sub(r'[^a-z0-9]+', '-', clean_srv.lower())[:25].strip('-')}"
        srv = Service(
            id=srv_id,
            brand_id=brand_id,
            name=clean_srv,
            pillar_url=f"{clean_domain}/services/{re.sub(r'[^a-z0-9]+', '-', clean_srv.lower())}",
            anchor_variations=json.dumps([clean_srv, f"jasa {clean_srv.lower()}", f"vendor {clean_srv.lower()}"]),
            target_personas=json.dumps(["Marketing Directors", "Founders", "COOs"]),
            target_industries=json.dumps(["Commercial", "Enterprise", "Creative"]),
            base_tags=json.dumps([clean_srv.lower(), f"{req.name.lower()} studio", f"jasa {clean_srv.lower()}"])
        )
        db.add(srv)

    # Initial location if provided
    if req.target_region:
        clean_reg = req.target_region.strip()
        loc_id = f"{brand_id}-{re.sub(r'[^a-z0-9]+', '-', clean_reg.lower())}"
        city_list = req.cities or [clean_reg]
        loc = LocationTarget(
            id=loc_id,
            brand_id=brand_id,
            region_name=clean_reg,
            sub_cities=json.dumps(city_list),
            location_tags=json.dumps([f"{c} studio" for c in city_list])
        )
        db.add(loc)

    db.commit()
    return {"success": True, "brand": brand.to_dict()}

@app.delete("/api/brands/{brand_id}")
def delete_brand(brand_id: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Cascade delete
    db.query(Article).filter(Article.brand_id == brand_id).delete()
    db.query(LocationTarget).filter(LocationTarget.brand_id == brand_id).delete()
    db.query(Service).filter(Service.brand_id == brand_id).delete()
    db.delete(brand)
    db.commit()
    return {"success": True, "deleted": brand_id}

@app.post("/api/brands/{brand_id}/test-connection")
def test_brand_connection(brand_id: str, db: Session = Depends(get_db)):
    """Tests live connection to a brand's WordPress bridge endpoint."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    endpoint = brand.wp_endpoint_url
    if not endpoint:
        return {"success": False, "status": "unconfigured", "error": "Endpoint WordPress belum disetel."}
    
    health_url = endpoint.replace("/publish", "/health")
    try:
        resp = requests.get(
            health_url,
            headers={"X-SEO-Engine-Key": brand.api_secret_key, "User-Agent": "GEO-SEO-Engine/2.1"},
            timeout=6
        )
        if resp.status_code == 200:
            return {"success": True, "status": "online", "details": resp.json()}
        elif resp.status_code == 403:
            return {
                "success": False,
                "status": "forbidden",
                "error": "HTTP 403: Secret Key tidak cocok dengan pengaturan di plugin WordPress."
            }
        elif resp.status_code == 404:
            return {
                "success": False,
                "status": "not_found",
                "error": "HTTP 404: Endpoint plugin tidak ditemukan. Pastikan unicam-seo-bridge.zip sudah aktif di WordPress."
            }
        return {"success": False, "status": "error", "error": f"HTTP {resp.status_code}: {resp.text[:150]}"}
    except Exception as e:
        return {"success": False, "status": "offline", "error": str(e)}

# Gemini Multi-Account Endpoints
@app.get("/api/gemini/accounts")
def get_gemini_accounts():
    return geo_writer.gemini.get_accounts_summary()

@app.post("/api/gemini/add-account")
def add_gemini_account(req: GeminiAccountRequest):
    res = geo_writer.gemini.add_account(
        email=req.email or "",
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
    """Clears all brands, services, locations, articles for a completely fresh start."""
    db.query(Article).delete()
    db.query(LocationTarget).delete()
    db.query(Service).delete()
    db.query(Brand).delete()
    db.commit()
    return {"success": True, "message": "Database berhasil direset menjadi 0 brand."}

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
            "login_path": req.login_path or "/wp-login.php"
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

@app.post("/api/publish-preview")
def publish_preview(req: PublishPreviewRequest, db: Session = Depends(get_db)):
    """Publishes the exact previewed article directly to WordPress with 16:9 featured image and 50 tags."""
    brand = db.query(Brand).filter(Brand.id == req.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand '{req.brand_id}' not found.")

    publish_result = bridge_client.publish_article(
        brand_data=brand.to_dict(),
        article_payload={
            "title": req.title,
            "content_html": req.content_html,
            "slug": req.slug,
            "status": req.status,
            "meta_description": req.meta_description,
            "primary_keyword": req.primary_keyword,
            "tags": req.tags,
            "featured_image_base64": req.featured_image_base64,
            "featured_image_filename": req.featured_image_filename or f"thumb-{req.slug[:35]}.jpg"
        }
    )

    if not publish_result.get("success"):
        return {
            "success": False,
            "error": publish_result.get("error", "WordPress site rejected the publishing request."),
            "details": publish_result
        }

    article_id = f"art-{uuid.uuid4().hex[:10]}"
    article_record = Article(
        id=article_id,
        brand_id=req.brand_id,
        service_id=req.service_id,
        primary_keyword=req.primary_keyword,
        target_location=req.city_name or req.location_region,
        title=req.title,
        slug=req.slug,
        structured_content=json.dumps({"blocks": 12}),
        content_html=req.content_html,
        faq_data=json.dumps([]),
        meta_description=req.meta_description,
        tags=json.dumps(req.tags),
        published_url=publish_result.get("url"),
        wp_post_id=publish_result.get("post_id"),
        status="PUBLISHED"
    )
    db.add(article_record)
    db.commit()

    return {
        "success": True,
        "article_id": article_id,
        "title": req.title,
        "url": article_record.published_url,
        "status": "PUBLISHED",
        "wp_post_id": article_record.wp_post_id,
        "tags_count": len(req.tags),
        "featured_image_url": publish_result.get("featured_image_url")
    }

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
            raise HTTPException(status_code=400, detail="Harus menyertakan sheet_url atau csv_content.")

        result = importer.import_from_csv_text(csv_text, db)
        return {
            "success": True,
            "rows_processed": result.get("rows_processed", 0),
            "brands_synced": result.get("brands_synced", 0),
            "services_synced": result.get("services_synced", 0),
            "locations_synced": result.get("locations_synced", 0),
            "brand_ids": result.get("brand_ids", []),
            "imported": result
        }
    except Exception as e:
        logger.error(f"Sheet import error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/articles")
def list_articles(db: Session = Depends(get_db)):
    articles = db.query(Article).order_by(Article.created_at.desc()).limit(100).all()
    return {"articles": [a.to_dict() for a in articles]}

@app.delete("/api/articles/{article_id}")
def delete_article(article_id: str, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    db.commit()
    return {"success": True, "deleted": article_id}

@app.get("/api/download-template")
def download_template():
    """Provides direct 1-click download of the CSV spreadsheet matrix template."""
    csv_path = "data/matrix_template.csv"
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Template CSV not found on server")
    return FileResponse(
        path=csv_path,
        filename="matrix_template.csv",
        media_type="text/csv"
    )

@app.get("/api/diagnostics/system")
def system_diagnostics(db: Session = Depends(get_db)):
    brands_count = db.query(Brand).count()
    articles_count = db.query(Article).count()
    services_count = db.query(Service).count()
    gemini_summary = geo_writer.gemini.get_accounts_summary()
    
    return {
        "status": "operational",
        "brands_loaded": brands_count,
        "services_configured": services_count,
        "articles_registered": articles_count,
        "gemini_accounts": gemini_summary.get("accounts_count", 0),
        "gemini_active": gemini_summary.get("active_accounts", 0),
        "openrouter_connected": True,
        "default_model": "gemini-2.0-flash",
        "port": int(os.getenv("PORT", "28420"))
    }
