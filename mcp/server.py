import sys
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from db.session import get_db, SessionLocal
from db.models import Brand, Service, LocationTarget, Article
from generators.geo_writer import ProgrammaticGEOWriter
from generators.link_injector import LinkInjector
from core.bridge_client import WordPressBridgeClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mcp_server")

# Initialize shared components
geo_writer = ProgrammaticGEOWriter()
link_injector = LinkInjector()
bridge_client = WordPressBridgeClient()

def tool_list_all_brands() -> Dict[str, Any]:
    """Returns all 10 configured brands and their summary data."""
    db: Session = SessionLocal()
    try:
        brands = db.query(Brand).all()
        return {
            "success": True,
            "total_brands": len(brands),
            "brands": [b.to_dict() for b in brands]
        }
    finally:
        db.close()

def tool_get_brand_and_service_context(brand_id: str) -> Dict[str, Any]:
    """Fetches full brand, services, and location target context for a brand."""
    db: Session = SessionLocal()
    try:
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            return {"success": False, "error": f"Brand '{brand_id}' not found."}
        
        services = db.query(Service).filter(Service.brand_id == brand_id).all()
        locations = db.query(LocationTarget).filter(LocationTarget.brand_id == brand_id).all()
        
        return {
            "success": True,
            "brand": brand.to_dict(),
            "services": [s.to_dict() for s in services],
            "locations": [loc.to_dict() for loc in locations]
        }
    finally:
        db.close()

def tool_preview_seo_article(
    brand_id: str,
    service_id: str,
    location_region: str,
    city_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a full 12-block preview of a Programmatic Local SEO & GEO article.
    Adheres strictly to the 12 blocks, 10 FAQs, 50 tags, and no-email rules.
    """
    db: Session = SessionLocal()
    try:
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            return {"success": False, "error": f"Brand '{brand_id}' not found."}
        
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            return {"success": False, "error": f"Service '{service_id}' not found."}

        location = db.query(LocationTarget).filter(
            LocationTarget.brand_id == brand_id,
            LocationTarget.region_name.ilike(location_region)
        ).first()

        location_dict = location.to_dict() if location else {
            "region_name": location_region,
            "sub_cities": [city_name] if city_name else [location_region],
            "local_context_notes": "",
            "location_tags": []
        }

        # Query recent brand articles for linking
        recent_articles = db.query(Article).filter(Article.brand_id == brand_id).limit(6).all()
        related_articles = [a.to_dict() for a in recent_articles]

        # Generate base 12-block content
        generated = geo_writer.generate_programmatic_article(
            brand_data=brand.to_dict(),
            service_data=service.to_dict(),
            location_data=location_dict,
            specific_city=city_name
        )

        # Inject contextual internal links, official directory block, and JSON-LD schema
        full_html = link_injector.inject_all(
            html_content=generated["content_html"],
            brand_data=brand.to_dict(),
            service_data=service.to_dict(),
            target_location=city_name or location_region,
            faq_items=generated["faq_items"],
            related_articles=related_articles,
            include_schema=True
        )

        return {
            "success": True,
            "title": generated["title"],
            "slug": generated["slug"],
            "primary_keyword": generated["primary_keyword"],
            "target_location": generated["target_location"],
            "meta_description": generated["meta_description"],
            "tags": generated["tags"],
            "tags_count": len(generated["tags"]),
            "faq_items_count": len(generated["faq_items"]),
            "content_html": full_html,
            "faq_items": generated["faq_items"]
        }
    finally:
        db.close()

def tool_publish_to_site(
    brand_id: str,
    service_id: str,
    location_region: str,
    city_name: Optional[str] = None,
    status: str = "publish",
    login_credentials: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Generates and publishes a programmatic article directly to the brand's WordPress site,
    recording the entry into the local SQLite database.
    """
    # 1. Generate full article
    preview = tool_preview_seo_article(brand_id, service_id, location_region, city_name)
    if not preview.get("success"):
        return preview

    db: Session = SessionLocal()
    try:
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            return {"success": False, "error": f"Brand {brand_id} not found"}

        # 2. Dispatch to WordPress via Bridge or Session Auth
        publish_result = bridge_client.publish_article(
            brand_data=brand.to_dict(),
            article_payload={
                "title": preview["title"],
                "content_html": preview["content_html"],
                "slug": preview["slug"],
                "status": status,
                "meta_description": preview["meta_description"],
                "primary_keyword": preview["primary_keyword"],
                "tags": preview["tags"]
            },
            login_credentials=login_credentials
        )

        article_id = f"art-{uuid.uuid4().hex[:10]}"
        is_published = publish_result.get("success", False)
        
        # 3. Store record in database
        article_record = Article(
            id=article_id,
            brand_id=brand_id,
            service_id=service_id,
            primary_keyword=preview["primary_keyword"],
            target_location=preview["target_location"],
            title=preview["title"],
            slug=preview["slug"],
            structured_content=json.dumps({"blocks": 12}),
            content_html=preview["content_html"],
            faq_data=json.dumps(preview["faq_items"]),
            meta_description=preview["meta_description"],
            tags=json.dumps(preview["tags"]),
            published_url=publish_result.get("url") or f"{brand.domain_url.rstrip('/')}/{preview['slug']}/",
            wp_post_id=publish_result.get("post_id"),
            status="PUBLISHED" if is_published else "DRAFT"
        )
        db.add(article_record)
        db.commit()

        return {
            "success": True,
            "article_id": article_id,
            "title": preview["title"],
            "url": article_record.published_url,
            "status": article_record.status,
            "wp_post_id": article_record.wp_post_id,
            "tags_count": preview["tags_count"],
            "bridge_response": publish_result
        }
    finally:
        db.close()

def tool_generate_bulk_matrix(
    brand_id: str,
    service_id: str,
    location_region: str,
    cities: List[str],
    auto_publish: bool = False
) -> Dict[str, Any]:
    """
    Mass produces Programmatic Local SEO landing pages across multiple target cities.
    """
    results = []
    for city in cities:
        if auto_publish:
            res = tool_publish_to_site(
                brand_id=brand_id,
                service_id=service_id,
                location_region=location_region,
                city_name=city,
                status="publish"
            )
        else:
            # Preview and save as draft
            preview = tool_preview_seo_article(
                brand_id=brand_id,
                service_id=service_id,
                location_region=location_region,
                city_name=city
            )
            if preview.get("success"):
                db: Session = SessionLocal()
                try:
                    brand = db.query(Brand).filter(Brand.id == brand_id).first()
                    art_id = f"art-{uuid.uuid4().hex[:10]}"
                    article_record = Article(
                        id=art_id,
                        brand_id=brand_id,
                        service_id=service_id,
                        primary_keyword=preview["primary_keyword"],
                        target_location=preview["target_location"],
                        title=preview["title"],
                        slug=preview["slug"],
                        structured_content=json.dumps({"blocks": 12}),
                        content_html=preview["content_html"],
                        faq_data=json.dumps(preview["faq_items"]),
                        meta_description=preview["meta_description"],
                        tags=json.dumps(preview["tags"]),
                        published_url=f"{brand.domain_url.rstrip('/')}/{preview['slug']}/" if brand else None,
                        status="DRAFT"
                    )
                    db.add(article_record)
                    db.commit()
                    res = {
                        "success": True,
                        "article_id": art_id,
                        "title": preview["title"],
                        "city": city,
                        "status": "DRAFT"
                    }
                finally:
                    db.close()
            else:
                res = preview
        results.append(res)

    return {
        "success": True,
        "total_generated": len(results),
        "results": results
    }

def tool_import_sheet_data(sheet_url_or_content: str) -> Dict[str, Any]:
    """
    Imports and syncs brand, services, and location target bank data from a Google Sheet URL or raw CSV string.
    """
    from importers.sheet_importer import SpreadsheetImporter
    importer = SpreadsheetImporter()
    db: Session = SessionLocal()
    try:
        trimmed = sheet_url_or_content.strip()
        if trimmed.startswith("http://") or trimmed.startswith("https://"):
            csv_text = importer.fetch_google_sheet_csv(trimmed)
        else:
            csv_text = trimmed
        return importer.parse_and_sync(csv_text, db)
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        db.close()

def tool_get_article_registry(limit: int = 50) -> Dict[str, Any]:
    """Lists articles stored in the local SQLite engine registry."""
    db: Session = SessionLocal()
    try:
        articles = db.query(Article).order_by(Article.created_at.desc()).limit(limit).all()
        return {
            "success": True,
            "count": len(articles),
            "articles": [a.to_dict() for a in articles]
        }
    finally:
        db.close()

# MCP JSON-RPC Server Handler
TOOLS_SCHEMA = [
    {
        "name": "list_all_brands",
        "description": "Lists all 10 configured programmatic brands and their active status.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_brand_and_service_context",
        "description": "Returns full brand profile, available services, and location matrices.",
        "inputSchema": {
            "type": "object",
            "properties": {"brand_id": {"type": "string", "description": "e.g. unimasi, unicam, segiatech"}},
            "required": ["brand_id"]
        }
    },
    {
        "name": "preview_seo_article",
        "description": "Generates a 12-block preview of a Programmatic Local SEO & GEO landing page with 10 FAQs and 50 tags.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "brand_id": {"type": "string"},
                "service_id": {"type": "string"},
                "location_region": {"type": "string"},
                "city_name": {"type": "string"}
            },
            "required": ["brand_id", "service_id", "location_region"]
        }
    },
    {
        "name": "publish_to_site",
        "description": "Publishes a programmatic article to WordPress with 50 tags and GEO schema.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "brand_id": {"type": "string"},
                "service_id": {"type": "string"},
                "location_region": {"type": "string"},
                "city_name": {"type": "string"},
                "status": {"type": "string", "default": "publish"}
            },
            "required": ["brand_id", "service_id", "location_region"]
        }
    },
    {
        "name": "generate_bulk_matrix",
        "description": "Batch generates articles across multiple target cities for programmatic dominance.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "brand_id": {"type": "string"},
                "service_id": {"type": "string"},
                "location_region": {"type": "string"},
                "cities": {"type": "array", "items": {"type": "string"}},
                "auto_publish": {"type": "boolean", "default": False}
            },
            "required": ["brand_id", "service_id", "location_region", "cities"]
        }
    },
    {
        "name": "get_article_registry",
        "description": "Fetches recently generated articles from the local SQLite database.",
        "inputSchema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 50}}
        }
    },
    {
        "name": "import_sheet_data",
        "description": "Imports matrix bank data (brands, services, cities, keywords) from a Google Sheet URL or CSV content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sheet_url_or_content": {
                    "type": "string",
                    "description": "Google Sheet URL (e.g. https://docs.google.com/spreadsheets/d/.../edit) or raw CSV text."
                }
            },
            "required": ["sheet_url_or_content"]
        }
    }
]

def run_stdio_server():
    """Runs standard JSON-RPC 2.0 loop over stdin/stdout for MCP clients."""
    logger.info("Starting Unicam MCP Server (stdio mode)...")
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {"name": "unicam-programmatic-geo-mcp", "version": "1.0.0"},
                        "capabilities": {"tools": {}}
                    }
                }
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS_SCHEMA}
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                
                tool_map = {
                    "list_all_brands": lambda: tool_list_all_brands(),
                    "get_brand_and_service_context": lambda: tool_get_brand_and_service_context(args.get("brand_id")),
                    "preview_seo_article": lambda: tool_preview_seo_article(
                        args.get("brand_id"), args.get("service_id"), args.get("location_region"), args.get("city_name")
                    ),
                    "publish_to_site": lambda: tool_publish_to_site(
                        args.get("brand_id"), args.get("service_id"), args.get("location_region"), args.get("city_name"), args.get("status", "publish")
                    ),
                    "generate_bulk_matrix": lambda: tool_generate_bulk_matrix(
                        args.get("brand_id"), args.get("service_id"), args.get("location_region"), args.get("cities", []), args.get("auto_publish", False)
                    ),
                    "get_article_registry": lambda: tool_get_article_registry(args.get("limit", 50)),
                    "import_sheet_data": lambda: tool_import_sheet_data(args.get("sheet_url_or_content", ""))
                }

                if tool_name in tool_map:
                    result = tool_map[tool_name]()
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                        }
                    }
                else:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Method {tool_name} not found"}
                    }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unknown method {method}"}
                }

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    run_stdio_server()
