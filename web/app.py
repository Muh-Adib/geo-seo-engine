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
from db.models import Brand, Service, LocationTarget, Article, KeywordBankItem
from generators.geo_writer import ProgrammaticGEOWriter
from generators.link_injector import LinkInjector
from core.bridge_client import WordPressBridgeClient
from core.router_client import LLMRouterClient
from core.gsc_client import GSCClient
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
router_client = geo_writer.router
gsc_client = GSCClient()

# Request Models
class RouterSettingsRequest(BaseModel):
    base_url: str
    api_key: Optional[str] = ""
    selected_model: str
    temperature: Optional[float] = 0.7

class GenerateCustomImageRequest(BaseModel):
    prompt: str
    brand_name: Optional[str] = "GEO Studio"
    location: Optional[str] = "Indonesia"
    aspect_ratio: Optional[str] = "16:9"
    style: Optional[str] = "photorealistic"

class TestCompletionRequest(BaseModel):
    prompt: str
    model: Optional[str] = None

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

class BrandSettingsRequest(BaseModel):
    name: Optional[str] = None
    domain_url: Optional[str] = None
    api_secret_key: Optional[str] = None
    logo_url: Optional[str] = None
    tagline: Optional[str] = None
    industry_focus: Optional[str] = None
    contact_whatsapp: Optional[str] = None
    contact_email: Optional[str] = None
    consultation_url: Optional[str] = None
    gsc_site_url: Optional[str] = None
    gsc_service_account_json: Optional[str] = None
    core_pain_points: Optional[List[str]] = None
    core_solutions: Optional[List[str]] = None
    hq_location: Optional[str] = None
    default_language: Optional[str] = None
    revision_guarantee: Optional[str] = None
    master_output_spec: Optional[str] = None
    cta_tagline: Optional[str] = None

class KeywordBankCreateRequest(BaseModel):
    category: str # "action", "subject", "predicate", "city"
    value: str
    brand_id: Optional[str] = None

class KeywordMatrixGenerateRequest(BaseModel):
    brand_id: Optional[str] = None
    actions: Optional[List[str]] = None
    subjects: Optional[List[str]] = None
    predicates: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    limit: Optional[int] = 50

DEFAULT_KEYWORD_BANK = [
    # Actions (Intent)
    {"category": "action", "value": "Jasa Pembuatan"},
    {"category": "action", "value": "Software House"},
    {"category": "action", "value": "Vendor Profesional"},
    {"category": "action", "value": "Konsultan IT"},
    {"category": "action", "value": "Jasa Rekayasa"},
    {"category": "action", "value": "Partner Digital"},
    # Subjects (Service/Product)
    {"category": "subject", "value": "Website Enterprise"},
    {"category": "subject", "value": "Aplikasi Web Kustom"},
    {"category": "subject", "value": "Sistem ERP & CRM"},
    {"category": "subject", "value": "Portal Berita & Media"},
    {"category": "subject", "value": "Aplikasi Mobile iOS & Android"},
    {"category": "subject", "value": "Landing Page Konversi Tinggi"},
    # Predicates (Problem Solving / Value Proposition)
    {"category": "predicate", "value": "Arsitektur Headless Cloud-Ready"},
    {"category": "predicate", "value": "Performa Kecepatan Sub-Detik"},
    {"category": "predicate", "value": "Keamanan Data Standar OWASP"},
    {"category": "predicate", "value": "Otomasi Proses Bisnis Terpadu"},
    {"category": "predicate", "value": "Garansi Bebas Bug & SLA 24/7"},
    {"category": "predicate", "value": "Desain UI/UX Modern & Responsif"},
    # Cities (Target Location)
    {"category": "city", "value": "Jakarta"},
    {"category": "city", "value": "Surabaya"},
    {"category": "city", "value": "Bandung"},
    {"category": "city", "value": "Semarang"},
    {"category": "city", "value": "Yogyakarta"},
    {"category": "city", "value": "Medan"},
    {"category": "city", "value": "Denpasar"},
    {"category": "city", "value": "Makassar"},
    {"category": "city", "value": "Tangerang"},
    {"category": "city", "value": "Bekasi"}
]

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

# Extended Brand Settings & Integrations
@app.get("/api/brands/{brand_id}/settings")
def get_brand_settings(brand_id: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand tidak ditemukan.")
    data = brand.to_dict()
    data["gsc_service_account_json"] = brand.gsc_service_account_json or ""
    return {"success": True, "settings": data}

@app.put("/api/brands/{brand_id}/settings")
def update_brand_settings(brand_id: str, req: BrandSettingsRequest, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand tidak ditemukan.")
    
    if req.name is not None and req.name.strip():
        brand.name = req.name.strip()
    if req.domain_url is not None:
        clean_domain = req.domain_url.strip().rstrip('/')
        if clean_domain and not clean_domain.startswith("http://") and not clean_domain.startswith("https://"):
            clean_domain = f"https://{clean_domain}"
        brand.domain_url = clean_domain
        brand.wp_endpoint_url = f"{clean_domain}/wp-json/seo-engine/v1/publish"
    if req.api_secret_key is not None:
        brand.api_secret_key = req.api_secret_key.strip()
    if req.logo_url is not None:
        brand.logo_url = req.logo_url.strip()
    if req.tagline is not None:
        brand.tagline = req.tagline.strip()
    if req.industry_focus is not None:
        brand.industry_focus = req.industry_focus.strip()
    if req.contact_whatsapp is not None:
        brand.contact_whatsapp = req.contact_whatsapp.strip()
    if req.contact_email is not None:
        brand.contact_email = req.contact_email.strip()
    if req.consultation_url is not None:
        brand.consultation_url = req.consultation_url.strip()
    if req.gsc_site_url is not None:
        brand.gsc_site_url = req.gsc_site_url.strip()
    if req.gsc_service_account_json is not None:
        brand.gsc_service_account_json = req.gsc_service_account_json.strip()
    if req.core_pain_points is not None:
        brand.core_pain_points = json.dumps(req.core_pain_points)
    if req.core_solutions is not None:
        brand.core_solutions = json.dumps(req.core_solutions)
    if req.hq_location is not None:
        brand.hq_location = req.hq_location.strip()
    if req.default_language is not None:
        brand.default_language = req.default_language.strip()
    if req.revision_guarantee is not None:
        brand.revision_guarantee = req.revision_guarantee.strip()
    if req.master_output_spec is not None:
        brand.master_output_spec = req.master_output_spec.strip()
    if req.cta_tagline is not None:
        brand.cta_tagline = req.cta_tagline.strip()

    db.commit()
    return {"success": True, "brand": brand.to_dict()}

@app.post("/api/brands/{brand_id}/sync-wp-articles")
def sync_wordpress_articles(brand_id: str, db: Session = Depends(get_db)):
    """Pulls live articles directly from WordPress REST API into the database."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand tidak ditemukan.")
    
    sync_res = bridge_client.sync_live_articles(brand.to_dict(), limit=100)
    if not sync_res.get("success"):
        return sync_res
    
    articles_data = sync_res.get("articles", [])
    synced_count = 0
    updated_count = 0
    
    for art in articles_data:
        wp_id = art.get("wp_post_id")
        pub_url = art.get("published_url")
        title = art.get("title", "")
        slug = art.get("slug", "")
        
        existing = None
        if wp_id:
            existing = db.query(Article).filter(Article.wp_post_id == wp_id, Article.brand_id == brand_id).first()
        if not existing and pub_url:
            existing = db.query(Article).filter(Article.published_url == pub_url, Article.brand_id == brand_id).first()
        
        if existing:
            existing.title = title or existing.title
            existing.status = art.get("status", "PUBLISHED")
            existing.published_url = pub_url or existing.published_url
            updated_count += 1
        else:
            srv = db.query(Service).filter(Service.brand_id == brand_id).first()
            srv_id = srv.id if srv else f"{brand_id}-general"
            new_id = f"art-{uuid.uuid4().hex[:12]}"
            new_article = Article(
                id=new_id,
                brand_id=brand_id,
                service_id=srv_id,
                primary_keyword=title[:100] if title else "Live Article",
                target_location=brand.hq_location or "Indonesia",
                title=title or "Live WordPress Article",
                slug=slug or (re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') if title else f"wp-{wp_id}"),
                meta_description=f"Artikel resmi dari {brand.name}: {title}",
                content_html="<p>Artikel telah disinkronkan langsung dari situs WordPress live.</p>",
                published_url=pub_url,
                wp_post_id=wp_id,
                status=art.get("status", "PUBLISHED")
            )
            db.add(new_article)
            synced_count += 1
            
    db.commit()
    return {
        "success": True,
        "source": sync_res.get("source"),
        "total_from_wp": len(articles_data),
        "synced_new": synced_count,
        "updated_existing": updated_count,
        "articles": [a.to_dict() for a in db.query(Article).filter(Article.brand_id == brand_id).order_by(Article.created_at.desc()).limit(100).all()]
    }

@app.get("/api/brands/{brand_id}/gsc-performance")
def get_brand_gsc_performance(brand_id: str, days: int = 28, db: Session = Depends(get_db)):
    """Fetches real search performance from Google Search Console via Service Account."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand tidak ditemukan.")
    
    site_url = brand.gsc_site_url or brand.domain_url
    if not site_url:
        return {
            "success": False,
            "configured": False,
            "error": "URL Situs / Property GSC belum diatur di Pengaturan Brand.",
            "overview": {"totalClicks": 0, "totalImpressions": 0, "averageCtr": "0.0%", "averagePosition": 0.0},
            "queries": [],
            "pages": []
        }
    
    cred_json = brand.gsc_service_account_json
    return gsc_client.get_search_analytics(site_url=site_url, days=days, credentials_json=cred_json)

@app.post("/api/brands/{brand_id}/gsc-test")
def test_brand_gsc_connection(brand_id: str, db: Session = Depends(get_db)):
    """Tests authentication & permission of the Service Account on GSC."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand tidak ditemukan.")
    
    site_url = brand.gsc_site_url or brand.domain_url
    cred_json = brand.gsc_service_account_json
    return gsc_client.test_connection(site_url=site_url, credentials_json=cred_json)

# Marketing Keyword Bank Routes
@app.get("/api/keywords/bank")
def get_keyword_bank(brand_id: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    """Lists keyword bank items grouped into Action, Subject, Predicate, City."""
    query = db.query(KeywordBankItem)
    if brand_id:
        query = query.filter((KeywordBankItem.brand_id == brand_id) | (KeywordBankItem.brand_id == None))
    if category:
        query = query.filter(KeywordBankItem.category == category.lower())
    
    items = query.order_by(KeywordBankItem.created_at.asc()).all()
    
    # Auto-seed if database keyword bank is empty
    if not items and db.query(KeywordBankItem).count() == 0:
        for d in DEFAULT_KEYWORD_BANK:
            item = KeywordBankItem(
                id=f"kb-{uuid.uuid4().hex[:10]}",
                brand_id=None,
                category=d["category"],
                value=d["value"],
                is_active=True
            )
            db.add(item)
        db.commit()
        items = db.query(KeywordBankItem).order_by(KeywordBankItem.created_at.asc()).all()

    grouped = {"action": [], "subject": [], "predicate": [], "city": []}
    for it in items:
        cat = it.category.lower()
        if cat in grouped:
            grouped[cat].append(it.to_dict())
        else:
            grouped.setdefault(cat, []).append(it.to_dict())

    return {
        "success": True,
        "total": len(items),
        "items": [it.to_dict() for it in items],
        "grouped": grouped
    }

@app.post("/api/keywords/bank")
def create_keyword_bank_item(req: KeywordBankCreateRequest, db: Session = Depends(get_db)):
    """Adds a new keyword to the bank."""
    cat = req.category.strip().lower()
    val = req.value.strip()
    if not val:
        raise HTTPException(status_code=400, detail="Nilai kata kunci tidak boleh kosong.")
    
    existing = db.query(KeywordBankItem).filter(
        KeywordBankItem.category == cat,
        KeywordBankItem.value == val,
        KeywordBankItem.brand_id == req.brand_id
    ).first()
    if existing:
        return {"success": True, "item": existing.to_dict(), "message": "Kata kunci sudah terdaftar di bank."}

    new_id = f"kb-{uuid.uuid4().hex[:10]}"
    item = KeywordBankItem(
        id=new_id,
        brand_id=req.brand_id,
        category=cat,
        value=val,
        is_active=True
    )
    db.add(item)
    db.commit()
    return {"success": True, "item": item.to_dict()}

@app.delete("/api/keywords/bank/{item_id}")
def delete_keyword_bank_item(item_id: str, db: Session = Depends(get_db)):
    """Removes a keyword from the bank."""
    item = db.query(KeywordBankItem).filter(KeywordBankItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan.")
    db.delete(item)
    db.commit()
    return {"success": True, "deleted": item_id}

@app.post("/api/keywords/generate-matrix")
def generate_keyword_matrix(req: KeywordMatrixGenerateRequest, db: Session = Depends(get_db)):
    """Combines Action + Subject + Predicate + City into high-conversion programmatic keywords."""
    actions = req.actions or []
    subjects = req.subjects or []
    predicates = req.predicates or []
    cities = req.cities or []

    if not actions:
        actions = [i.value for i in db.query(KeywordBankItem).filter(KeywordBankItem.category == "action", KeywordBankItem.is_active == True).all()]
    if not subjects:
        subjects = [i.value for i in db.query(KeywordBankItem).filter(KeywordBankItem.category == "subject", KeywordBankItem.is_active == True).all()]
    if not predicates:
        predicates = [i.value for i in db.query(KeywordBankItem).filter(KeywordBankItem.category == "predicate", KeywordBankItem.is_active == True).all()]
    if not cities:
        cities = [i.value for i in db.query(KeywordBankItem).filter(KeywordBankItem.category == "city", KeywordBankItem.is_active == True).all()]

    if not actions: actions = ["Jasa Pembuatan", "Software House", "Konsultan IT"]
    if not subjects: subjects = ["Website Enterprise", "Aplikasi Web Kustom", "Sistem ERP"]
    if not predicates: predicates = ["Arsitektur Headless Cloud-Ready", "Performa Kecepatan Sub-Detik", "Garansi Bebas Bug"]
    if not cities: cities = ["Jakarta", "Surabaya", "Bandung", "Yogyakarta"]

    combinations = []
    limit = req.limit or 50

    for city in cities:
        for subj in subjects:
            for act in actions:
                for pred in predicates:
                    primary_kw = f"{act} {subj} {city}"
                    title = f"{act} {subj} di {city} - {pred}"
                    meta_preview = f"Mencari {act.lower()} {subj.lower()} profesional di {city}? Kami hadirkan solusi terpercaya dengan {pred.lower()} dan garansi purna-jual."
                    
                    combinations.append({
                        "id": f"matrix-{uuid.uuid4().hex[:8]}",
                        "action": act,
                        "subject": subj,
                        "predicate": pred,
                        "city": city,
                        "primary_keyword": primary_kw,
                        "suggested_title": title,
                        "meta_preview": meta_preview,
                        "intent": "Commercial / High-Intent Problem Solving",
                        "problem_addressed": f"Tantangan performa dan skalabilitas {subj.lower()} di {city}",
                        "solution_offered": pred
                    })
                    if len(combinations) >= limit:
                        break
                if len(combinations) >= limit:
                    break
            if len(combinations) >= limit:
                break
        if len(combinations) >= limit:
            break

    return {
        "success": True,
        "total_generated": len(combinations),
        "dimensions": {
            "actions_count": len(actions),
            "subjects_count": len(subjects),
            "predicates_count": len(predicates),
            "cities_count": len(cities)
        },
        "matrix": combinations
    }

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

# Router & Model Dynamic Discovery Endpoints (9router / OpenAI-compatible)
@app.get("/api/router/status")
def get_router_status():
    """Returns router connection health and current configuration."""
    health = router_client.check_health()
    return {
        "success": True,
        "health": health,
        "config": {
            "base_url": router_client.config.get("base_url"),
            "api_key_masked": f"{router_client.config.get('api_key', '')[:8]}..." if router_client.config.get("api_key") else "(none)",
            "selected_model": router_client.config.get("selected_model"),
            "temperature": router_client.config.get("temperature", 0.7)
        }
    }

@app.get("/api/router/models")
@app.post("/api/router/fetch-models")
def fetch_router_models():
    """Dynamically fetches real live models from the router (never fictitious/hardcoded)."""
    result = router_client.fetch_models()
    return result

@app.post("/api/router/settings")
def update_router_settings(req: RouterSettingsRequest):
    """Updates router connection and active model selection."""
    result = router_client.update_settings(
        base_url=req.base_url,
        api_key=req.api_key or "",
        selected_model=req.selected_model,
        temperature=req.temperature or 0.7
    )
    # Sync to geo_writer
    geo_writer.model = req.selected_model
    return result

@app.post("/api/router/test-completion")
def test_router_completion(req: TestCompletionRequest):
    """Sends a quick test message through the router to verify model responsiveness."""
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt tidak boleh kosong.")
    
    target_model = req.model or router_client.config.get("selected_model", "ox-alpha")
    messages = [
        {"role": "system", "content": "You are a concise AI assistant. Respond in 1-2 helpful sentences."},
        {"role": "user", "content": req.prompt.strip()}
    ]
    resp = router_client.generate_chat_completion(messages=messages, model=target_model)
    if not resp:
        return {
            "success": False,
            "error": f"Model '{target_model}' tidak memberikan respons. Pastikan router aktif.",
            "model_used": target_model
        }
    return {
        "success": True,
        "response": resp,
        "model_used": target_model
    }

# Studio Generator Gambar Endpoints
@app.post("/api/images/generate")
def generate_custom_image(req: GenerateCustomImageRequest):
    """Generates custom graphic/thumbnail with specified aspect ratio (16:9, 1:1, 9:16) and style."""
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt tidak boleh kosong.")
    
    result = geo_writer.gemini.generate_custom_image(
        prompt=req.prompt.strip(),
        brand_name=req.brand_name or "GEO Studio",
        location=req.location or "Indonesia",
        aspect_ratio=req.aspect_ratio or "16:9",
        style=req.style or "photorealistic"
    )
    return result

@app.get("/api/images/gallery")
def get_image_gallery():
    """Returns list of generated images in the studio gallery."""
    images = geo_writer.gemini.list_gallery_images()
    return {"images": images}

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
    router_health = router_client.check_health()
    
    return {
        "status": "operational",
        "brands_loaded": brands_count,
        "services_configured": services_count,
        "articles_registered": articles_count,
        "gemini_accounts": gemini_summary.get("accounts_count", 0),
        "gemini_active": gemini_summary.get("active_accounts", 0),
        "router_connected": router_health.get("online", False),
        "router_models_count": router_health.get("models_count", 0),
        "active_model": router_client.config.get("selected_model", "ox-alpha"),
        "port": int(os.getenv("PORT", "28420"))
    }
