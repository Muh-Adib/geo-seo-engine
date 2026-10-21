import pytest
from starlette.testclient import TestClient
from web.app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_dashboard_homepage(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "GEO SEO Engine" in response.text
    assert "Situs & Brand" in response.text

def test_api_list_brands(client):
    response = client.get("/api/brands")
    assert response.status_code == 200
    data = response.json()
    assert "brands" in data
    assert isinstance(data["brands"], list)

def test_api_brand_context(client, test_db_brand):
    b_id = test_db_brand["brand_id"]
    response = client.get(f"/api/brands/{b_id}/context")
    assert response.status_code == 200
    data = response.json()
    assert data["brand"]["name"] == "UNIMASI"
    assert len(data["services"]) >= 1
    assert len(data["locations"]) >= 1

def test_api_generate_preview(client, test_db_brand):
    b_id = test_db_brand["brand_id"]
    s_id = test_db_brand["service_id"]
    payload = {
        "brand_id": b_id,
        "service_id": s_id,
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
    assert "router_connected" in data

def test_api_router_endpoints(client):
    # 1. Status
    res = client.get("/api/router/status")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 2. Models
    m_res = client.get("/api/router/models")
    assert m_res.status_code == 200
    assert m_res.json()["success"] is True
    assert m_res.json()["count"] > 0

    # 3. Settings update
    s_res = client.post("/api/router/settings", json={
        "base_url": "http://127.0.0.1:20128/v1",
        "api_key": "test-key",
        "selected_model": "ox-alpha",
        "temperature": 0.7
    })
    assert s_res.status_code == 200
    assert s_res.json()["success"] is True

def test_api_image_generator_and_gallery(client):
    # 1. Generate custom image
    gen_res = client.post("/api/images/generate", json={
        "prompt": "4K Cinematic Studio Rig",
        "aspect_ratio": "16:9",
        "style": "photorealistic",
        "brand_name": "GEO Studio Test"
    })
    assert gen_res.status_code == 200
    img_data = gen_res.json()
    assert img_data["success"] is True
    assert "output/images" in img_data["file_path"]

    # 2. Gallery listing
    gal_res = client.get("/api/images/gallery")
    assert gal_res.status_code == 200
    assert len(gal_res.json().get("images", [])) >= 1
