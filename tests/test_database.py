import pytest
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import Brand, Service, LocationTarget, Article

def test_ten_brands_exist():
    db: Session = SessionLocal()
    try:
        brands = db.query(Brand).all()
        assert len(brands) >= 10, f"Expected at least 10 brands, found {len(brands)}"
        brand_ids = [b.id for b in brands]
        expected_ids = [
            "unimasi", "unicam", "segiatech", "archivis", "safetymotion",
            "motioncraft", "lumenspace", "brandvibe", "cloudshift", "renderpulse"
        ]
        for eid in expected_ids:
            assert eid in brand_ids, f"Brand {eid} missing from database"
    finally:
        db.close()

def test_brand_services_and_locations():
    db: Session = SessionLocal()
    try:
        for brand in db.query(Brand).all():
            services = db.query(Service).filter(Service.brand_id == brand.id).all()
            assert len(services) >= 1, f"Brand {brand.id} must have at least 1 service"
            locations = db.query(LocationTarget).filter(LocationTarget.brand_id == brand.id).all()
            assert len(locations) >= 1, f"Brand {brand.id} must have at least 1 location target"
    finally:
        db.close()
