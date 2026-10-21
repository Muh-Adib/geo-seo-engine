import pytest
from starlette.testclient import TestClient
from web.app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_dashboard_homepage(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Unicam GEO Engine" in response.text
    assert "Brands" in response.text

def test_api_list_brands(client):
    response = client.get("/api/brands")
    assert response.status_code == 200
    data = response.json()
    assert "brands" in data
    assert len(data["brands"]) >= 10

def test_api_brand_context(client):
    response = client.get("/api/brands/unimasi/context")
    assert response.status_code == 200
    data = response.json()
    assert data["brand"]["name"] == "UNIMASI"
    assert len(data["services"]) >= 1
    assert len(data["locations"]) >= 1

def test_api_generate_preview(client):
    payload = {
        "brand_id": "unimasi",
        "service_id": "unimasi-safety",
        "location_region": "Australia",
        "city_name": "Perth"
    }
    response = client.post("/api/preview", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "3D Safety Induction Video Perth - UNIMASI" in data["title"]
    assert data["tags_count"] == 50
    assert data["faq_items_count"] == 10
    assert "geo-silo-directory" in data["content_html"]

def test_api_download_template(client):
    response = client.get("/api/download-template")
    assert response.status_code == 200
    assert "brand_id,brand_name" in response.text

def test_api_import_sheet_csv(client):
    csv_sample = """brand_id,brand_name,domain_url,hq_location,default_language,service_id,service_name,pillar_url,target_region,cities
testbrand,Test Brand,https://testbrand.com,Yogyakarta,en,test-srv,Test 3D Service,https://testbrand.com/srv,Australia,"Sydney, Melbourne"
"""
    response = client.post("/api/import-sheet", json={"csv_content": csv_sample})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["rows_processed"] == 1
    assert "testbrand" in data["brand_ids"]

def test_api_gemini_accounts(client):
    response = client.get("/api/gemini/accounts")
    assert response.status_code == 200
    data = response.json()
    assert "accounts" in data
    assert "has_local_antigravity" in data

def test_api_create_and_delete_brand(client):
    payload = {
        "name": "Custom Studio Test",
        "domain_url": "https://customstudiotest.com",
        "hq_location": "Yogyakarta, Indonesia",
        "default_language": "id",
        "service_name": "Jasa 3D Rendering",
        "target_region": "Indonesia",
        "cities": ["Jakarta", "Surabaya"]
    }
    # 1. Create brand
    res = client.post("/api/brands", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    brand_id = data["brand"]["id"]

    # 2. Verify exists
    ctx = client.get(f"/api/brands/{brand_id}/context")
    assert ctx.status_code == 200

    # 3. Delete brand
    del_res = client.delete(f"/api/brands/{brand_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

def test_api_system_diagnostics(client):
    response = client.get("/api/diagnostics/system")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["brands_loaded"] >= 10
    assert data["openrouter_connected"] is True
