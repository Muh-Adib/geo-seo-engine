import re
import csv
import io
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from db.models import Brand, Service, LocationTarget

logger = logging.getLogger("sheet_importer")

class SpreadsheetImporter:
    """
    Imports and synchronizes Bank Data from Google Sheets or CSV files into the SQLite database.
    Supports:
    - Direct Google Sheets Public/Viewer URL (auto-converted to CSV export)
    - Local CSV files or raw CSV string streams
    """

    @staticmethod
    def normalize_google_sheet_url(url: str) -> str:
        """
        Converts standard Google Sheets editing URLs into direct CSV export URLs.
        Example input: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit?gid=12345#gid=12345
        Example output: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/export?format=csv&gid=12345
        """
        sheet_id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        if not sheet_id_match:
            return url

        sheet_id = sheet_id_match.group(1)
        gid_match = re.search(r'[?&#]gid=([0-9]+)', url)
        gid = gid_match.group(1) if gid_match else "0"

        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    def fetch_google_sheet_csv(self, url: str, timeout: int = 15) -> str:
        """Downloads raw CSV content from a Google Sheet export URL."""
        export_url = self.normalize_google_sheet_url(url)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
        }
        resp = requests.get(export_url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            raise ValueError(f"Failed to fetch Google Sheet (HTTP {resp.status_code}). Ensure sheet sharing is set to 'Anyone with the link can view'.")
        return resp.text

    def parse_and_sync(self, csv_content: str, db: Session) -> Dict[str, Any]:
        """
        Parses CSV string and syncs brands, services, and locations into SQLite database.
        """
        f = io.StringIO(csv_content.strip())
        reader = csv.DictReader(f)
        
        # Normalize column header keys (strip whitespace, lowercase)
        normalized_headers = {orig: orig.strip().lower() for orig in reader.fieldnames or []}

        rows_processed = 0
        brands_synced = set()
        services_synced = set()
        locations_synced = set()

        for raw_row in reader:
            row = {normalized_headers.get(k, k): (v or "").strip() for k, v in raw_row.items()}
            
            brand_id = row.get("brand_id") or row.get("brand") or "unimasi"
            brand_name = row.get("brand_name") or brand_id.upper()
            domain_url = row.get("domain_url") or f"https://{brand_id}.com"
            hq_loc = row.get("hq_location") or "Yogyakarta, Indonesia"
            lang = row.get("default_language") or ("id" if "indonesia" in hq_loc.lower() else "en")

            # 1. Upsert Brand
            brand = db.query(Brand).filter(Brand.id == brand_id).first()
            if not brand:
                brand = Brand(
                    id=brand_id,
                    name=brand_name,
                    slug=re.sub(r'[^a-z0-9]+', '-', brand_name.lower()).strip('-'),
                    platform="WORDPRESS",
                    domain_url=domain_url,
                    wp_endpoint_url=f"{domain_url.rstrip('/')}/wp-json/seo-engine/v1/publish",
                    hq_location=hq_loc,
                    default_language=lang,
                    revision_guarantee="Free 2x revision guarantee",
                    master_output_spec="Uncompressed 4K master files",
                    cta_tagline=f"🎥 Elevate your visual content with {brand_name}."
                )
                db.add(brand)
                db.flush()
            brands_synced.add(brand_id)

            # 2. Upsert Service
            service_name = row.get("service_name")
            if service_name:
                service_id = row.get("service_id") or f"{brand_id}-{re.sub(r'[^a-z0-9]+', '-', service_name.lower())[:25].strip('-')}"
                pillar_url = row.get("pillar_url") or f"{domain_url.rstrip('/')}/services/{re.sub(r'[^a-z0-9]+', '-', service_name.lower())}"
                
                # Parse array fields
                anchors = [a.strip() for a in row.get("anchor_variations", "").split(",") if a.strip()] or [service_name]
                personas = [p.strip() for p in row.get("target_personas", "").split(",") if p.strip()]
                industries = [i.strip() for i in row.get("target_industries", "").split(",") if i.strip()]
                custom_tags = [t.strip() for t in row.get("custom_tags", "").split(",") if t.strip()]

                service = db.query(Service).filter(Service.id == service_id).first()
                if not service:
                    service = Service(
                        id=service_id,
                        brand_id=brand_id,
                        name=service_name,
                        pillar_url=pillar_url,
                        anchor_variations=json.dumps(anchors),
                        target_personas=json.dumps(personas),
                        target_industries=json.dumps(industries),
                        base_tags=json.dumps(custom_tags or anchors),
                        estimated_timeline="2 to 5 weeks"
                    )
                    db.add(service)
                else:
                    service.name = service_name
                    service.pillar_url = pillar_url
                    if anchors:
                        service.anchor_variations = json.dumps(anchors)
                    if custom_tags:
                        service.base_tags = json.dumps(custom_tags)
                db.flush()
                services_synced.add(service_id)

            # 3. Upsert Location Target
            target_region = row.get("target_region")
            if target_region:
                loc_id = f"{brand_id}-{re.sub(r'[^a-z0-9]+', '-', target_region.lower())}"
                cities = [c.strip() for c in row.get("cities", "").split(",") if c.strip()]
                
                loc = db.query(LocationTarget).filter(LocationTarget.id == loc_id).first()
                if not loc:
                    loc = LocationTarget(
                        id=loc_id,
                        brand_id=brand_id,
                        region_name=target_region,
                        sub_cities=json.dumps(cities or [target_region]),
                        location_tags=json.dumps([f"{c} studio" for c in cities] if cities else [])
                    )
                    db.add(loc)
                else:
                    if cities:
                        loc.sub_cities = json.dumps(cities)
                db.flush()
                locations_synced.add(loc_id)

            rows_processed += 1

        db.commit()

        return {
            "success": True,
            "rows_processed": rows_processed,
            "brands_synced": len(brands_synced),
            "services_synced": len(services_synced),
            "locations_synced": len(locations_synced),
            "brand_ids": list(brands_synced)
        }
