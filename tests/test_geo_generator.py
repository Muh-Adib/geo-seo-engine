import re
import pytest
from generators.geo_writer import ProgrammaticGEOWriter

@pytest.fixture
def writer():
    return ProgrammaticGEOWriter()

def test_12_block_structure_and_constraints_english(writer, sample_brand_en, sample_service_en, sample_location_en):
    article = writer.generate_programmatic_article(
        brand_data=sample_brand_en,
        service_data=sample_service_en,
        location_data=sample_location_en,
        specific_city="Sydney",
        use_llm=False
    )

    html = article["content_html"]

    # 1. H1 / H2 Title check
    assert "3D Safety Induction Video Sydney - UNIMASI" in article["title"]
    
    # 2. Intro mentions tier-1 cities & HQ Yogyakarta
    assert "Yogyakarta, Indonesia" in html
    assert "Sydney" in html

    # 3. Exactly 10 GEO FAQ items
    assert len(article["faq_items"]) == 10
    assert "10 Questions and Answers" in html

    # 4. Exactly 50 tags prepared for WordPress taxonomy (NOT in body html)
    assert len(article["tags"]) == 50
    assert "Tags Transaksional & Terkait:" not in html
    
    # 5. Strict NO EMAIL rule
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    text_without_scripts = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
    found_emails = re.findall(email_pattern, text_without_scripts)
    assert len(found_emails) == 0, f"Found email addresses: {found_emails}"
    assert "@unimasi.co.id" not in html

    # 6. Italic Keyword Subjudul on English regional article
    assert "*Keyword Subjudul:" in html

    # 7. Meta description length
    assert len(article["meta_description"]) <= 160

def test_indonesian_language_adaptation(writer, sample_brand_id, sample_service_id, sample_location_id):
    article = writer.generate_programmatic_article(
        brand_data=sample_brand_id,
        service_data=sample_service_id,
        location_data=sample_location_id,
        specific_city="Jakarta",
        use_llm=False
    )

    html = article["content_html"]

    # Check Indonesian keywords and structure
    assert "Jasa Pemetaan Drone LiDAR Jakarta - UNICAM" in article["title"]
    assert len(article["faq_items"]) == 10
    assert len(article["tags"]) == 50
    assert "Yogyakarta" in html
    assert "garansi" in html.lower()
