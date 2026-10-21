import pytest
import mcp.server as s

def test_mcp_tools(test_db_brand):
    b_id = test_db_brand["brand_id"]
    s_id = test_db_brand["service_id"]

    # 1. List brands
    brands_res = s.tool_list_all_brands()
    assert brands_res["success"] is True
    assert brands_res["total_brands"] >= 1

    # 2. Get context
    ctx = s.tool_get_brand_and_service_context(b_id)
    assert ctx["success"] is True
    assert len(ctx["services"]) >= 1

    # 3. Preview article
    preview = s.tool_preview_seo_article(b_id, s_id, "Australia", "Sydney")
    assert preview["success"] is True
    assert preview["tags_count"] == 50
    assert preview["faq_items_count"] == 10
    assert "geo-silo-directory" in preview["content_html"]

    # 4. Generate bulk matrix (draft mode)
    bulk = s.tool_generate_bulk_matrix(
        brand_id=b_id,
        service_id=s_id,
        location_region="Australia",
        cities=["Melbourne", "Brisbane"],
        auto_publish=False
    )
    assert bulk["success"] is True
    assert bulk["total_generated"] == 2

    # 5. Article registry
    registry = s.tool_get_article_registry(limit=10)
    assert registry["success"] is True
    assert registry["count"] >= 2

    # 6. Import sheet data
    csv_sample = "brand_id,brand_name,domain_url,hq_location,default_language,service_id,service_name,pillar_url,target_region,cities\nsheettest,Sheet Test,https://sheettest.com,Yogyakarta,en,st-1,3D Sheet Service,https://sheettest.com/s,Australia,Perth\n"
    imp_res = s.tool_import_sheet_data(csv_sample)
    assert imp_res["success"] is True
    assert imp_res["rows_processed"] == 1
    assert "sheettest" in imp_res["brand_ids"]
