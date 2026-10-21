import re
import json
from typing import List, Dict, Any, Optional

class LinkInjector:
    """
    Contextual Internal Link Siloing & JSON-LD Schema Engine.
    - Injects 3-5 natural contextual internal links into body paragraphs.
    - Replaces spammy hidden links with an official 'Explore Our Regional Solutions' directory block.
    - Generates Schema.org JSON-LD (FAQPage + Service/LocalBusiness).
    """

    def __init__(self, max_body_links: int = 4):
        self.max_body_links = max_body_links

    def inject_all(
        self,
        html_content: str,
        brand_data: Dict[str, Any],
        service_data: Dict[str, Any],
        target_location: str,
        faq_items: List[Dict[str, str]],
        related_articles: Optional[List[Dict[str, Any]]] = None,
        include_schema: bool = True
    ) -> str:
        """
        Processes an HTML article to inject contextual links, official silo directory, and JSON-LD schema.
        """
        # 1. Inject contextual anchor links in paragraphs
        processed_html = self.inject_in_content_links(
            html_content=html_content,
            brand_data=brand_data,
            service_data=service_data,
            related_articles=related_articles or []
        )

        # 2. Append official Explore Our Regional Solutions block
        silo_block = self.build_explore_silo_block(
            brand_data=brand_data,
            service_data=service_data,
            target_location=target_location,
            related_articles=related_articles or []
        )
        processed_html += f"\n\n{silo_block}"

        # 3. Append JSON-LD schema if requested
        if include_schema and faq_items:
            schema_script = self.build_json_ld_schema(
                brand_data=brand_data,
                service_data=service_data,
                target_location=target_location,
                faq_items=faq_items
            )
            processed_html += f"\n\n{schema_script}"

        return processed_html

    def inject_in_content_links(
        self,
        html_content: str,
        brand_data: Dict[str, Any],
        service_data: Dict[str, Any],
        related_articles: List[Dict[str, Any]]
    ) -> str:
        """
        Injects 3 to 5 contextual internal links directly into paragraph tags (<p>...</p>).
        Avoids headings (H1-H6), existing links (<a >), and code blocks.
        """
        links_added = 0
        used_anchors = set()

        # Link candidates:
        # 1. Brand Service Pillar Page
        pillar_url = service_data.get("pillar_url")
        anchor_variations = service_data.get("anchor_variations", [])
        if isinstance(anchor_variations, str):
            anchor_variations = json.loads(anchor_variations or "[]")

        link_candidates = []
        if pillar_url and anchor_variations:
            for anchor in anchor_variations:
                link_candidates.append({
                    "url": pillar_url,
                    "anchor": anchor,
                    "type": "pillar"
                })

        # 2. Related Articles
        for art in related_articles:
            art_url = art.get("published_url") or f"{brand_data.get('domain_url', '')}/{art.get('slug', '')}/"
            art_kw = art.get("primary_keyword") or art.get("title")
            if art_url and art_kw:
                link_candidates.append({
                    "url": art_url,
                    "anchor": art_kw,
                    "type": "cluster"
                })

        if not link_candidates:
            return html_content

        # Split content into paragraphs and headers to only modify <p> blocks
        p_pattern = re.compile(r'(<p[^>]*>)(.*?)(</p>)', re.DOTALL | re.IGNORECASE)

        def replace_paragraph(match):
            nonlocal links_added
            if links_added >= self.max_body_links:
                return match.group(0)

            opening_tag = match.group(1)
            p_text = match.group(2)
            closing_tag = match.group(3)

            # Skip paragraphs that already have anchor tags
            if '<a ' in p_text.lower():
                return match.group(0)

            # Try to match a link candidate
            for cand in link_candidates:
                if links_added >= self.max_body_links:
                    break
                anchor = cand["anchor"]
                url = cand["url"]

                if anchor.lower() in used_anchors:
                    continue

                # Case-insensitive word boundary match
                pattern = re.compile(rf'\b({re.escape(anchor)})\b', re.IGNORECASE)
                if pattern.search(p_text):
                    # Replace only first occurrence in this paragraph
                    p_text = pattern.sub(rf'<a href="{url}" title="\1">\1</a>', p_text, count=1)
                    used_anchors.add(anchor.lower())
                    links_added += 1
                    break

            return f"{opening_tag}{p_text}{closing_tag}"

        return p_pattern.sub(replace_paragraph, html_content)

    def build_explore_silo_block(
        self,
        brand_data: Dict[str, Any],
        service_data: Dict[str, Any],
        target_location: str,
        related_articles: List[Dict[str, Any]]
    ) -> str:
        """
        Builds the compliant 'Explore Our Regional & Specialized Solutions' component.
        Presents 6-10 hub links cleanly in a responsive grid.
        """
        brand_name = brand_data.get("name", "Studio")
        service_name = service_data.get("name", "Services")
        domain = brand_data.get("domain_url", "https://unimasi.com").rstrip("/")
        pillar_url = service_data.get("pillar_url", f"{domain}/services/")

        items_html = []
        
        # 1. Pillar link
        items_html.append(
            f'<li><a href="{pillar_url}" style="color: #2563eb; text-decoration: none; font-weight: 500;">'
            f'Master Overview: {service_name} Hub & Pipeline &rarr;</a></li>'
        )

        # 2. Articles in this cluster or other locations
        count = 0
        for art in related_articles:
            if count >= 8:
                break
            art_title = art.get("title") or art.get("primary_keyword", "")
            art_url = art.get("published_url") or f"{domain}/{art.get('slug', '')}/"
            items_html.append(
                f'<li><a href="{art_url}" style="color: #4b5563; text-decoration: none;">'
                f'{art_title}</a></li>'
            )
            count += 1

        # Dynamic fallback items if database has few published articles yet: link to brand's actual services & location overview
        if len(items_html) < 4:
            brand_services = brand_data.get("services", [])
            for s in brand_services:
                s_name = s.get("name") if isinstance(s, dict) else str(s)
                s_url = s.get("pillar_url", f"{domain}/services/") if isinstance(s, dict) else f"{domain}/services/"
                if s_name and s_name.lower() != service_name.lower() and len(items_html) < 6:
                    items_html.append(
                        f'<li><a href="{s_url}" style="color: #4b5563; text-decoration: none;">'
                        f'{s_name} Overview & Case Studies</a></li>'
                    )

            if len(items_html) < 4:
                items_html.append(
                    f'<li><a href="{pillar_url}" style="color: #4b5563; text-decoration: none;">'
                    f'Client Case Studies in {target_location} & Global Portfolio</a></li>'
                )

        list_items = "\n      ".join(items_html)

        html = f"""<!-- GEO Contextual Silo Directory -->
<div class="geo-silo-directory" style="margin-top: 48px; padding: 24px 28px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <h3 style="margin-top: 0; margin-bottom: 8px; font-size: 1.25rem; font-weight: 700; color: #0f172a;">
    Explore Our Regional & Specialized {service_name} Solutions
  </h3>
  <p style="margin-top: 0; margin-bottom: 16px; font-size: 0.95rem; color: #64748b; line-height: 1.5;">
    {brand_name} delivers end-to-end remote production pipelines for global partners. Discover regional case studies, production frameworks, and specialized solutions:
  </p>
  <ul style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; padding-left: 20px; margin: 0; font-size: 0.95rem;">
      {list_items}
  </ul>
</div>"""
        return html

    def build_json_ld_schema(
        self,
        brand_data: Dict[str, Any],
        service_data: Dict[str, Any],
        target_location: str,
        faq_items: List[Dict[str, str]]
    ) -> str:
        """
        Constructs Schema.org JSON-LD structured data for FAQPage and Service/LocalBusiness.
        """
        brand_name = brand_data.get("name", "Studio")
        domain = brand_data.get("domain_url", "https://unimasi.com").rstrip("/")
        hq = brand_data.get("hq_location", "Yogyakarta, Indonesia")
        service_name = service_data.get("name", "Production Service")
        pillar_url = service_data.get("pillar_url", f"{domain}/services/")

        # Build FAQ mainEntity list
        faq_entities = []
        for item in faq_items[:10]:
            q = item.get("question", "").strip()
            a = item.get("answer", "").strip()
            if q and a:
                faq_entities.append({
                    "@type": "Question",
                    "name": q,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": a
                    }
                })

        schema_payload = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "FAQPage",
                    "mainEntity": faq_entities
                },
                {
                    "@type": "ProfessionalService",
                    "@id": f"{domain}/#organization",
                    "name": brand_name,
                    "url": domain,
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": hq.split(",")[0].strip(),
                        "addressCountry": "ID"
                    },
                    "areaServed": {
                        "@type": "Place",
                        "name": target_location
                    },
                    "hasOfferCatalog": {
                        "@type": "OfferCatalog",
                        "name": f"{brand_name} Visual Solutions",
                        "itemListElement": [
                            {
                                "@type": "Offer",
                                "itemOffered": {
                                    "@type": "Service",
                                    "name": service_name,
                                    "url": pillar_url,
                                    "description": f"Specialized remote {service_name} services for {target_location} by {brand_name}."
                                }
                            }
                        ]
                    }
                }
            ]
        }

        json_str = json.dumps(schema_payload, indent=2, ensure_ascii=False)
        return f'<script type="application/ld+json">\n{json_str}\n</script>'
