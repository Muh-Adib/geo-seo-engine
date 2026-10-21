import pytest
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import Brand, Service, LocationTarget, Article

def test_database_initial_and_crud_lifecycle():
    db: Session = SessionLocal()
    try:
        # Create test brand
        test_brand_id = "test-studio-dynamic"
        brand = Brand(
            id=test_brand_id,
            name="Test Studio Dynamic",
            slug="test-studio-dynamic",
            platform="WORDPRESS",
            domain_url="https://testdynamic.com",
            wp_endpoint_url="https://testdynamic.com/wp-json/seo-engine/v1/publish",
            api_secret_key="secret-key-dynamic",
            hq_location="Yogyakarta, Indonesia",
            default_language="id",
            revision_guarantee="2x free revision",
            master_output_spec="4K master files",
            cta_tagline="Test dynamic studio"
        )
        db.add(brand)
        db.flush()

        service = Service(
            id=f"{test_brand_id}-srv",
            brand_id=test_brand_id,
            name="Jasa Pembuatan Video",
            pillar_url="https://testdynamic.com/services/video",
            anchor_variations='["Jasa Pembuatan Video"]',
            target_personas='["Marketing"]',
            target_industries='["Agency"]',
            base_tags='["video"]'
        )
        db.add(service)

        location = LocationTarget(
            id=f"{test_brand_id}-loc",
            brand_id=test_brand_id,
            region_name="Indonesia",
            sub_cities='["Jakarta", "Surabaya"]',
            location_tags='["jakarta video"]'
        )
        db.add(location)
        db.commit()

        # Query & Verify
        fetched_brand = db.query(Brand).filter(Brand.id == test_brand_id).first()
        assert fetched_brand is not None
        assert fetched_brand.name == "Test Studio Dynamic"

        fetched_services = db.query(Service).filter(Service.brand_id == test_brand_id).all()
        assert len(fetched_services) == 1
        assert fetched_services[0].name == "Jasa Pembuatan Video"

        fetched_locs = db.query(LocationTarget).filter(LocationTarget.brand_id == test_brand_id).all()
        assert len(fetched_locs) == 1
        assert fetched_locs[0].region_name == "Indonesia"

        # Cleanup test record
        db.query(Service).filter(Service.brand_id == test_brand_id).delete()
        db.query(LocationTarget).filter(LocationTarget.brand_id == test_brand_id).delete()
        db.delete(fetched_brand)
        db.commit()

        # Confirm deleted
        assert db.query(Brand).filter(Brand.id == test_brand_id).first() is None
    finally:
        db.close()
