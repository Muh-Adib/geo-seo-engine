import os
import re
import json
import base64
import logging
import requests
from io import BytesIO
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

from core.gemini_auth import GeminiAuthManager

logger = logging.getLogger("gemini_generator")

class GeminiMultiAccountEngine:
    """
    Multi-Account Google Gemini & Visual Asset Engine.
    - Connects directly to Google Gemini user accounts (including Antigravity Desktop sessions).
    - Supports multi-account rotation for high throughput and rate-limit bypass.
    - Builds industry-specific problem-solving prompts (Software House, Video, Drone, Enterprise).
    - Generates 16:9 featured thumbnails with Brand Logo watermarking.
    - Fallback to high-aesthetic typography engine (Pillow) with real logo compositing so generation never fails.
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(os.path.join(self.output_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "assets"), exist_ok=True)
        self.auth = GeminiAuthManager()

    def get_brand_asset_dir(self, brand_id: Optional[str] = None) -> str:
        """Returns dedicated asset directory for a brand: output/assets/{brand_id}/images/"""
        if brand_id:
            target_dir = os.path.join(self.output_dir, "assets", brand_id, "images")
        else:
            target_dir = os.path.join(self.output_dir, "images")
        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    def get_brand_asset_url(self, brand_id: Optional[str], filename: str) -> str:
        """Returns web-accessible relative URL for an asset."""
        if brand_id:
            return f"/output/assets/{brand_id}/images/{filename}"
        return f"/output/images/{filename}"

    def get_accounts_summary(self) -> Dict[str, Any]:
        """Returns connected accounts summary."""
        return self.auth.get_accounts_summary()

    def add_account(self, email: str, credential: str, auth_type: str = "api_key") -> Dict[str, Any]:
        return self.auth.add_account(email, credential, auth_type)

    def remove_account(self, account_id: str) -> bool:
        return self.auth.remove_account(account_id)

    def build_industry_prompt(
        self,
        service_name: str,
        location: str,
        brand_name: str,
        industry: Optional[str] = None
    ) -> str:
        """
        Builds a tailored, problem-solving visual prompt for commercial AI image generation.
        Avoids generic or irrelevant objects; targets the brand's actual product/service.
        """
        ind = (industry or "").lower()
        srv = service_name.lower()

        if any(w in ind or w in srv for w in ["software", "web", "aplikasi", "it", "code", "app", "dev", "sistem", "erp"]):
            return (
                f"Modern high-tech enterprise software development studio visual for {service_name} in {location}. "
                f"Sleek clean developer workstation, dual monitors displaying futuristic glassmorphism UI/UX code and cloud architecture, "
                f"subtle ambient cyan and violet LED lighting, 3D isometric cloud server network graphics, 8k commercial quality, "
                f"created for {brand_name}, professional technology showcase."
            )
        elif any(w in ind or w in srv for w in ["drone", "lidar", "mapping", "pemetaan", "survey"]):
            return (
                f"Professional industrial LiDAR aerial survey drone scanning urban infrastructure in {location}. "
                f"High-altitude precision photogrammetry, 8K volumetric lighting, topographical digital twin grid overlay, "
                f"clean modern engineering aesthetic by {brand_name}."
            )
        elif any(w in ind or w in srv for w in ["video", "film", "animasi", "3d", "motion", "creative"]):
            return (
                f"Cinematic 8K commercial film production studio setup for {service_name} in {location}. "
                f"High-end cinema camera on robotic arm, softbox master lighting, clean studio set, anamorphic lens flares, "
                f"award-winning color grading by {brand_name}."
            )
        else:
            return (
                f"Ultra-modern premium enterprise B2B service visual for {service_name} in {location}. "
                f"Architectural glass office, executive strategy board, sleek minimalist tech aesthetic, "
                f"award winning commercial design by {brand_name}, 8k resolution."
            )

    def generate_featured_thumbnail(
        self,
        title: str,
        service_name: str,
        brand_name: str,
        location: str,
        slug: str,
        logo_url: Optional[str] = None,
        industry: Optional[str] = None,
        brand_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a 16:9 (1200x675) featured thumbnail for WordPress.
        Overlays brand logo and uses industry-appropriate problem-solving visual aesthetic.
        Saves into dedicated per-site asset directory when brand_id is specified.
        """
        filename = f"thumb-{slug[:35]}.jpg"
        target_dir = self.get_brand_asset_dir(brand_id)
        filepath = os.path.join(target_dir, filename)
        file_url = self.get_brand_asset_url(brand_id, filename)

        prompt = self.build_industry_prompt(
            service_name=service_name,
            location=location,
            brand_name=brand_name,
            industry=industry
        )

        # 1. Try Imagen generation using user Gemini accounts / Antigravity session
        attempts = max(1, len(self.auth.accounts))
        for _ in range(attempts):
            auth_info = self.auth.get_active_auth_headers_or_param()
            if not auth_info:
                break

            headers = {"Content-Type": "application/json"}
            headers.update(auth_info.get("headers", {}))
            params = auth_info.get("param", {})

            url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"
            payload = {
                "instances": [{"prompt": prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": "16:9",
                    "personGeneration": "ALLOW_ADULT"
                }
            }

            try:
                resp = requests.post(url, headers=headers, params=params, json=payload, timeout=22)
                if resp.status_code == 200:
                    data = resp.json()
                    predictions = data.get("predictions", [])
                    if predictions and "bytesBase64Encoded" in predictions[0]:
                        raw_bytes = base64.b64decode(predictions[0]["bytesBase64Encoded"])
                        base_img = Image.open(BytesIO(raw_bytes)).convert("RGB")
                        base_img = base_img.resize((1200, 675), Image.Resampling.LANCZOS)
                        
                        # Overlay Logo onto Imagen output
                        final_img = self._composite_branding(base_img, brand_name, location, logo_url, title)
                        final_img.save(filepath, "JPEG", quality=92)

                        with open(filepath, "rb") as f:
                            b64_res = base64.b64encode(f.read()).decode("utf-8")

                        logger.info(f"[GeminiEngine] Successfully generated branded Imagen thumbnail: {filepath}")
                        return {
                            "success": True,
                            "source": "gemini_imagen_3",
                            "file_path": filepath,
                            "file_url": file_url,
                            "url": file_url,
                            "brand_id": brand_id,
                            "filename": filename,
                            "base64_data": b64_res,
                            "alt_text": f"{service_name} in {location} - {brand_name}",
                            "caption": f"Professional solution for {service_name} {location} by {brand_name}."
                        }
                elif resp.status_code in [429, 403]:
                    logger.warning("[GeminiEngine] Quota hit on active user account. Rotating...")
                    self.auth.rotate()
                else:
                    self.auth.rotate()
            except Exception as e:
                logger.warning(f"[GeminiEngine] Imagen request error: {e}")
                self.auth.rotate()

        # 2. Resilient Studio Aesthetic Canvas Generator (Pillow Fallback with Logo)
        self._build_studio_canvas(
            filepath=filepath,
            title=title,
            brand_name=brand_name,
            location=location,
            service_name=service_name,
            logo_url=logo_url,
            industry=industry
        )

        with open(filepath, "rb") as f:
            b64_canvas = base64.b64encode(f.read()).decode("utf-8")

        return {
            "success": True,
            "source": "studio_canvas_fallback",
            "file_path": filepath,
            "file_url": file_url,
            "url": file_url,
            "brand_id": brand_id,
            "filename": filename,
            "base64_data": b64_canvas,
            "alt_text": f"{service_name} {location} - {brand_name}",
            "caption": f"Professional visual for {service_name} {location}."
        }

    def _composite_branding(
        self,
        base_img: Image.Image,
        brand_name: str,
        location: str,
        logo_url: Optional[str] = None,
        title: Optional[str] = None
    ) -> Image.Image:
        """Composites logo and glassmorphism badge over an image."""
        width, height = base_img.size
        draw = ImageDraw.Draw(base_img)

        # Header Pill Left (Location & Tag)
        draw.rounded_rectangle([(40, 40), (min(width - 40, 450), 90)], radius=12, fill=(15, 23, 42))
        draw.text((55, 55), f"✦ {brand_name.upper()}  •  {location.upper()}", fill=(241, 245, 249))

        # Brand Logo on Top Right
        self._draw_logo_on_canvas(base_img, logo_url, brand_name, width, height)
        return base_img

    def _draw_logo_on_canvas(
        self,
        canvas: Image.Image,
        logo_url: Optional[str],
        brand_name: str,
        width: int,
        height: int
    ):
        """Draws logo image or high-res typography badge on top right."""
        logo_placed = False

        if logo_url and logo_url.strip():
            logo_clean = logo_url.strip()
            try:
                logo_img = None
                if logo_clean.startswith("http://") or logo_clean.startswith("https://"):
                    resp = requests.get(logo_clean, timeout=5)
                    if resp.status_code == 200:
                        logo_img = Image.open(BytesIO(resp.content))
                else:
                    candidates = [
                        logo_clean,
                        logo_clean.lstrip("/"),
                        os.path.join(self.base_output_dir, "..", logo_clean.lstrip("/")),
                        os.path.join(self.base_output_dir, logo_clean.lstrip("/")),
                        os.path.join(os.getcwd(), logo_clean.lstrip("/"))
                    ]
                    for cand in candidates:
                        if os.path.exists(cand) and os.path.isfile(cand):
                            logo_img = Image.open(cand)
                            break

                if logo_img:
                    logo_img = logo_img.convert("RGBA")
                    max_w, max_h = 220, 60
                    logo_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                    
                    lw, lh = logo_img.size
                    box_x1 = width - lw - 60
                    box_y1 = 35
                    box_x2 = width - 40
                    box_y2 = box_y1 + lh + 20

                    # Draw sleek glass backdrop for logo
                    overlay = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
                    draw_o = ImageDraw.Draw(overlay)
                    draw_o.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=12, fill=(15, 23, 42, 220), outline=(99, 102, 241, 180), width=1)
                    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB"))
                    
                    # Paste logo with alpha mask
                    canvas.paste(logo_img, (box_x1 + 10, box_y1 + 10), mask=logo_img.split()[3])
                    logo_placed = True
            except Exception as e:
                logger.warning(f"Could not composite logo image: {e}")

        if not logo_placed:
            draw = ImageDraw.Draw(canvas)
            badge_text = f"  💎 {brand_name.upper()}  "
            badge_x2 = width - 40
            badge_x1 = max(width - 280, 0)
            draw.rounded_rectangle([(badge_x1, 40), (badge_x2, 90)], radius=12, fill=(30, 27, 75), outline=(99, 102, 241), width=1)
            draw.text((badge_x1 + 18, 55), badge_text, fill=(248, 250, 252))

    def _build_studio_canvas(
        self,
        filepath: str,
        title: str,
        brand_name: str,
        location: str,
        service_name: str,
        logo_url: Optional[str] = None,
        industry: Optional[str] = None
    ):
        """
        Creates a high-end, 16:9 (1200x675) studio thumbnail with typography,
        dark modern gradient, badge pills, problem-solving accents, and brand logo.
        """
        width, height = 1200, 675
        img = Image.new("RGB", (width, height), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)

        # Ambient Gradient
        for y in range(height):
            ratio = y / height
            r = int(15 + (12 * ratio))
            g = int(23 + (15 * ratio))
            b = int(42 + (40 * ratio))
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Decorative glowing borders
        draw.rounded_rectangle([(30, 30), (width - 30, height - 30)], radius=24, outline=(79, 70, 229), width=2)
        draw.rounded_rectangle([(34, 34), (width - 34, height - 34)], radius=22, outline=(99, 102, 241), width=1)

        # Header Badge Pill (Left)
        badge_text = f"  ⚡ SOLUSI TERBAIK  |  📍 {location.upper()}  "
        draw.rounded_rectangle([(65, 45), (460, 95)], radius=12, fill=(67, 56, 202))
        draw.text((80, 60), badge_text, fill=(255, 255, 255))

        # Brand Logo (Top Right)
        self._draw_logo_on_canvas(img, logo_url, brand_name, width, height)

        # Service Subtitle Pill
        draw.rounded_rectangle([(65, 140), (min(width - 65, 620), 185)], radius=8, fill=(30, 41, 59))
        draw.text((80, 153), f"LAYANAN SPESIALIS: {service_name.upper()}", fill=(129, 140, 248))

        # Main Title (wrap text cleanly)
        words = title.split()
        lines = []
        cur_line = []
        for w in words:
            if len(" ".join(cur_line + [w])) <= 34:
                cur_line.append(w)
            else:
                lines.append(" ".join(cur_line))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))

        y_text = 220
        for line in lines[:3]:
            draw.text((68, y_text + 3), line, fill=(0, 0, 0))
            draw.text((65, y_text), line, fill=(248, 250, 252))
            y_text += 70

        # Problem-Solution Value Prop Bar
        footer_y = height - 120
        draw.rounded_rectangle([(65, footer_y), (width - 65, footer_y + 60)], radius=14, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
        draw.text((85, footer_y + 14), f"✓ Solusi Terpercaya & Bebas Kendala  •  ✓ Konsultasi Langsung  •  ✓ Bergaransi Resmi", fill=(52, 211, 153))
        draw.text((85, footer_y + 36), f"Official Partner: {brand_name} • Wilayah Layanan: {location}", fill=(148, 163, 184))

        img.save(filepath, "JPEG", quality=92)

    def generate_custom_image(
        self,
        prompt: str,
        brand_name: str = "GEO Studio",
        location: str = "Indonesia",
        aspect_ratio: str = "16:9",
        style: str = "photorealistic",
        logo_url: Optional[str] = None,
        brand_id: Optional[str] = None,
        brand_color_primary: Optional[str] = "#4f46e5",
        brand_color_accent: Optional[str] = "#7c3aed",
        watermark_logo: bool = True
    ) -> Dict[str, Any]:
        """
        Production image generator supporting 16:9, 1:1, 9:16, 4:3 aspect ratios,
        Google Imagen 3 API integration, and brand color palette / logo watermarking.
        Stores into per-brand asset directory output/assets/{brand_id}/images/ when specified.
        """
        import time
        import uuid

        clean_slug = re.sub(r'[^a-z0-9]+', '-', prompt.lower())[:25].strip('-') or "render"
        filename = f"gen-{int(time.time())}-{clean_slug}.jpg"
        target_dir = self.get_brand_asset_dir(brand_id)
        filepath = os.path.join(target_dir, filename)
        web_url = self.get_brand_asset_url(brand_id, filename)

        # Resolution map
        width, height = 1200, 675
        imagen_ratio = "16:9"
        if aspect_ratio == "1:1":
            width, height = 1080, 1080
            imagen_ratio = "1:1"
        elif aspect_ratio == "9:16":
            width, height = 720, 1280
            imagen_ratio = "9:16"
        elif aspect_ratio == "4:3":
            width, height = 1200, 900
            imagen_ratio = "4:3"

        # Style prompt enrichment
        style_enrichment = ""
        if style == "photorealistic" or style == "enterprise":
            style_enrichment = "Award-winning commercial photography, architectural glass office, high-end enterprise technology aesthetic, 8k resolution, cinematic lighting. "
        elif style == "creative":
            style_enrichment = "Vibrant modern agency branding visual, glassmorphic 3D elements, dynamic gradient lighting, ultra-clean commercial composition. "
        elif style == "industrial":
            style_enrichment = "Precision engineering schematic, technical LiDAR blueprint, industrial grade commercial photography, crisp studio lighting. "
        elif style == "editorial":
            style_enrichment = "Minimalist luxury editorial aesthetic, soft natural studio lighting, high fashion typography layout, perfect negative space. "

        full_prompt = f"{style_enrichment}{prompt}. Official brand visual for {brand_name} in {location}."

        # 1. Attempt Google Imagen 3 via Gemini authentication / Antigravity session
        attempts = max(1, len(self.auth.accounts))
        for _ in range(attempts):
            auth_info = self.auth.get_active_auth_headers_or_param()
            if not auth_info:
                break

            headers = {"Content-Type": "application/json"}
            headers.update(auth_info.get("headers", {}))
            params = auth_info.get("param", {})

            url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"
            payload = {
                "instances": [{"prompt": full_prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": imagen_ratio,
                    "personGeneration": "ALLOW_ADULT"
                }
            }

            try:
                resp = requests.post(url, headers=headers, params=params, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    predictions = data.get("predictions", [])
                    if predictions and "bytesBase64Encoded" in predictions[0]:
                        raw_bytes = base64.b64decode(predictions[0]["bytesBase64Encoded"])
                        base_img = Image.open(BytesIO(raw_bytes)).convert("RGB")
                        base_img = base_img.resize((width, height), Image.Resampling.LANCZOS)

                        # Overlay logo watermark if enabled
                        if watermark_logo and (logo_url or brand_name):
                            self._draw_logo_on_canvas(base_img, logo_url, brand_name, width, height)

                        base_img.save(filepath, "JPEG", quality=92)
                        with open(filepath, "rb") as f:
                            b64_res = base64.b64encode(f.read()).decode("utf-8")

                        logger.info(f"[GeminiEngine] Successfully generated custom Imagen 3 visual: {filepath}")
                        result = {
                            "success": True,
                            "source": "gemini_imagen_3",
                            "id": f"img-{uuid.uuid4().hex[:8]}",
                            "filename": filename,
                            "file_path": filepath,
                            "url": web_url,
                            "brand_id": brand_id,
                            "prompt": prompt,
                            "brand_name": brand_name,
                            "aspect_ratio": aspect_ratio,
                            "style": style,
                            "width": width,
                            "height": height,
                            "base64_data": b64_res
                        }
                        self._record_gallery_item(result, brand_id=brand_id)
                        return result
                elif resp.status_code in [429, 403]:
                    self.auth.rotate()
                else:
                    self.auth.rotate()
            except Exception as e:
                logger.warning(f"[GeminiEngine] Imagen generation request error: {e}")
                self.auth.rotate()

        # 2. Resilient High-Aesthetic Studio Canvas Engine (Fallback)
        # Parse brand color tokens
        def parse_hex(hex_val, fallback):
            try:
                h = (hex_val or "").lstrip("#")
                if len(h) == 6:
                    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            except Exception:
                pass
            return fallback

        c_primary = parse_hex(brand_color_primary, (79, 70, 229))
        c_accent = parse_hex(brand_color_accent, (124, 58, 237))

        img = Image.new("RGB", (width, height), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)

        # Ambient gradient background incorporating brand colors
        for y in range(height):
            ratio = y / height
            r = int(12 + ((c_primary[0] * 0.12) * ratio))
            g = int(18 + ((c_primary[1] * 0.12) * ratio))
            b = int(32 + ((c_accent[2] * 0.18) * ratio))
            draw.line([(0, y), (width, y)], fill=(min(r, 255), min(g, 255), min(b, 255)))

        # Modern tech grid overlay (subtle lines)
        grid_step = 60
        for gx in range(0, width, grid_step):
            draw.line([(gx, 0), (gx, height)], fill=(255, 255, 255, 8))
        for gy in range(0, height, grid_step):
            draw.line([(0, gy), (width, gy)], fill=(255, 255, 255, 8))

        # Brand accent border
        draw.rounded_rectangle([(24, 24), (width - 24, height - 24)], radius=20, outline=c_primary, width=2)
        draw.rounded_rectangle([(28, 28), (width - 28, height - 28)], radius=18, outline=c_accent, width=1)

        # Header Category Badge (Left)
        badge_text = f"  ✦ {brand_name.upper()}  •  {style.upper()}  •  {location.upper()}  "
        badge_w = min(width - 50, 520) if width >= 800 else width - 60
        draw.rounded_rectangle([(50, 45), (badge_w, 95)], radius=12, fill=c_primary)
        draw.text((65, 61), badge_text, fill=(255, 255, 255))

        # Logo on Top Right if enabled
        if watermark_logo and width >= 700:
            self._draw_logo_on_canvas(img, logo_url, brand_name, width, height)

        # Main Prompt Headline (Wrap text cleanly)
        words = prompt.split()
        lines = []
        cur = []
        max_chars = 36 if width >= 1000 else (26 if width >= 700 else 18)
        for w in words:
            if len(" ".join(cur + [w])) <= max_chars:
                cur.append(w)
            else:
                lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))

        y_pos = int(height * 0.30)
        line_height = 64 if height >= 900 else 52
        for line in lines[:4]:
            draw.text((54, y_pos + 3), line, fill=(0, 0, 0))
            draw.text((50, y_pos), line, fill=(248, 250, 252))
            y_pos += line_height

        # Problem-Solution Value Pill
        if height >= 600:
            sol_y = y_pos + 20
            draw.rounded_rectangle([(50, sol_y), (min(width - 50, 680), sol_y + 40)], radius=8, fill=(30, 41, 59))
            draw.text((65, sol_y + 11), f"✓ Solusi Terpercaya  •  ✓ Bergaransi Resmi  •  ✓ Konsultasi Langsung", fill=(52, 211, 153))

        # Footer Status Pill
        footer_y = height - 85
        draw.rounded_rectangle([(50, footer_y), (width - 50, footer_y + 45)], radius=10, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
        draw.text((65, footer_y + 14), f"✨ GEO Engine Studio Visual • Rasio {aspect_ratio} ({width}x{height}px) • {brand_name}", fill=(148, 163, 184))

        img.save(filepath, "JPEG", quality=92)

        with open(filepath, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        result = {
            "success": True,
            "source": "studio_canvas_fallback",
            "id": f"img-{uuid.uuid4().hex[:8]}",
            "filename": filename,
            "file_path": filepath,
            "url": web_url,
            "brand_id": brand_id,
            "prompt": prompt,
            "brand_name": brand_name,
            "aspect_ratio": aspect_ratio,
            "style": style,
            "width": width,
            "height": height,
            "base64_data": b64
        }

        self._record_gallery_item(result, brand_id=brand_id)
        return result

    def craft_creative_prompt(
        self,
        brand_name: str,
        industry: Optional[str] = None,
        service_name: Optional[str] = None,
        location: Optional[str] = None,
        pain_point: Optional[str] = None,
        solution: Optional[str] = None,
        brand_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crafts a tailored commercial visual prompt for Antigravity or Gemini App generation."""
        ind = (industry or "Technology & Software Development").strip()
        srv = (service_name or "Enterprise Software Development").strip()
        loc = (location or "Indonesia").strip()
        pp = (pain_point or "sistem lama yang lambat dan sering crash").strip()
        sol = (solution or "arsitektur modern berkinerja tinggi, responsif dan stabil").strip()

        base_prompt = self.build_industry_prompt(
            service_name=srv,
            location=loc,
            brand_name=brand_name,
            industry=ind
        )

        full_prompt = (
            f"{base_prompt} "
            f"Commercial marketing visual solving client pain point '{pp}' with real solution '{sol}'. "
            f"Featuring clean professional branding for {brand_name} in {loc}. "
            f"Hyper-detailed, octane render, 8k resolution, photorealistic, cinematic lighting, no distorted text."
        )

        target_dir = self.get_brand_asset_dir(brand_id)

        return {
            "success": True,
            "brand_id": brand_id,
            "brand_name": brand_name,
            "prompt": full_prompt,
            "aspect_ratios": ["16:9", "1:1", "9:16"],
            "target_dir": target_dir,
            "instruction": "Salin prompt ini untuk dijalankan via Antigravity atau Gemini App, lalu masukkan hasil gambar ke bank asset situs ini."
        }

    def _record_gallery_item(self, item: Dict[str, Any], brand_id: Optional[str] = None):
        clean_record = {k: v for k, v in item.items() if k != "base64_data"}

        # 1. Record in global gallery
        gallery_file = "data/image_gallery.json"
        items = []
        if os.path.exists(gallery_file):
            try:
                with open(gallery_file, "r") as f:
                    items = json.load(f)
            except Exception:
                items = []
        items.insert(0, clean_record)
        try:
            with open(gallery_file, "w") as f:
                json.dump(items[:150], f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save global gallery index: {e}")

        # 2. Record in per-brand asset index if brand_id is specified
        if brand_id:
            brand_dir = self.get_brand_asset_dir(brand_id)
            brand_index = os.path.join(brand_dir, "assets_index.json")
            brand_items = []
            if os.path.exists(brand_index):
                try:
                    with open(brand_index, "r") as f:
                        brand_items = json.load(f)
                except Exception:
                    brand_items = []
            brand_items.insert(0, clean_record)
            try:
                with open(brand_index, "w") as f:
                    json.dump(brand_items[:100], f, indent=2)
            except Exception as e:
                logger.warning(f"Could not save brand gallery index for {brand_id}: {e}")

    def list_gallery_images(self, brand_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists images in gallery, scoped strictly to brand_id when provided, filtering out missing files."""
        if brand_id:
            brand_dir = self.get_brand_asset_dir(brand_id)
            brand_index = os.path.join(brand_dir, "assets_index.json")
            if os.path.exists(brand_index):
                try:
                    with open(brand_index, "r") as f:
                        items = json.load(f)
                    valid_items = []
                    for it in items:
                        fp = it.get("file_path") or os.path.join(brand_dir, it.get("filename", ""))
                        if os.path.exists(fp):
                            valid_items.append(it)
                    return valid_items
                except Exception:
                    pass

            # Fallback to scanning brand's images directory
            scanned = []
            if os.path.exists(brand_dir):
                for f in sorted(os.listdir(brand_dir), reverse=True):
                    if f.endswith(".jpg") or f.endswith(".png") or f.endswith(".webp"):
                        scanned.append({
                            "id": f,
                            "filename": f,
                            "brand_id": brand_id,
                            "url": self.get_brand_asset_url(brand_id, f),
                            "file_path": os.path.join(brand_dir, f),
                            "prompt": f.replace("thumb-", "").replace("gen-", "").replace(".jpg", "").replace(".png", "").replace("-", " ")
                        })
            return scanned

        # Global list
        gallery_file = "data/image_gallery.json"
        if os.path.exists(gallery_file):
            try:
                with open(gallery_file, "r") as f:
                    items = json.load(f)
                valid_items = []
                for it in items:
                    fp = it.get("file_path") or (it.get("url", "").lstrip("/"))
                    if os.path.exists(fp):
                        valid_items.append(it)
                return valid_items
            except Exception:
                pass
        
        scanned = []
        img_dir = os.path.join(self.output_dir, "images")
        if os.path.exists(img_dir):
            for f in sorted(os.listdir(img_dir), reverse=True):
                if f.endswith(".jpg") or f.endswith(".png"):
                    scanned.append({
                        "id": f,
                        "filename": f,
                        "url": f"/output/images/{f}",
                        "prompt": f.replace("thumb-", "").replace("gen-", "").replace(".jpg", "").replace("-", " ")
                    })
        return scanned
