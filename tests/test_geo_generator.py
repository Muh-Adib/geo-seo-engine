import re
import pytest
from generators.geo_writer import ProgrammaticGEOWriter
from db.session import SessionLocal
from db.models import Brand, Service, LocationTarget

@pytest.fixture
def writer():
    return ProgrammaticGEOWriter()

def test_12_block_structure_and_constraints_english(writer):
    db = SessionLocal()
    try:
        brand = db.query(Brand).filter(Brand.id == "unimasi").first().to_dict()
        service = db.query(Service).filter(Service.id == "unimasi-safety").first().to_dict()
        location = db.query(LocationTarget).filter(LocationTarget.brand_id == "unimasi").first().to_dict()
        
        article = writer.generate_programmatic_article(
            brand_data=brand,
            service_data=service,
            location_data=location,
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
        # Strip script tags when checking for emails
        text_without_scripts = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
        found_emails = re.findall(email_pattern, text_without_scripts)
        assert len(found_emails) == 0, f"Found email addresses: {found_emails}"
        assert "@unimasi.co.id" not in html

        # 6. Italic Keyword Subjudul on English regional article
        assert "*Keyword Subjudul:" in html

        # 7. Meta description length
        assert len(article["meta_description"]) <= 160
    finally:
        db.close()

def test_indonesian_language_adaptation(writer):
    db = SessionLocal()
    try:
        brand = db.query(Brand).filter(Brand.id == "unicam").first().to_dict()
        service = db.query(Service).filter(Service.id == "unicam-mapping").first().to_dict()
        location = db.query(LocationTarget).filter(LocationTarget.brand_id == "unicam").first().to_dict()

        article = writer.generate_programmatic_article(
            brand_data=brand,
            service_data=service,
            location_data=location,
            specific_city="Jakarta",
            use_llm=False
        )

        html = article["content_html"]

        # Check Indonesian keywords and structure
        assert "Jasa Video Mapping Jakarta - UNICAM STUDIO" in article["title"]
        assert len(article["faq_items"]) == 10
        assert len(article["tags"]) == 50
        assert "Yogyakarta" in html
        assert "Garansi revisi 2x gratis" in html or "Free 2x revision" in html or "garansi" in html.lower()
    finally:
        db.close()
