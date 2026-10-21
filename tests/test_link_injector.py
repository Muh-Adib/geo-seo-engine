import json
import pytest
from generators.link_injector import LinkInjector
from db.session import SessionLocal
from db.models import Brand, Service

@pytest.fixture
def injector():
    return LinkInjector(max_body_links=4)

def test_link_injection_and_schema(injector):
    db = SessionLocal()
    try:
        brand = db.query(Brand).filter(Brand.id == "unimasi").first().to_dict()
        service = db.query(Service).filter(Service.id == "unimasi-safety").first().to_dict()

        sample_html = """
        <p>Looking for a 3D safety induction video for heavy mining equipment.</p>
        <p>Our studio ensures HSE visual induction standards are met perfectly.</p>
        """

        sample_faqs = [
            {"question": f"Q{i} about safety video?", "answer": f"Answer {i} detailing 4K and 2-5 week timeline."}
            for i in range(1, 11)
        ]

        processed = injector.inject_all(
            html_content=sample_html,
            brand_data=brand,
            service_data=service,
            target_location="Sydney",
            faq_items=sample_faqs,
            related_articles=[],
            include_schema=True
        )

        # 1. Check in-content links inserted into <p>
        assert '<a href="https://unimasi.com/services/3d-safety-induction"' in processed

        # 2. Check official directory silo block
        assert "Explore Our Regional & Specialized" in processed
        assert "geo-silo-directory" in processed

        # 3. Check JSON-LD Schema
        assert '<script type="application/ld+json">' in processed
        assert '"@type": "FAQPage"' in processed
        assert '"@type": "ProfessionalService"' in processed
        assert '"name": "Q1 about safety video?"' in processed
    finally:
        db.close()
