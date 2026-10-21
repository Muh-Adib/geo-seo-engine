import pytest
import json
from fastapi.testclient import TestClient
from web.app import app
from db.models import Brand, Service, LocationTarget, KeywordBankItem
from core.gsc_client import GSCClient
from core.bridge_client import WordPressBridgeClient
from generators.gemini_generator import GeminiMultiAccountEngine

client = TestClient(app)

def test_brand_settings_crud(test_db_brand):
    brand_id = test_db_brand["brand_id"]
    
    # 1. Get settings
    res = client.get(f"/api/brands/{brand_id}/settings")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["settings"]["id"] == brand_id

    # 2. Update settings
    update_payload = {
        "name": "SegiaTech Enterprise",
        "industry_focus": "Software House & Enterprise IT",
        "logo_url": "https://www.segiatech.com/wp-content/uploads/logo.png",
        "tagline": "Software House Berstandar Enterprise Performa Sub-Detik",
        "contact_whatsapp": "6281234567890",
        "consultation_url": "https://www.segiatech.com/kontak",
        "gsc_site_url": "https://www.segiatech.com/",
        "gsc_service_account_json": '{"type": "service_account", "client_email": "seo@segiatech.iam.gserviceaccount.com"}',
        "core_pain_points": [
            "Website lama lambat dan menurunkan konversi",
            "Aplikasi sering down saat lonjakan trafik",
            "Vendor lepas tanggung jawab pasca peluncuran"
        ],
        "core_solutions": [
            "Arsitektur Next.js modern kecepatan sub-detik",
            "Arsitektur backend scalable microservices",
            "Garansi bebas bug dan SLA pemeliharaan berkala"
        ]
    }
    put_res = client.put(f"/api/brands/{brand_id}/settings", json=update_payload)
    assert put_res.status_code == 200
    brand_updated = put_res.json()["brand"]
    assert brand_updated["name"] == "SegiaTech Enterprise"
    assert brand_updated["industry_focus"] == "Software House & Enterprise IT"
    assert brand_updated["contact_whatsapp"] == "6281234567890"
    assert len(brand_updated["core_pain_points"]) == 3
    assert len(brand_updated["core_solutions"]) == 3
    assert brand_updated["has_gsc_credentials"] is True

def test_keyword_bank_and_matrix_generation():
    # 1. Get bank (should auto-seed default items)
    res = client.get("/api/keywords/bank")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total"] >= 10
    assert "action" in data["grouped"]
    assert "subject" in data["grouped"]
    assert "predicate" in data["grouped"]
    assert "city" in data["grouped"]

    # 2. Add custom item to bank
    add_res = client.post("/api/keywords/bank", json={
        "category": "action",
        "value": "Konsultan Cloud Skalabel"
    })
    assert add_res.status_code == 200
    item = add_res.json()["item"]
    assert item["value"] == "Konsultan Cloud Skalabel"
    item_id = item["id"]

    # 3. Generate combinatorial matrix
    matrix_res = client.post("/api/keywords/generate-matrix", json={
        "actions": ["Jasa Pembuatan", "Software House"],
        "subjects": ["Website Enterprise", "Sistem ERP"],
        "predicates": ["Arsitektur Headless", "Performa Sub-Detik"],
        "cities": ["Jakarta", "Surabaya"],
        "limit": 10
    })
    assert matrix_res.status_code == 200
    mdata = matrix_res.json()
    assert mdata["success"] is True
    assert mdata["total_generated"] <= 10
    first_comb = mdata["matrix"][0]
    assert "primary_keyword" in first_comb
    assert "suggested_title" in first_comb
    assert "problem_addressed" in first_comb
    assert "solution_offered" in first_comb

    # 4. Delete item
    del_res = client.delete(f"/api/keywords/bank/{item_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] == item_id

def test_gsc_client_structure():
    client = GSCClient()
    # Test with unconfigured dummy site
    res = client.get_search_analytics("https://example.com", days=28)
    assert res["success"] is False
    assert res["configured"] is False
    assert "overview" in res
    assert res["overview"]["totalClicks"] == 0

import os
from PIL import Image

def test_logo_watermark_in_thumbnail(tmp_path):
    engine = GeminiMultiAccountEngine()
    test_file = str(tmp_path / "test_thumb.jpg")
    engine._build_studio_canvas(
        filepath=test_file,
        title="Jasa Pembuatan Website Enterprise Jakarta",
        brand_name="SegiaTech",
        location="Jakarta",
        service_name="Website Enterprise",
        logo_url=None,
        industry="Software House & Enterprise IT"
    )
    assert os.path.exists(test_file)
    with Image.open(test_file) as img:
        assert img.width == 1200
        assert img.height == 675
