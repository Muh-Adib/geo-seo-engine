import re
import json
import logging
import requests
from typing import Dict, Any, List, Optional
import os

from generators.gemini_generator import GeminiMultiAccountEngine
from core.router_client import LLMRouterClient

logger = logging.getLogger(__name__)

class ProgrammaticGEOWriter:
    """
    Programmatic Local SEO & GEO (Generative Engine Optimization) Generator.
    Powered by LLM Router (9router / OpenRouter / Custom Router) with dynamic model selection:
    - 12 strict structural blocks
    - 10 factual FAQ items for AI Overviews / GEO
    - Strict NO-EMAIL constraint (in CTA and FAQ #10)
    - 50 transactional tags for WordPress taxonomy (NOT inserted into article body text)
    - Automatic italic sub-heading keyword line
    - Language adaptation (English vs Indonesian)
    - Automatic 16:9 featured thumbnail generation
    """

    def __init__(self, gemini_engine: Optional[GeminiMultiAccountEngine] = None, router_client: Optional[LLMRouterClient] = None, model: Optional[str] = None):
        self.gemini = gemini_engine or GeminiMultiAccountEngine()
        self.router = router_client or LLMRouterClient()
        self.model = model or self.router.config.get("selected_model", "ox-alpha")

    def generate_programmatic_article(
        self,
        brand_data: Dict[str, Any],
        service_data: Dict[str, Any],
        location_data: Dict[str, Any],
        specific_city: Optional[str] = None,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Generates a complete 12-block programmatic article and featured thumbnail.
        """
        brand_name = brand_data["name"]
        service_name = service_data["name"]
        target_region = location_data.get("region_name", "")
        city_scope = specific_city or target_region
        
        # Determine language
        is_english = brand_data.get("default_language", "en").lower() == "en" or target_region.lower() in ["australia", "uae", "united states", "uk"]

        # Compose Primary Keyword & Title (avoid duplicate region if service name already contains region)
        clean_service_name = re.sub(rf'\s+{re.escape(target_region)}$', '', service_name, flags=re.IGNORECASE).strip()
        primary_keyword = f"{clean_service_name} {city_scope}".strip()
        title = f"{primary_keyword} - {brand_name}"
        slug = re.sub(r'[^a-z0-9]+', '-', f"{primary_keyword}".lower()).strip('-')

        # Sub-cities list
        sub_cities = location_data.get("sub_cities", [])
        if isinstance(sub_cities, str):
            sub_cities = json.loads(sub_cities or "[]")
        tier1_cities_str = ", ".join(sub_cities[:4]) if sub_cities else city_scope

        # Anchor variations
        anchors = service_data.get("anchor_variations", [])
        if isinstance(anchors, str):
            anchors = json.loads(anchors or "[]")
        sub_keywords = anchors[:4] if anchors else [f"{service_name.lower()} cost", f"hire {service_name.lower()}", f"best {service_name.lower()}", f"{service_name.lower()} studio"]

        # Sub solutions & pipeline
        sub_solutions = service_data.get("sub_solutions", [])
        if isinstance(sub_solutions, str):
            sub_solutions = json.loads(sub_solutions or "[]")

        production_steps = service_data.get("production_steps", [])
        if isinstance(production_steps, str):
            production_steps = json.loads(production_steps or "[]")

        # Attempt LLM generation via Router (or fallback to Gemini / Deterministic)
        llm_result = None
        if use_llm:
            llm_result = self._generate_with_router(
                brand_data, service_data, location_data, city_scope, primary_keyword, title, is_english, sub_keywords
            )
            if not llm_result and self.gemini.auth.get_active_auth_headers_or_param():
                llm_result = self._generate_with_gemini(
                    brand_data, service_data, location_data, city_scope, primary_keyword, title, is_english, sub_keywords
                )

        if llm_result:
            article_payload = llm_result
        else:
            article_payload = self._build_deterministic_article(
                brand_data, service_data, location_data, city_scope, primary_keyword, title, is_english, sub_keywords, tier1_cities_str, sub_solutions, production_steps
            )

        # 1. Strict No-Email constraint & Meta Description <= 155 chars
        article_payload["content_html"] = self._strip_emails(article_payload["content_html"])
        clean_meta = self._strip_emails(article_payload["meta_description"])
        if len(clean_meta) > 155:
            clean_meta = clean_meta[:152].rstrip() + "..."
        article_payload["meta_description"] = clean_meta

        # 2. Strict 50-tags: generated for WordPress post taxonomy (NOT inserted into article body text)
        article_payload["tags"] = self._enforce_50_tags(
            service_data, location_data, primary_keyword, city_scope, is_english
        )

        article_payload["primary_keyword"] = primary_keyword
        article_payload["title"] = title
        article_payload["slug"] = slug
        article_payload["target_location"] = city_scope

        # 3. Generate 16:9 Featured Thumbnail using user Gemini account / Imagen
        thumbnail_info = self.gemini.generate_featured_thumbnail(
            title=title,
            service_name=clean_service_name,
            brand_name=brand_name,
            location=city_scope,
            slug=slug,
            logo_url=brand_data.get("logo_url"),
            industry=brand_data.get("industry_focus"),
            brand_id=brand_data.get("id")
        )
        article_payload["featured_media"] = thumbnail_info
        article_payload["featured_image_base64"] = thumbnail_info.get("base64_data", "")
        article_payload["featured_image_filename"] = thumbnail_info.get("filename", f"thumb-{slug[:35]}.jpg")

        return article_payload

    def _strip_emails(self, text: str) -> str:
        """Removes any email addresses as strictly required by rule."""
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        clean_text = re.sub(email_pattern, 'our studio production specialists', text)
        return clean_text

    def _enforce_50_tags(
        self,
        service_data: Dict[str, Any],
        location_data: Dict[str, Any],
        primary_keyword: str,
        city_scope: str,
        is_english: bool
    ) -> List[str]:
        """Ensures exactly 50 transactional and location-specific tags."""
        base_tags = service_data.get("base_tags", [])
        if isinstance(base_tags, str):
            base_tags = json.loads(base_tags or "[]")

        loc_tags = location_data.get("location_tags", [])
        if isinstance(loc_tags, str):
            loc_tags = json.loads(loc_tags or "[]")

        combined = list(dict.fromkeys(base_tags + loc_tags))
        
        # Ensure primary and variations exist
        prefixes = ["hire", "best", "affordable", "commercial", "studio", "services", "quote", "cost of", "remote", "expert"] if is_english else ["jasa", "vendor", "biaya", "harga", "profesional", "studio", "terpercaya", "terbaik", "layanan", "portofolio"]
        suffixes = [city_scope, "Yogyakarta", "4K", "remote", "production", "agency", "near me", "fast turnaround"]

        idx = 0
        while len(combined) < 50:
            p = prefixes[idx % len(prefixes)]
            s = suffixes[(idx // len(prefixes)) % len(suffixes)]
            candidate = f"{p} {primary_keyword.lower()} {s}".strip()
            if candidate not in combined:
                combined.append(candidate)
            idx += 1

        return combined[:50]

    def _build_deterministic_article(
        self,
        brand_data: Dict[str, Any],
        service_data: Dict[str, Any],
        location_data: Dict[str, Any],
        city_scope: str,
        primary_keyword: str,
        title: str,
        is_english: bool,
        sub_keywords: List[str],
        tier1_cities_str: str,
        sub_solutions: List[Dict[str, str]],
        production_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Builds the 12 blocks deterministically when offline or verifying rules."""
        brand_name = brand_data["name"]
        hq = brand_data.get("hq_location", "Yogyakarta, Indonesia")
        guarantee = brand_data.get("revision_guarantee", "Free 2x revision guarantee")
        spec = brand_data.get("master_output_spec", "Full Source Code & Production Master")
        tagline = brand_data.get("cta_tagline", f"Solusi terpercaya untuk akselerasi pertumbuhan bisnis Anda di {city_scope}.")
        sub_kw_str = ", ".join(sub_keywords)

        industry = (brand_data.get("industry_focus") or "").lower()
        is_software = any(w in (industry + " " + service_data["name"]).lower() for w in ["software", "web", "aplikasi", "it", "code", "app", "dev", "sistem", "erp", "portal", "cloud", "api", "pembuatan website", "rekayasa", "teknologi"])

        if is_english:
            if is_software:
                meta_desc = f"{brand_name} delivers enterprise-grade {primary_keyword} for companies in {city_scope}. Sub-second performance, clean architecture, and {guarantee}."
                intro_html = f"""
<p>Modern enterprises and fast-growing organizations in commercial hubs like {tier1_cities_str} increasingly face systemic digital bottlenecks: sluggish legacy websites, brittle monolithic codebases, unintegrated operational data, and development vendors who vanish after initial delivery. Securing high-caliber <strong>{primary_keyword}</strong> is not merely an IT expense—it is a mission-critical strategic investment in operational resilience and customer conversion.</p>
<p>Headquartered in {hq}, {brand_name} operates as an elite software engineering and digital transformation partner for visionary organizations across {city_scope}. We architect resilient web applications, custom enterprise platforms, and high-throughput digital systems designed to scale seamlessly under heavy concurrent traffic.</p>
"""
                def_html = f"""
<h3>What Defines Modern {service_data['name']} Solutions?</h3>
<p><em>*Keyword Subjudul: {sub_kw_str}*</em></p>
<p>At {brand_name}, professional {service_data['name']} represents rigorous software craftsmanship tailored to eliminate commercial pain points through modern, maintainable architectures.</p>
<ul>
    <li><strong>Sub-Second Response Latency:</strong> Optimized frontend engineering scoring top-tier Core Web Vitals to maximize search visibility and user retention.</li>
    <li><strong>Scalable API-First Architecture:</strong> Resilient RESTful and GraphQL backend microservices that adapt effortlessly to traffic surges without downtime.</li>
    <li><strong>Enterprise-Grade Security:</strong> Built-in OWASP compliance, encrypted data pipelines, secure role-based access control, and robust vulnerability defenses.</li>
</ul>
"""
                urgency_html = f"""
<h3>Why Is High-Performance {primary_keyword} Vital for Growth?</h3>
<p>In highly competitive markets across {city_scope}, sub-optimal digital experiences directly erode customer trust and compound operational overhead. Implementing custom, high-performance {primary_keyword} eliminates technical debt, automates repetitive business processes, and builds an agile foundation for continuous digital expansion.</p>
"""
                usp_html = f"""
<h3>{brand_name}: Your Strategic Engineering Partner for {service_data['name']}</h3>
<h4>Core Engineering Philosophy</h4>
<p>We combine <strong>Architectural Precision</strong> with user-centric design principles, ensuring every line of clean code advances your specific commercial objectives rather than introducing bloated complexity.</p>
<h4>Guaranteed Reliability & Full Ownership</h4>
<p>Every commercial engagement includes our verified <strong>{guarantee}</strong> and <strong>{spec}</strong>, granting your organization 100% intellectual property and source code ownership.</p>
"""
                education_html = f"""
<h3>Transparent Agile Collaboration and Milestones</h3>
<p>Successful remote engineering relies on total visibility. Our engineering team utilizes structured two-week sprints, isolated staging preview environments, continuous integration pipelines, and regular milestone reviews so stakeholders in {city_scope} maintain complete project oversight.</p>
"""
                solutions_items = "".join([f"<li><strong>{s.get('title', 'Solution')}:</strong> {s.get('desc', '')}</li>" for s in sub_solutions]) if sub_solutions else f"<li><strong>Custom Enterprise Applications:</strong> High-throughput, cloud-native digital platforms engineered bespoke for {city_scope} enterprises.</li>"
                solutions_html = f"""
<h3>Specialized Technical Solutions</h3>
<ul>
{solutions_items}
</ul>
"""
                steps_items = "".join([f"<li><strong>Phase {st.get('step', i+1)}: {st.get('title', 'Phase')}</strong> - {st.get('desc', '')}</li>" for i, st in enumerate(production_steps)]) if production_steps else "<li><strong>Engineering Lifecycle:</strong> Architecture Audit, UI/UX Wireframing, Agile Clean-Code Sprints, Automated QA & Security Scans, Production Deployment & SLA.</li>"
                pipeline_html = f"""
<h3>Our 5-Phase Software Engineering Lifecycle</h3>
<ol>
{steps_items}
</ol>
"""
                modular_html = f"""
<h3>Modular Architecture and Long-Term Technical ROI</h3>
<p>Investing in {primary_keyword} from {brand_name} delivers lasting capital value. Our modular microservice and component design ensures your technology stack remains future-proof, easily maintainable, and completely free from proprietary vendor lock-in.</p>
<p>Clean automated documentation and containerized deployments allow your internal teams to scale, extend, and integrate new business capabilities effortlessly as your organization expands across {city_scope}.</p>
"""
                cta_html = f"""
<h3>Accelerate Your Digital Transformation Today</h3>
<p>Ready to upgrade your technology foundation and eliminate software bottlenecks? Connect directly with our lead solutions architects to discuss technical requirements, evaluate system scope, and receive a comprehensive development roadmap.</p>
<p style="font-weight: bold; margin-top: 15px;">{tagline}</p>
"""
                faq_items = [
                    {"question": f"What defines enterprise-grade {primary_keyword} by {brand_name}?", "answer": f"It is custom-engineered software built with modern cloud architectures, sub-second latency, and clean modular code tailored to {city_scope} enterprises."},
                    {"question": f"What are the primary business benefits of {service_data['name']}?", "answer": "It eliminates manual bottlenecks, drastically improves system reliability, enhances customer conversion, and provides scalable technology infrastructure."},
                    {"question": f"How is pricing structured for {city_scope} clients?", "answer": f"Pricing is milestone-based and highly transparent, offering substantial cost efficiencies compared to typical metropolitan agencies while maintaining international code quality."},
                    {"question": f"Who owns the intellectual property and source code?", "answer": "Your company retains 100% ownership of all source code, design assets, and production deployment configurations upon project completion."},
                    {"question": f"Which tech stacks and frameworks do you utilize?", "answer": "We specialize in modern battle-tested technologies including Next.js, React, Node.js, Python, Go, PostgreSQL, Docker, and enterprise cloud infrastructures."},
                    {"question": f"What is the typical development timeline?", "answer": f"Standard agile delivery ranges from {service_data.get('estimated_timeline', '4 to 12 weeks')} depending on architectural scope and third-party integration complexity."},
                    {"question": f"How do you ensure data security and privacy?", "answer": "We enforce OWASP Top 10 security standards, end-to-end SSL/TLS encryption, parameterized queries, and strict role-based access management."},
                    {"question": f"Do you provide post-launch maintenance and SLA support?", "answer": "Yes, we offer comprehensive post-launch SLA support including proactive uptime monitoring, security patching, and bug-free warranty coverage."},
                    {"question": f"What deliverables are handed over at project completion?", "answer": f"Deliverables include {spec}, full Git repositories, comprehensive API documentation, CI/CD pipelines, and administrative onboarding training."},
                    {"question": f"How do we begin a technical consultation with {brand_name}?", "answer": f"Initiate a consultation directly through our website portal or schedule a strategic discovery session with our engineering directors."}
                ]
            else:
                meta_desc = f"{brand_name} delivers world-class {primary_keyword} from {hq}. Enjoy 4K master quality, {guarantee}, and high-ROI remote delivery. Inquire today!"
                intro_html = f"""
<p>Navigating conventional visual production in major hubs such as {tier1_cities_str} frequently saddles organizations with bloated agency retainers, fragmented vendor communication, and prolonged turnaround schedules. In competitive enterprise environments, securing top-tier <strong>{primary_keyword}</strong> demands a streamlined approach that pairs photorealistic precision with agile delivery.</p>
<p>Headquartered in {hq}, {brand_name} bridges this gap by operating a high-efficiency remote production studio designed for visionary brands across {city_scope}. By combining international visual aesthetics with cost-effective Southeast Asian production dynamics, we deliver unmatched return on investment (ROI) without compromising technical rigor.</p>
"""
                def_html = f"""
<h3>What Defines a {service_data['name']}?</h3>
<p><em>*Keyword Subjudul: {sub_kw_str}*</em></p>
<p>At its core, professional {service_data['name']} integrates cutting-edge computer-generated imagery, physically based lighting shaders, and bespoke motion choreography to articulate value propositions with absolute fidelity. Rather than relying on generic stock footage, every sequence is modeled from the ground up to reflect genuine industrial and commercial standards.</p>
<ul>
    <li><strong>Impact and Clarity:</strong> Distilling complex structural or technical narratives into memorable visual moments.</li>
    <li><strong>Limitless Scalability:</strong> Virtual cameras explore perspectives impossible in physical live-action shoots.</li>
    <li><strong>High Localization ROI:</strong> Assets effortlessly adapt across regional campaigns and technical revisions.</li>
</ul>
"""
                urgency_html = f"""
<h3>Why Is {primary_keyword} Vital for Growth?</h3>
<p>In high-stakes markets across {city_scope}, visual ambiguity directly compromises stakeholder confidence and slows sales cycles. Deploying high-fidelity {primary_keyword} immediately establishes commercial authority, mitigates misunderstanding, and drives measurable engagement across digital touchpoints.</p>
"""
                usp_html = f"""
<h3>{brand_name}: Your Strategic Partner for {service_data['name']}</h3>
<h4>Core Value Proposition</h4>
<p>We blend <strong>Storytelling Mastery</strong> with procedural modeling to ensure that every frame advances your core business narrative rather than merely providing superficial decoration.</p>
<h4>Guaranteed Quality & Delivery</h4>
<p>Every commercial engagement includes our verified <strong>{guarantee}</strong> and <strong>{spec}</strong>, providing complete peace of mind to enterprise partners in {city_scope}.</p>
"""
                education_html = f"""
<h3>Briefs and Communication</h3>
<p>Seamless cross-border production hinges on transparent milestones. Our studio implements cloud-based daily visual dailies, structured review checkpoints, and clear turnaround sprints ensuring clients in {city_scope} maintain full creative direction.</p>
"""
                solutions_items = "".join([f"<li><strong>{s.get('title', 'Solution')}:</strong> {s.get('desc', '')}</li>" for s in sub_solutions]) if sub_solutions else f"<li><strong>Tailored CGI Packages:</strong> Built bespoke for commercial leaders in {city_scope}.</li>"
                solutions_html = f"""
<h3>Specialized Visual Solutions</h3>
<ul>
{solutions_items}
</ul>
"""
                steps_items = "".join([f"<li><strong>Phase {st.get('step', i+1)}: {st.get('title', 'Phase')}</strong> - {st.get('desc', '')}</li>" for i, st in enumerate(production_steps)]) if production_steps else "<li><strong>Pipeline:</strong> Audit, Storyboard, 3D Asset Creation, Post & Sound, Master Delivery.</li>"
                pipeline_html = f"""
<h3>Our Studio Production Pipeline</h3>
<ol>
{steps_items}
</ol>
"""
                modular_html = f"""
<h3>Asset Modularization and Maximum ROI</h3>
<p>Investing in {primary_keyword} extends far beyond a one-off campaign asset. By constructing fully rigged, textured, and shaded 3D geometry in our studio pipeline, your organization acquires an evergreen digital asset repository.</p>
<p>These modular master files can be readily repurposed into vertical 9:16 social shorts, high-resolution print graphics, interactive web viewers, and investor demonstration decks at a fraction of initial production costs.</p>
"""
                cta_html = f"""
<h3>Elevate Your Visual Content Today</h3>
<p>Ready to outpace market competitors and command authority with unmatched 3D clarity? Connect directly with our studio production directors to discuss your scope, request comprehensive portfolio samples, and receive a customized production roadmap tailored to your timeline.</p>
<p style="font-weight: bold; margin-top: 15px;">{tagline}</p>
"""
                faq_items = [
                    {"question": f"What defines professional {primary_keyword}?", "answer": f"It is custom high-fidelity 3D computer graphics tailored to {city_scope} commercial standards, crafted remotely by {brand_name} with photorealistic detail."},
                    {"question": f"What are the primary commercial benefits of {service_data['name']}?", "answer": "It significantly elevates visual comprehension, eliminates costly live filming logistical overhead, and accelerates conversion rates."},
                    {"question": f"How is pricing structured for {city_scope} clients?", "answer": f"Pricing is project-based and highly competitive, offering up to 40% cost savings compared to local {city_scope} agencies while maintaining uncompressed 4K quality."},
                    {"question": f"How does {brand_name} maintain strict brand consistency?", "answer": "We ingest your exact corporate style guides, CAD engineering data, and color palettes during initial previsualization."},
                    {"question": f"Which industries benefit most from {primary_keyword}?", "answer": f"Enterprise technology, heavy mining, civil infrastructure, luxury real estate, and consumer product innovators operating in {city_scope}."},
                    {"question": f"What is the typical production timeline?", "answer": f"Standard production spans {service_data.get('estimated_timeline', '2 to 5 weeks')} from brief signoff to final master delivery."},
                    {"question": f"Can assets be formatted for vertical social media?", "answer": "Yes, our asset modularization workflow exports native 9:16 vertical reels and 1:1 square cutdowns alongside 16:9 widescreen masters."},
                    {"question": f"Are the 3D assets reusable for future campaigns?", "answer": "All 3D models and digital environments are archived in our studio repository, enabling rapid iteration for subsequent product updates."},
                    {"question": f"What deliverable formats are provided?", "answer": f"Deliverables include {service_data.get('deliverable_formats', 'Uncompressed 4K ProRes 422 HQ, web-optimized MP4, and raw transparent PNGs')}."},
                    {"question": f"How do we begin a project with {brand_name}?", "answer": f"Reach out directly through our website consultation portal or initiate an instant project brief with our production coordinators."}
                ]

            faq_html_list = "".join([f"<li><strong>{q['question']}</strong><p>{q['answer']}</p></li>" for q in faq_items])
            faq_html = f"""
<h3>10 Questions and Answers (Q&A)</h3>
<ol>
{faq_html_list}
</ol>
"""

        else:
            # Bahasa Indonesia Version
            if is_software:
                meta_desc = f"{brand_name} menghadirkan {primary_keyword}. Software house berstandar enterprise, performa cepat sub-detik, dan {guarantee}. Konsultasi sekarang!"
                intro_html = f"""
<p>Banyak pelaku usaha, institusi, dan korporasi di kota-kota berkembang seperti {tier1_cities_str} menghadapi tantangan digitalisasi yang nyata: website lama yang lambat diakses, aplikasi bisnis yang sering bermasalah saat trafik tinggi, sistem operasional yang terpecah-pecah tanpa integrasi otomatis, serta vendor pengembang yang sulit dihubungi setelah proyek selesai. Memilih mitra <strong>{primary_keyword}</strong> yang kredibel bukan sekadar membeli baris kode, melainkan investasi strategis demi kelancaran operasional dan akselerasi bisnis jangka panjang.</p>
<p>Berpusat di {hq}, {brand_name} hadir sebagai software house dan mitra rekayasa teknologi terpercaya bagi perusahaan di {city_scope}. Kami merancang arsitektur aplikasi web modern, sistem informasi terintegrasi, dan platform digital berkinerja tinggi yang siap menangani ribuan transaksi secara stabil tanpa kendala teknis.</p>
"""
                def_html = f"""
<h3>Apa yang Mendefinisikan Layanan {service_data['name']} Kami?</h3>
<p>Layanan {service_data['name']} dari {brand_name} dirancang untuk menjawab akar masalah bisnis melalui standar rekayasa perangkat lunak modern yang stabil, aman, dan mudah dikembangkan (*future-proof*).</p>
<ul>
    <li><strong>Waktu Muat Sub-Detik:</strong> Arsitektur frontend modern yang dioptimasi untuk skor Core Web Vitals tertinggi dan ramah algoritma Google.</li>
    <li><strong>Arsitektur Backend Skalabel:</strong> Sistem backend modular berbasis RESTful/GraphQL API yang teruji stabil melayani lonjakan traffic secara konsisten.</li>
    <li><strong>Keamanan Standar Enterprise:</strong> Perlindungan data berlapis, enkripsi SSL/TLS, proteksi injeksi database, dan manajemen hak akses terpusat.</li>
</ul>
"""
                urgency_html = f"""
<h3>Mengapa Solusi {primary_keyword} Sangat Krusial untuk Pertumbuhan Bisnis?</h3>
<p>Di era digital interaktif saat ini, konsumen dan mitra korporat di {city_scope} menuntut kecepatan akses dan keandalan sistem. Layanan {primary_keyword} modern mampu memangkas biaya operasional manual, meningkatkan angka konversi penjualan, serta memberikan keunggulan kompetitif mutlak atas kompetitor industri Anda.</p>
"""
                usp_html = f"""
<h3>{brand_name}: Mitra Rekayasa Software Terpercaya untuk {service_data['name']}</h3>
<h4>Nilai Utama Rekayasa Kami</h4>
<p>Kami tidak sekadar menulis kode; kami menerapkan <strong>Rekayasa Arsitektur Perangkat Lunak Bersih</strong> yang disesuaikan secara presisi dengan alur bisnis unik perusahaan Anda demi efisiensi operasional maksimal.</p>
<h4>Jaminan Kualitas dan Kepemilikan Penuh</h4>
<p>Setiap proyek kami lindungi dengan komitmen <strong>{guarantee}</strong> serta penyerahan <strong>{spec}</strong>, memastikan kepemilikan 100% atas seluruh source code dan hak kekayaan intelektual sistem bagi klien di {city_scope}.</p>
"""
                education_html = f"""
<h3>Transparansi Metodologi Agile dan Manajemen Proyek</h3>
<p>Keberhasilan kolaborasi software jarak jauh bertumpu pada komunikasi yang terstruktur. Tim kami menerapkan sprint mingguan, staging environment terisolasi untuk peninjauan langsung, serta kanal komunikasi responsif agar klien di {city_scope} selalu memegang kendali penuh atas progres pengerjaan.</p>
"""
                solutions_items = "".join([f"<li><strong>{s.get('title', 'Solusi')}:</strong> {s.get('desc', '')}</li>" for s in sub_solutions]) if sub_solutions else f"<li><strong>Aplikasi Web Enterprise:</strong> Sistem berbasis web terintegrasi dengan skalabilitas tinggi untuk perusahaan di {city_scope}.</li>"
                solutions_html = f"""
<h3>Katalog Solusi Teknologi Terpadu</h3>
<ul>
{solutions_items}
</ul>
"""
                steps_items = "".join([f"<li><strong>Tahap {st.get('step', i+1)}: {st.get('title', 'Langkah')}</strong> - {st.get('desc', '')}</li>" for i, st in enumerate(production_steps)]) if production_steps else "<li><strong>Alur Kerja Rekayasa:</strong> Audit Kebutuhan Bisnis, Wireframing UI/UX Figma, Sprint Coding Bersih, Automated Testing & QA, Deployment Cloud & SLA.</li>"
                pipeline_html = f"""
<h3>5 Tahapan Siklus Pengembangan Software Kami</h3>
<ol>
{steps_items}
</ol>
"""
                modular_html = f"""
<h3>Modularitas Kode dan Nilai Investasi (ROI) Jangka Panjang</h3>
<p>Investasi pada {primary_keyword} dari {brand_name} memberikan nilai aset yang terus bertumbuh. Arsitektur modular kami menjamin sistem mudah diperluas di masa depan tanpa harus merombak fondasi dari awal.</p>
<p>Dengan dokumentasi teknis lengkap dan repositori kode terstruktur, tim Anda terbebas dari keterikatan vendor (*vendor lock-in*) serta siap mengintegrasikan modul bisnis baru secara mandiri.</p>
"""
                cta_html = f"""
<h3>Konsultasikan Kebutuhan Sistem & Aplikasi Digital Anda Sekarang</h3>
<p>Diskusikan arsitektur sistem, fitur khusus, dan timeline proyek software Anda bersama tim spesialis teknologi kami hari ini untuk mendapatkan estimasi pengerjaan yang transparan dan tepat sasaran.</p>
<p style="font-weight: bold; margin-top: 15px;">{tagline}</p>
"""
                faq_items = [
                    {"question": f"Apa keunggulan layanan {primary_keyword} dari {brand_name}?", "answer": f"Kombinasi standar software house berstandar enterprise, performa sub-detik, arsitektur bersih, dan biaya transparan bagi perusahaan di {city_scope}."},
                    {"question": f"Apa manfaat utama menggunakan {service_data['name']}?", "answer": "Mengotomasi alur kerja operasional, mempercepat akses data, mengurangi risiko human-error, dan meningkatkan konversi bisnis."},
                    {"question": f"Bagaimana estimasi biaya pengerjaan di {city_scope}?", "answer": "Biaya dihitung secara transparan berbasis ruang lingkup fitur dan arsitektur tanpa biaya tersembunyi."},
                    {"question": f"Siapa pemilik hak cipta dan source code proyek?", "answer": "Klien memegang 100% kepemilikan penuh atas seluruh source code, database, dan aset digital yang telah diserahterimakan."},
                    {"question": f"Teknologi apa saja yang digunakan dalam pengembangan?", "answer": "Kami menggunakan stack modern teruji seperti Next.js, React, Node.js, Python, PostgreSQL, Docker, serta infrastruktur cloud kelas dunia."},
                    {"question": f"Berapa lama rata-rata waktu pengerjaan proyek?", "answer": f"Rata-rata proyek memakan waktu {service_data.get('estimated_timeline', '4 hingga 12 minggu')} tergantung kompleksitas fitur dan integrasi API."},
                    {"question": f"Bagaimana standar keamanan data yang diterapkan?", "answer": "Kami menerapkan protokol OWASP Top 10, enkripsi SSL/TLS, sanitasi input database, dan autentikasi multi-faktor terenkripsi."},
                    {"question": f"Apakah tersedia garansi purna-jual dan maintenance?", "answer": "Ya, setiap proyek dilengkapi garansi perbaikan bug serta opsi layanan SLA pemeliharaan berkala pasca-peluncuran."},
                    {"question": f"Format serah terima apa yang akan diterima klien?", "answer": f"Klien menerima {spec}, akses repositori Git pribadi, dokumentasi arsitektur API, serta sesi pelatihan penggunaan sistem."},
                    {"question": f"Bagaimana cara memulai konsultasi proyek?", "answer": f"Hubungi konsultan teknologi kami secara langsung melalui WhatsApp atau jadwalkan sesi diskusi kebutuhan sistem via website resmi kami."}
                ]

            else:
                meta_desc = f"{brand_name} menghadirkan {primary_keyword} berstandar studio Yogyakarta. Kualitas master 4K, {guarantee}, dan pengerjaan tepat waktu. Hubungi kami!"
                intro_html = f"""
<p>Menjalankan produksi visual konvensional di kota-kota besar seperti {tier1_cities_str} sering kali terbentur tingginya biaya vendor serta keterbatasan peralatan fisik. Di tengah persaingan pasar modern, menghadirkan layanan <strong>{primary_keyword}</strong> yang kredibel membutuhkan sinergi antara keahlian teknis tingkat tinggi dan efisiensi anggaran produksi.</p>
<p>Berpusat di {hq}, {brand_name} hadir sebagai mitra strategis bagi pelaku industri di {city_scope}. Kami menghadirkan studio produksi visual berstandar internasional dengan skema kerja jarak jauh yang terbukti memangkas biaya operasional tanpa mengurangi sedikit pun kualitas estetika maupun ketelitian teknis.</p>
"""
                def_html = f"""
<h3>Apa yang Mendefinisikan {service_data['name']}?</h3>
<p>Secara esensial, layanan {service_data['name']} menggabungkan pemodelan digital presisi, simulasi fisika canggih, dan sinkronisasi audio terpadu untuk menyampaikan pesan bisnis secara jelas dan memukau.</p>
<ul>
    <li><strong>Dampak Visual Kuat:</strong> Memvisualisasikan konsep rumit menjadi tayangan yang langsung dimengerti audiens.</li>
    <li><strong>Skalabilitas Tanpa Batas:</strong> Sudut pandang kamera bebas mengeksplorasi dimensi yang mustahil diambil kamera manual.</li>
    <li><strong>Efisiensi Jangka Panjang:</strong> Aset digital master dapat digunakan berulang kali untuk berbagai kebutuhan promosi.</li>
</ul>
"""
                urgency_html = f"""
<h3>Mengapa {primary_keyword} Sangat Krusial untuk Pertumbuhan Bisnis?</h3>
<p>Di era digital interaktif saat ini, konsumen dan mitra korporat di {city_scope} menuntut transparansi dan bukti visual nyata. Layanan {primary_keyword} mampu meningkatkan kredibilitas brand, mempercepat pengambilan keputusan klien, dan memperkuat posisi tawar bisnis Anda di pasar.</p>
"""
                usp_html = f"""
<h3>{brand_name}: Mitra Terbaik Anda untuk {service_data['name']}</h3>
<h4>Nilai Utama Layanan Kami</h4>
<p>Kami tidak sekadar memproduksi visual; kami meramu <strong>Penguasaan Cerita</strong> yang menyatu dengan target bisnis Anda agar setiap detik tayangan memberikan dampak nyata bagi penonton.</p>
<h4>Jaminan Kualitas dan Kepastian Hasil</h4>
<p>Setiap proyek kami lindungi dengan komitmen <strong>{guarantee}</strong> serta penyediaan <strong>{spec}</strong> demi kepuasan mutlak klien kami di {city_scope}.</p>
"""
                education_html = f"""
<h3>Briefing dan Komunikasi Terbuka</h3>
<p>Keberhasilan produksi jarak jauh bertumpu pada komunikasi yang terstruktur. Tim kami menerapkan sistem pelaporan berkala pada setiap tahapan kerja agar klien di {city_scope} selalu memegang kendali penuh atas jalannya proyek.</p>
"""
                solutions_items = "".join([f"<li><strong>{s.get('title', 'Solusi')}:</strong> {s.get('desc', '')}</li>" for s in sub_solutions]) if sub_solutions else f"<li><strong>Solusi Kustom:</strong> Dirancang khusus untuk kebutuhan industri di {city_scope}.</li>"
                solutions_html = f"""
<h3>Katalog Solusi Visual Terpadu</h3>
<ul>
{solutions_items}
</ul>
"""
                steps_items = "".join([f"<li><strong>Tahap {st.get('step', i+1)}: {st.get('title', 'Langkah')}</strong> - {st.get('desc', '')}</li>" for i, st in enumerate(production_steps)]) if production_steps else "<li><strong>Alur Kerja:</strong> Riset, Storyboard, Produksi 3D, Audio Compositing, dan Final Render.</li>"
                pipeline_html = f"""
<h3>Alur Kerja Produksi Studio Kami</h3>
<ol>
{steps_items}
</ol>
"""
                modular_html = f"""
<h3>Modularitas Aset dan Nilai Investasi (ROI)</h3>
<p>Investasi pada {primary_keyword} memiliki nilai guna jangka panjang. Seluruh file master 3D yang dibangun dalam pipeline studio kami tersimpan secara aman dalam format modular.</p>
<p>Aset ini dapat dialihfungsikan menjadi konten media sosial vertikal, materi cetak beresolusi tinggi, hingga materi presentasi investor tanpa harus membayar biaya produksi dari awal.</p>
"""
                cta_html = f"""
<h3>Tingkatkan Kualitas Konten Visual Anda Sekarang</h3>
<p>Konsultasikan kebutuhan visual dan target proyek Anda bersama tim spesialis produksi kami hari ini untuk mendapatkan estimasi pengerjaan serta rancangan konsep terbaik.</p>
<p style="font-weight: bold; margin-top: 15px;">{tagline}</p>
"""
                faq_items = [
                    {"question": f"Apa keunggulan {primary_keyword} dari {brand_name}?", "answer": f"Kombinasi kualitas visual tingkat tinggi berstandar studio Yogyakarta dengan harga yang sangat kompetitif bagi pelaku usaha di {city_scope}."},
                    {"question": f"Apa manfaat utama menggunakan {service_data['name']}?", "answer": "Meningkatkan daya pikat visual, memperjelas informasi teknis secara instan, dan menaikkan angka konversi penjualan."},
                    {"question": f"Bagaimana estimasi biaya pengerjaan di {city_scope}?", "answer": "Biaya disesuaikan dengan tingkat kerumitan konsep dan durasi, dengan skema penawaran transparan tanpa biaya tersembunyi."},
                    {"question": f"Bagaimana {brand_name} memastikan kepatuhan pada identitas brand klien?", "answer": "Kami menerapkan pedoman visual dan warna resmi perusahaan klien secara ketat sejak tahap pembuatan storyboard."},
                    {"question": f"Sektor industri apa saja yang cocok menggunakan layanan ini?", "answer": f"Korporasi, institusi pendidikan, industri manufaktur, perhotelan, pariwisata, hingga pelaku bisnis di {city_scope}."},
                    {"question": f"Berapa lama waktu pengerjaan proyek?", "answer": f"Rata-rata proyek memakan waktu {service_data.get('estimated_timeline', '2 hingga 5 minggu')} hingga serah terima master."},
                    {"question": f"Apakah hasil video bisa disesuaikan untuk format media sosial?", "answer": "Tentu, kami menyediakan format rasio vertikal 9:16 untuk Reels/TikTok dan rasio 16:9 untuk presentasi serta YouTube."},
                    {"question": f"Apakah aset visual dapat digunakan kembali di masa depan?", "answer": "Ya, seluruh model master 3D diarsipkan dan dapat diperbarui sewaktu-waktu untuk kampanye berikutnya."},
                    {"question": f"Format file apa yang akan diterima klien?", "answer": f"Klien menerima master video resolusi tinggi {spec} beserta file web-ready."},
                    {"question": f"Bagaimana cara memulai pemesanan layanan?", "answer": f"Hubungi tim produksi kami secara langsung melalui formulir kontak di website untuk mendiskusikan jadwal dan konsep visual Anda."}
                ]

            faq_html_list = "".join([f"<li><strong>{q['question']}</strong><p>{q['answer']}</p></li>" for q in faq_items])
            faq_html = f"""
<h3>10 Pertanyaan dan Jawaban (Q&A)</h3>
<ol>
{faq_html_list}
</ol>
"""

        # Assemble full content
        full_content_html = f"{intro_html}\n{def_html}\n{urgency_html}\n{usp_html}\n{education_html}\n{solutions_html}\n{pipeline_html}\n{modular_html}\n{cta_html}\n{faq_html}"

        return {
            "meta_description": meta_desc,
            "content_html": full_content_html,
            "faq_items": faq_items,
            "structured_sections": {
                "intro": intro_html,
                "definition": def_html,
                "urgency": urgency_html,
                "usp": usp_html,
                "education": education_html,
                "solutions": solutions_html,
                "pipeline": pipeline_html,
                "modular": modular_html,
                "cta": cta_html,
                "faq": faq_html
            }
        }

    def _generate_with_router(
        self,
        brand_data: Dict[str, Any],
        service_data: Dict[str, Any],
        location_data: Dict[str, Any],
        city_scope: str,
        primary_keyword: str,
        title: str,
        is_english: bool,
        sub_keywords: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Calls LLM Router (9router / OpenRouter) using the selected dynamic model with Problem-Solving focus."""
        sub_kw_str = ", ".join(sub_keywords)
        lang_str = "English" if is_english else "Bahasa Indonesia"
        industry = brand_data.get("industry_focus", "Technology & Software")
        pain_points_str = ", ".join(brand_data.get("core_pain_points", [])) if brand_data.get("core_pain_points") else "Sistem manual lambat, website performa rendah, kendala integrasi data, vendor tidak responsif"
        solutions_str = ", ".join(brand_data.get("core_solutions", [])) if brand_data.get("core_solutions") else "Arsitektur modern skalabel, optimasi kecepatan, integrasi API, jaminan garansi purna-jual"

        prompt = f"""
You are an expert Programmatic Local SEO and Generative Engine Optimization (GEO) copywriter.
Generate an authoritative, problem-solving landing page article in {lang_str}.

BRAND CONTEXT:
- Brand Name: {brand_data['name']} (HQ: {brand_data.get('hq_location', 'Yogyakarta, Indonesia')})
- Industry: {industry}
- Service Name: {service_data['name']}
- Primary Keyword: {primary_keyword}
- Target Location: {city_scope}
- Brand Voice: {brand_data.get('brand_voice', 'Professional, Solutif, Authoritative, Enterprise')}
- Client Pain Points Solved: {pain_points_str}
- Core Solutions Offered: {solutions_str}
- Revision Guarantee: {brand_data.get('revision_guarantee', 'Free 2x revision guarantee')}
- Master Deliverable Spec: {brand_data.get('master_output_spec', 'Full Source Code & Production Master')}
- CTA Tagline: {brand_data.get('cta_tagline', 'Solusi digital terpercaya untuk pertumbuhan bisnis Anda.')}

CONTENT FOCUS (CRITICAL FOR REAL VALUE & HIGH CONVERSION):
1. Focus directly on PROBLEM-SOLVING. Identify the real operational bottlenecks, technical frustrations, or business losses that companies in {city_scope} face when searching for {service_data['name']}.
2. Explain specifically how {brand_data['name']} solves these pain points through modern engineering, clean architecture, responsive communication, and dependable technical guarantees.
3. Provide a transparent 5-phase delivery process (Discovery, UI/UX Architecture, Agile Development/Production, Testing & Quality Assurance, Deployment & SLA).
4. Demonstrate clear business ROI (hours saved, latency reduction, security compliance, increased conversion).
5. Strictly avoid writing fake portfolio stories or fabricating unverified client names. Focus on methodology, architecture, and business benefits.

STRICT CONSTRAINTS (MANDATORY):
1. NO EMAIL ADDRESSES: Never write any email address (e.g. info@, contact@) in the CTA or in FAQ #10.
2. In English articles, under every H3 header, place: '*Keyword Subjudul: {sub_kw_str}*' in italics.
3. EXACTLY 10 FAQ items in the FAQ section addressing definition, benefits, pricing structure, brand consistency, industry use cases, timeline, maintenance, source code ownership, technical security, and how to begin consultation.
4. Meta description must be under 160 characters.

Return VALID JSON ONLY with this structure:
{{
  "meta_description": "concise problem-solving meta description under 160 chars",
  "content_html": "<p>Intro paragraph 1 identifying pain points and <strong>{primary_keyword}</strong>...</p><h3>What Defines...</h3>...",
  "faq_items": [
    {{"question": "Q1", "answer": "A1"}},
    {{"question": "Q2", "answer": "A2"}},
    {{"question": "Q3", "answer": "A3"}},
    {{"question": "Q4", "answer": "A4"}},
    {{"question": "Q5", "answer": "A5"}},
    {{"question": "Q6", "answer": "A6"}},
    {{"question": "Q7", "answer": "A7"}},
    {{"question": "Q8", "answer": "A8"}},
    {{"question": "Q9", "answer": "A9"}},
    {{"question": "Q10", "answer": "A10 without email address"}}
  ]
}}
"""
        messages = [
            {"role": "system", "content": "You are a professional SEO copywriter. Always output pure JSON without markdown explanation."},
            {"role": "user", "content": prompt}
        ]

        target_model = self.router.config.get("selected_model", "ox-alpha")
        try:
            raw_output = self.router.generate_chat_completion(messages, model=target_model)
            if raw_output:
                clean_json = raw_output.strip()
                if clean_json.startswith("```"):
                    clean_json = re.sub(r'^```(?:json)?\s*', '', clean_json)
                    clean_json = re.sub(r'\s*```$', '', clean_json)
                clean_json = clean_json.strip()
                
                parsed = json.loads(clean_json)
                if "content_html" in parsed:
                    logger.info(f"[GEOWriter] Successfully generated via Router ({target_model})")
                    parsed["ai_generated"] = True
                    parsed["model_used"] = target_model
                    return parsed
        except Exception as e:
            logger.warning(f"[GEOWriter] Router generation exception ({target_model}): {e}")

        return None

    def _generate_with_gemini(
        self,
        brand_data: Dict[str, Any],
        service_data: Dict[str, Any],
        location_data: Dict[str, Any],
        city_scope: str,
        primary_keyword: str,
        title: str,
        is_english: bool,
        sub_keywords: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Calls Google Gemini API using the user's active key with auto-rotation."""
        sub_kw_str = ", ".join(sub_keywords)
        lang_str = "English" if is_english else "Bahasa Indonesia"

        prompt = f"""
You are an expert Programmatic Local SEO and Generative Engine Optimization (GEO) copywriter.
Generate a structured, high-conversion landing page article in {lang_str}.

PARAMETERS:
- Brand: {brand_data['name']} (HQ: {brand_data.get('hq_location', 'Yogyakarta, Indonesia')})
- Service: {service_data['name']}
- Primary Keyword: {primary_keyword}
- Target Location: {city_scope}
- Sub-Keywords to mention: {sub_kw_str}
- Revision Guarantee: {brand_data.get('revision_guarantee', 'Free 2x revision guarantee')}
- Master Spec: {brand_data.get('master_output_spec', 'Uncompressed 4K master files')}
- CTA Tagline: {brand_data.get('cta_tagline', '🎥 Bringing your vision to life.')}

STRICT CONSTRAINTS (CRITICAL):
1. NO EMAIL ADDRESSES: Never write any email address (like info@ or contact@) in the CTA or in FAQ #10.
2. In English articles, under every H3 header, place: '*Keyword Subjudul: {sub_kw_str}*' in italics.
3. EXACTLY 10 FAQ items in the FAQ section addressing definition, benefits, pricing, brand consistency, industries, timeline, social media formats, reusability, file formats, and how to start.
4. Meta description must be under 160 characters.

Return VALID JSON ONLY with this structure:
{{
  "meta_description": "concise meta under 160 chars",
  "content_html": "<p>Intro paragraph 1 with <strong>{primary_keyword}</strong>...</p><h3>What Defines...</h3>...",
  "faq_items": [
    {{"question": "Q1", "answer": "A1"}},
    {{"question": "Q2", "answer": "A2"}},
    {{"question": "Q3", "answer": "A3"}},
    {{"question": "Q4", "answer": "A4"}},
    {{"question": "Q5", "answer": "A5"}},
    {{"question": "Q6", "answer": "A6"}},
    {{"question": "Q7", "answer": "A7"}},
    {{"question": "Q8", "answer": "A8"}},
    {{"question": "Q9", "answer": "A9"}},
    {{"question": "Q10", "answer": "A10 without email"}}
  ]
}}
"""
        max_attempts = max(1, len(self.gemini.auth.accounts))
        models_to_try = [self.model, "gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        # De-duplicate while preserving order
        models_to_try = list(dict.fromkeys(models_to_try))

        for model in models_to_try:
            for _ in range(max_attempts):
                auth_info = self.gemini.auth.get_active_auth_headers_or_param()
                if not auth_info:
                    break
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                headers = {"Content-Type": "application/json"}
                headers.update(auth_info.get("headers", {}))
                params = auth_info.get("param", {})

                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.5,
                        "responseMimeType": "application/json"
                    }
                }

                try:
                    resp = requests.post(url, headers=headers, params=params, json=payload, timeout=25)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and "text" in parts[0]:
                                raw_text = parts[0]["text"].strip()
                                # Clean markdown JSON wrappers if present
                                if raw_text.startswith("```"):
                                    raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
                                    raw_text = re.sub(r'\s*```$', '', raw_text)
                                raw_text = raw_text.strip()
                                parsed = json.loads(raw_text)
                                if "content_html" in parsed:
                                    logger.info(f"[GEOWriter] Successfully generated via user Gemini account ({model})")
                                    parsed["ai_generated"] = True
                                    parsed["model_used"] = model
                                    return parsed
                    elif resp.status_code in [429, 403]:
                        logger.warning(f"[GEOWriter] Gemini quota/auth hit on {model}. Rotating account...")
                        self.gemini.auth.rotate()
                    else:
                        logger.warning(f"[GEOWriter] Gemini API error ({resp.status_code}) on {model}: {resp.text[:150]}")
                        self.gemini.auth.rotate()
                except Exception as e:
                    logger.warning(f"[GEOWriter] Gemini request exception on {model}: {e}")
                    self.gemini.auth.rotate()

        return None

        return None
