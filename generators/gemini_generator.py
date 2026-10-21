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

    def __init__(self, output_dir: str = "output/images"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.auth = GeminiAuthManager()

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
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a 16:9 (1200x675) featured thumbnail for WordPress.
        Overlays brand logo and uses industry-appropriate problem-solving visual aesthetic.
        """
        filename = f"thumb-{slug[:35]}.jpg"
        filepath = os.path.join(self.output_dir, filename)

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
                elif os.path.exists(logo_clean):
                    logo_img = Image.open(logo_clean)

                if logo_img:
                    logo_img = logo_img.convert("RGBA")
                    max_w, max_h = 200, 55
                    logo_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                    
                    lw, lh = logo_img.size
                    box_x1 = width - lw - 60
                    box_y1 = 35
                    box_x2 = width - 40
                    box_y2 = box_y1 + lh + 20

                    # Draw glass backdrop for logo
                    overlay = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
                    draw_o = ImageDraw.Draw(overlay)
                    draw_o.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=12, fill=(15, 23, 42, 210), outline=(99, 102, 241, 200), width=1)
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
        logo_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Interactive visual generator supporting 16:9, 1:1, 9:16 aspect ratios and brand logo watermarking.
        """
        import time
        import uuid

        clean_slug = re.sub(r'[^a-z0-9]+', '-', prompt.lower())[:25].strip('-') or "render"
        filename = f"gen-{int(time.time())}-{clean_slug}.jpg"
        filepath = os.path.join(self.output_dir, filename)

        width, height = 1200, 675
        if aspect_ratio == "1:1":
            width, height = 1000, 1000
        elif aspect_ratio == "9:16":
            width, height = 720, 1280

        img = Image.new("RGB", (width, height), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)

        # Ambient gradient background
        for y in range(height):
            ratio = y / height
            if style == "cyberpunk":
                r = int(18 + (30 * ratio))
                g = int(10 + (15 * ratio))
                b = int(45 + (60 * ratio))
            elif style == "minimalist":
                r = int(24 + (16 * ratio))
                g = int(27 + (18 * ratio))
                b = int(35 + (22 * ratio))
            else:
                r = int(15 + (18 * ratio))
                g = int(23 + (12 * ratio))
                b = int(42 + (35 * ratio))
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Accent border
        draw.rounded_rectangle([(24, 24), (width - 24, height - 24)], radius=20, outline=(99, 102, 241), width=2)

        # Header Badge
        badge_text = f"  ✦ {brand_name.upper()}  •  {style.upper()}  •  {location.upper()}  "
        draw.rounded_rectangle([(50, 50), (min(width - 50, 520), 100)], radius=12, fill=(67, 56, 202))
        draw.text((65, 66), badge_text, fill=(255, 255, 255))

        # Logo on Top Right if width allows
        if width >= 900:
            self._draw_logo_on_canvas(img, logo_url, brand_name, width, height)

        # Prompt Title Text Wrap
        words = prompt.split()
        lines = []
        cur = []
        max_chars = 34 if width >= 1000 else 22
        for w in words:
            if len(" ".join(cur + [w])) <= max_chars:
                cur.append(w)
            else:
                lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))

        y_pos = int(height * 0.32)
        for line in lines[:4]:
            draw.text((54, y_pos + 2), line, fill=(0, 0, 0))
            draw.text((50, y_pos), line, fill=(248, 250, 252))
            y_pos += 65

        # Footer pill
        footer_y = height - 90
        draw.rounded_rectangle([(50, footer_y), (width - 50, footer_y + 45)], radius=10, fill=(30, 41, 59))
        draw.text((65, footer_y + 14), f"✨ Generated by GEO Studio AI • Ratio {aspect_ratio} • Resolution {width}x{height}", fill=(148, 163, 184))

        img.save(filepath, "JPEG", quality=92)

        with open(filepath, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        result = {
            "success": True,
            "id": f"img-{uuid.uuid4().hex[:8]}",
            "filename": filename,
            "file_path": filepath,
            "url": f"/output/images/{filename}",
            "prompt": prompt,
            "brand_name": brand_name,
            "aspect_ratio": aspect_ratio,
            "style": style,
            "width": width,
            "height": height,
            "base64_data": b64
        }

        self._record_gallery_item(result)
        return result

    def _record_gallery_item(self, item: Dict[str, Any]):
        gallery_file = "data/image_gallery.json"
        items = []
        if os.path.exists(gallery_file):
            try:
                with open(gallery_file, "r") as f:
                    items = json.load(f)
            except Exception:
                items = []
        
        clean_record = {k: v for k, v in item.items() if k != "base64_data"}
        items.insert(0, clean_record)
        try:
            with open(gallery_file, "w") as f:
                json.dump(items[:100], f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save gallery index: {e}")

    def list_gallery_images(self) -> List[Dict[str, Any]]:
        gallery_file = "data/image_gallery.json"
        if os.path.exists(gallery_file):
            try:
                with open(gallery_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        
        scanned = []
        if os.path.exists(self.output_dir):
            for f in sorted(os.listdir(self.output_dir), reverse=True):
                if f.endswith(".jpg") or f.endswith(".png"):
                    scanned.append({
                        "id": f,
                        "filename": f,
                        "url": f"/output/images/{f}",
                        "prompt": f.replace("thumb-", "").replace("gen-", "").replace(".jpg", "").replace("-", " ")
                    })
        return scanned
