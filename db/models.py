import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Brand(Base):
    __tablename__ = "brands"

    id = Column(String(50), primary_key=True) # e.g. "unimasi", "unicam", "segiatech"
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    platform = Column(String(20), default="WORDPRESS") # WORDPRESS or NEXTJS
    domain_url = Column(String(255), nullable=False)
    wp_endpoint_url = Column(String(255), nullable=True) # e.g. https://unimasi.com/wp-json/seo-engine/v1/publish
    api_secret_key = Column(String(100), default="unicam-geo-secret-key-2026")
    
    hq_location = Column(String(100), default="Yogyakarta, Indonesia")
    default_language = Column(String(10), default="en") # "en" or "id"
    brand_voice = Column(Text, nullable=True)
    core_value_pillars = Column(Text, default="[]") # JSON list of objects [{title, desc}]
    revision_guarantee = Column(String(100), default="Free 2x revision guarantee")
    master_output_spec = Column(String(100), default="Uncompressed 4K master files")
    cta_tagline = Column(String(255), default="🎥 Elevate your visual content with our world-class studio.")

    # Extended Brand & GSC Settings
    logo_url = Column(String(500), nullable=True) # Logo image URL or local path to overlay on thumbnail
    tagline = Column(String(255), nullable=True) # Official brand tagline
    industry_focus = Column(String(100), default="Technology & Software") # e.g. Software House, Creative Media
    contact_whatsapp = Column(String(50), nullable=True) # WhatsApp consultation number
    contact_email = Column(String(100), nullable=True)
    consultation_url = Column(String(255), nullable=True) # Consultation link (e.g. /kontak)
    gsc_site_url = Column(String(255), nullable=True) # GSC Property (e.g. https://www.segiatech.com or sc-domain:segiatech.com)
    gsc_service_account_json = Column(Text, nullable=True) # Service account JSON credentials for GSC
    core_pain_points = Column(Text, default="[]") # JSON list of client pain points solved
    core_solutions = Column(Text, default="[]") # JSON list of solutions provided

    # Relationships
    services = relationship("Service", back_populates="brand", cascade="all, delete-orphan")
    locations = relationship("LocationTarget", back_populates="brand", cascade="all, delete-orphan")
    media_assets = relationship("MediaAsset", back_populates="brand", cascade="all, delete-orphan")
    articles = relationship("Article", back_populates="brand", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "platform": self.platform,
            "domain_url": self.domain_url,
            "wp_endpoint_url": self.wp_endpoint_url,
            "api_secret_key": self.api_secret_key,
            "hq_location": self.hq_location,
            "default_language": self.default_language,
            "brand_voice": self.brand_voice or "Professional, Solutif, Enterprise Tech",
            "core_value_pillars": json.loads(self.core_value_pillars or "[]"),
            "revision_guarantee": self.revision_guarantee,
            "master_output_spec": self.master_output_spec,
            "cta_tagline": self.cta_tagline,
            "logo_url": self.logo_url or "",
            "tagline": self.tagline or self.cta_tagline,
            "industry_focus": self.industry_focus or "Technology & Software",
            "contact_whatsapp": self.contact_whatsapp or "",
            "contact_email": self.contact_email or "",
            "consultation_url": self.consultation_url or "",
            "gsc_site_url": self.gsc_site_url or self.domain_url,
            "has_gsc_credentials": bool(self.gsc_service_account_json and len(self.gsc_service_account_json.strip()) > 10),
            "core_pain_points": json.loads(self.core_pain_points or "[]"),
            "core_solutions": json.loads(self.core_solutions or "[]"),
            "services_count": len(self.services) if self.services else 0,
            "articles_count": len(self.articles) if self.articles else 0
        }

class Service(Base):
    __tablename__ = "services"

    id = Column(String(50), primary_key=True)
    brand_id = Column(String(50), ForeignKey("brands.id"), nullable=False)
    name = Column(String(150), nullable=False) # e.g. "3D Safety Induction Video"
    pillar_url = Column(String(255), nullable=False)
    anchor_variations = Column(Text, default="[]") # JSON list of string anchors
    
    technical_pipeline = Column(Text, default="[]") # JSON list of strings (e.g. 3D modeling, LOTO sequence)
    target_personas = Column(Text, default="[]") # JSON list of strings (e.g. COOs, HSE Directors)
    target_industries = Column(Text, default="[]") # JSON list of strings (e.g. Mining, Construction)
    sub_solutions = Column(Text, default="[]") # JSON list of 4 solutions
    production_steps = Column(Text, default="[]") # JSON list of 5 steps
    estimated_timeline = Column(String(50), default="2 to 5 weeks")
    deliverable_formats = Column(Text, default='["4K MP4/MOV", "Apple ProRes", "SCORM/LMS package"]')
    base_tags = Column(Text, default="[]") # JSON list of 30-40 tags

    brand = relationship("Brand", back_populates="services")
    articles = relationship("Article", back_populates="service")
    media_assets = relationship("MediaAsset", back_populates="service")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "brand_id": self.brand_id,
            "name": self.name,
            "pillar_url": self.pillar_url,
            "anchor_variations": json.loads(self.anchor_variations or "[]"),
            "technical_pipeline": json.loads(self.technical_pipeline or "[]"),
            "target_personas": json.loads(self.target_personas or "[]"),
            "target_industries": json.loads(self.target_industries or "[]"),
            "sub_solutions": json.loads(self.sub_solutions or "[]"),
            "production_steps": json.loads(self.production_steps or "[]"),
            "estimated_timeline": self.estimated_timeline,
            "deliverable_formats": json.loads(self.deliverable_formats or "[]"),
            "base_tags": json.loads(self.base_tags or "[]")
        }

class LocationTarget(Base):
    __tablename__ = "location_targets"

    id = Column(String(50), primary_key=True)
    brand_id = Column(String(50), ForeignKey("brands.id"), nullable=False)
    region_name = Column(String(100), nullable=False) # e.g. "Australia", "UAE", "Indonesia"
    sub_cities = Column(Text, default="[]") # JSON list of cities (e.g. Sydney, Melbourne)
    local_context_notes = Column(Text, nullable=True) # e.g. Safe Work Australia
    location_tags = Column(Text, default="[]")

    brand = relationship("Brand", back_populates="locations")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "brand_id": self.brand_id,
            "region_name": self.region_name,
            "sub_cities": json.loads(self.sub_cities or "[]"),
            "local_context_notes": self.local_context_notes,
            "location_tags": json.loads(self.location_tags or "[]")
        }

class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(String(50), primary_key=True)
    brand_id = Column(String(50), ForeignKey("brands.id"), nullable=False)
    service_id = Column(String(50), ForeignKey("services.id"), nullable=True)
    file_url = Column(String(255), nullable=False)
    role = Column(String(30), default="FEATURED") # FEATURED or INLINE_ILLUSTRATION
    alt_text_template = Column(String(255), default="{primary_keyword} - {brand_name}")
    title_template = Column(String(255), default="Professional {service_name} in {location} by {brand_name}")
    caption_template = Column(String(255), default="High-resolution 4K render for {primary_keyword}.")

    brand = relationship("Brand", back_populates="media_assets")
    service = relationship("Service", back_populates="media_assets")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "brand_id": self.brand_id,
            "service_id": self.service_id,
            "file_url": self.file_url,
            "role": self.role,
            "alt_text_template": self.alt_text_template,
            "title_template": self.title_template,
            "caption_template": self.caption_template
        }

class Article(Base):
    __tablename__ = "articles"

    id = Column(String(60), primary_key=True)
    brand_id = Column(String(50), ForeignKey("brands.id"), nullable=False)
    service_id = Column(String(50), ForeignKey("services.id"), nullable=False)
    primary_keyword = Column(String(200), nullable=False)
    target_location = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    
    structured_content = Column(Text, default="{}") # JSON dict storing 12 blocks
    content_html = Column(Text, nullable=False)
    faq_data = Column(Text, default="[]") # JSON list of 10 Q&A items
    meta_description = Column(String(255), nullable=False)
    tags = Column(Text, default="[]") # JSON list of 50 tags
    
    published_url = Column(String(255), nullable=True)
    wp_post_id = Column(Integer, nullable=True)
    status = Column(String(30), default="DRAFT") # DRAFT, PUBLISHED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    brand = relationship("Brand", back_populates="articles")
    service = relationship("Service", back_populates="articles")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "brand_id": self.brand_id,
            "service_id": self.service_id,
            "primary_keyword": self.primary_keyword,
            "target_location": self.target_location,
            "title": self.title,
            "slug": self.slug,
            "meta_description": self.meta_description,
            "tags_count": len(json.loads(self.tags or "[]")),
            "faq_count": len(json.loads(self.faq_data or "[]")),
            "published_url": self.published_url,
            "wp_post_id": self.wp_post_id,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else ""
        }

class KeywordBankItem(Base):
    """
    Marketing Matrix Keyword Bank.
    Combines 4 dimensions:
    - action (Intent/Action: Jasa Pembuatan, Software House, Vendor, Konsultan)
    - subject (Product/Service: Website Enterprise, Aplikasi Web Kustom, Sistem ERP)
    - predicate (Value Prop/Problem Solved: Arsitektur Headless Cloud-Ready, Solusi Otomasi Bisnis)
    - city (Target Region/City: Jakarta, Surabaya, Bandung, dll.)
    """
    __tablename__ = "keyword_bank"

    id = Column(String(50), primary_key=True)
    brand_id = Column(String(50), ForeignKey("brands.id", ondelete="CASCADE"), nullable=True)
    category = Column(String(30), nullable=False) # "action", "subject", "predicate", "city"
    value = Column(String(150), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "brand_id": self.brand_id,
            "category": self.category,
            "value": self.value,
            "is_active": self.is_active
        }
