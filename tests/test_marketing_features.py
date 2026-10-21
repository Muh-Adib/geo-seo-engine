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

def test_per_brand_keyword_bank_isolation(test_db_brand):
    brand_id = test_db_brand["brand_id"]
    
    # 1. Fetch bank for this brand
    res = client.get(f"/api/keywords/bank?brand_id={brand_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["brand_id"] == brand_id
    
    # 2. Add keyword strictly for this brand
    add_res = client.post("/api/keywords/bank", json={
        "category": "action",
        "value": f"Vendor Spesifik {brand_id}",
        "brand_id": brand_id
    })
    assert add_res.status_code == 200
    new_item = add_res.json()["item"]
    assert new_item["brand_id"] == brand_id

    # 3. Verify it is returned for this brand
    res_after = client.get(f"/api/keywords/bank?brand_id={brand_id}")
    items = res_after.json()["items"]
    assert any(i["value"] == f"Vendor Spesifik {brand_id}" for i in items)

def test_brand_asset_directory_and_prompt_generation(test_db_brand):
    brand_id = test_db_brand["brand_id"]

    # 1. Create tailored prompt
    prompt_res = client.post(f"/api/brands/{brand_id}/create-image-prompt", json={
        "brand_id": brand_id,
        "service_name": "Enterprise ERP System",
        "location": "Jakarta"
    })
    assert prompt_res.status_code == 200
    pdata = prompt_res.json()
    assert pdata["success"] is True
    assert "Enterprise ERP System" in pdata["prompt"] or "Jakarta" in pdata["prompt"]

    # 2. Generate image scoped to brand
    gen_res = client.post(f"/api/brands/{brand_id}/generate-image", json={
        "prompt": "Clean enterprise software studio with futuristic dashboard 8k",
        "aspect_ratio": "16:9",
        "style": "photorealistic",
        "brand_id": brand_id
    })
    assert gen_res.status_code == 200
    gdata = gen_res.json()
    assert gdata["success"] is True
    assert f"/output/assets/{brand_id}/images/" in gdata["url"]
    assert os.path.exists(gdata["file_path"])

    # 3. Retrieve brand assets
    assets_res = client.get(f"/api/brands/{brand_id}/assets")
    assert assets_res.status_code == 200
    adata = assets_res.json()
    assert adata["success"] is True
    assert adata["brand_id"] == brand_id
    assert adata["total"] >= 1
    assert any(img["filename"] == gdata["filename"] for img in adata["images"])

def test_brand_asset_upload(test_db_brand, tmp_path):
    brand_id = test_db_brand["brand_id"]
    test_img_path = tmp_path / "antigravity_render.jpg"
    test_img = Image.new("RGB", (800, 600), color=(30, 41, 59))
    test_img.save(test_img_path, "JPEG")

    with open(test_img_path, "rb") as f:
        res = client.post(
            f"/api/brands/{brand_id}/assets/upload",
            files={"file": ("antigravity_render.jpg", f, "image/jpeg")}
        )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "upload-" in data["asset"]["filename"]
    assert f"/output/assets/{brand_id}/images/" in data["asset"]["url"]
    assert os.path.exists(data["asset"]["file_path"])
