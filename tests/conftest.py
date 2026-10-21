import json
import pytest
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import Brand, Service, LocationTarget, Article

@pytest.fixture
def sample_brand_en():
    return {
        "id": "testbrand-en",
        "name": "UNIMASI",
        "slug": "unimasi",
        "platform": "WORDPRESS",
        "domain_url": "https://unimasi.co.id",
        "wp_endpoint_url": "https://unimasi.co.id/wp-json/seo-engine/v1/publish",
        "api_secret_key": "test-key-2026",
        "hq_location": "Yogyakarta, Indonesia",
        "default_language": "en",
        "revision_guarantee": "Free 2x revision guarantee",
        "master_output_spec": "Uncompressed 4K master files",
        "cta_tagline": "Elevate your visual storytelling with UNIMASI."
    }

@pytest.fixture
def sample_service_en():
    return {
        "id": "srv-safety-en",
        "brand_id": "testbrand-en",
        "name": "3D Safety Induction Video",
        "pillar_url": "https://unimasi.co.id/services/3d-safety-induction",
        "anchor_variations": json.dumps(["3D Safety Induction Video", "safety induction animation", "mining safety video"]),
        "target_personas": json.dumps(["HSE Managers", "Mining Directors", "Safety Officers"]),
        "target_industries": json.dumps(["Mining", "Oil & Gas", "Construction"]),
        "base_tags": json.dumps(["safety induction", "3d animation", "mining safety"])
    }

@pytest.fixture
def sample_location_en():
    return {
        "id": "loc-aus",
        "brand_id": "testbrand-en",
        "region_name": "Australia",
        "sub_cities": json.dumps(["Sydney", "Melbourne", "Brisbane", "Perth"]),
        "location_tags": json.dumps(["Sydney video studio", "Melbourne 3d animation", "Perth mining safety"])
    }

@pytest.fixture
def sample_brand_id():
    return {
        "id": "testbrand-id",
        "name": "UNICAM",
        "slug": "unicam",
        "platform": "WORDPRESS",
        "domain_url": "https://unicam.co.id",
        "wp_endpoint_url": "https://unicam.co.id/wp-json/seo-engine/v1/publish",
        "api_secret_key": "test-key-2026",
        "hq_location": "Yogyakarta, Indonesia",
        "default_language": "id",
        "revision_guarantee": "Garansi revisi 2x gratis",
        "master_output_spec": "Master 4K uncompressed",
        "cta_tagline": "Solusi dokumentasi visual profesional bersama UNICAM."
    }

@pytest.fixture
def sample_service_id():
    return {
        "id": "srv-mapping-id",
        "brand_id": "testbrand-id",
        "name": "Jasa Pemetaan Drone LiDAR",
        "pillar_url": "https://unicam.co.id/services/jasa-pemetaan-drone",
        "anchor_variations": json.dumps(["Jasa Pemetaan Drone LiDAR", "vendor drone mapping", "surveyor lidar"]),
        "target_personas": json.dumps(["Project Manager", "Site Engineer", "Kepala Proyek"]),
        "target_industries": json.dumps(["Konstruksi", "Infrastruktur", "Pertambangan"]),
        "base_tags": json.dumps(["pemetaan drone", "drone lidar", "surveyor"])
    }

@pytest.fixture
def sample_location_id():
    return {
        "id": "loc-id",
        "brand_id": "testbrand-id",
        "region_name": "Indonesia",
        "sub_cities": json.dumps(["Jakarta", "Surabaya", "Bandung", "Semarang"]),
        "location_tags": json.dumps(["jasa drone jakarta", "pemetaan surabaya", "surveyor bandung"])
    }

@pytest.fixture(scope="function")
def test_db_brand(sample_brand_en, sample_service_en, sample_location_en):
    db: Session = SessionLocal()
    brand_id = sample_brand_en["id"]
    service_id = sample_service_en["id"]
    loc_id = sample_location_en["id"]
    
    # Setup test records
    b = Brand(**sample_brand_en)
    s = Service(**sample_service_en)
    l = LocationTarget(**sample_location_en)
    
    db.merge(b)
    db.merge(s)
    db.merge(l)
    db.commit()
    
    yield {"brand_id": brand_id, "service_id": service_id, "loc_id": loc_id}
    
    # Teardown
    db.query(Article).filter(Article.brand_id == brand_id).delete()
    db.query(Service).filter(Service.id == service_id).delete()
    db.query(LocationTarget).filter(LocationTarget.id == loc_id).delete()
    db.query(Brand).filter(Brand.id == brand_id).delete()
    db.commit()
    db.close()
