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
    Multi-Account Google Gemini & Imagen Manager.
    - Connects directly to Google Gemini user accounts (including Antigravity Desktop sessions).
    - Supports multi-account rotation for high throughput and rate-limit bypass.
    - Generates 16:9 featured thumbnails and in-article graphics.
    - Fallback to high-aesthetic typography engine (Pillow) so generation never fails.
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

    def generate_featured_thumbnail(
        self,
        title: str,
        service_name: str,
        brand_name: str,
        location: str,
        slug: str
    ) -> Dict[str, Any]:
        """
        Generates a 16:9 1200x675 thumbnail.
        Tries Google Imagen API across connected user accounts; falls back to high-res Studio Canvas.
        """
        filename = f"thumb-{slug[:35]}.jpg"
        filepath = os.path.join(self.output_dir, filename)

        # 1. Try Imagen generation using user Gemini accounts
        attempts = max(1, len(self.auth.accounts))
        for _ in range(attempts):
            auth_info = self.auth.get_active_auth_headers_or_param()
            if not auth_info:
                break

            headers = {"Content-Type": "application/json"}
            headers.update(auth_info.get("headers", {}))
            params = auth_info.get("param", {})

            url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"
            prompt = (
                f"Hyperrealistic 8k commercial cinematic visual for {service_name} in {location}, "
                f"professional lighting, award winning 3D render by {brand_name}, octane render, photorealistic, 16:9 ratio."
            )
            payload = {
                "instances": [{"prompt": prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": "16:9",
                    "personGeneration": "ALLOW_ADULT"
                }
            }

            try:
                resp = requests.post(url, headers=headers, params=params, json=payload, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    predictions = data.get("predictions", [])
                    if predictions and "bytesBase64Encoded" in predictions[0]:
                        img_data = base64.b64decode(predictions[0]["bytesBase64Encoded"])
                        with open(filepath, "wb") as f:
                            f.write(img_data)
                        logger.info(f"[GeminiEngine] Successfully generated Imagen thumbnail: {filepath}")
                        return {
                            "success": True,
                            "source": "gemini_imagen_3",
                            "file_path": filepath,
                            "filename": filename,
                            "base64_data": predictions[0]["bytesBase64Encoded"],
                            "alt_text": f"{service_name} in {location} by {brand_name}",
                            "caption": f"Professional master visual for {service_name} {location}."
                        }
                elif resp.status_code in [429, 403]:
                    logger.warning("[GeminiEngine] Quota hit on active user account. Rotating...")
                    self.auth.rotate()
                else:
                    logger.warning(f"[GeminiEngine] Imagen HTTP {resp.status_code}: {resp.text[:120]}")
                    self.auth.rotate()
            except Exception as e:
                logger.warning(f"[GeminiEngine] Imagen request error: {e}")
                self.auth.rotate()

        # 2. Resilient Studio Aesthetic Canvas Generator (Pillow Fallback)
        self._build_studio_canvas(
            filepath=filepath,
            title=title,
            brand_name=brand_name,
            location=location,
            service_name=service_name
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
            "caption": f"High resolution render for {service_name} {location}."
        }

    def _build_studio_canvas(
        self,
        filepath: str,
        title: str,
        brand_name: str,
        location: str,
        service_name: str
    ):
        """
        Creates a modern, 16:9 (1200x675) studio thumbnail with typography,
        dark modern gradient, badge pills, and crisp layout.
        """
        width, height = 1200, 675
        img = Image.new("RGB", (width, height), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)

        # Gradient overlay
        for y in range(height):
            r = int(15 + (15 * (y / height)))
            g = int(23 + (4 * (y / height)))
            b = int(42 + (33 * (y / height)))
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Decorative glowing accent border
        draw.rounded_rectangle([(30, 30), (width - 30, height - 30)], radius=24, outline=(79, 70, 229), width=2)
        draw.rounded_rectangle([(34, 34), (width - 34, height - 34)], radius=22, outline=(99, 102, 241), width=1)

        # Brand & Location Badge Pill
        badge_text = f"  ⚡ {brand_name.upper()}  |  📍 {location.upper()}  "
        draw.rounded_rectangle([(65, 65), (550, 115)], radius=12, fill=(67, 56, 202))
        draw.text((80, 78), badge_text, fill=(255, 255, 255))

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

        y_text = 190
        for line in lines[:3]:
            draw.text((68, y_text + 3), line, fill=(0, 0, 0))
            draw.text((65, y_text), line, fill=(248, 250, 252))
            y_text += 70

        # Footer Subtitle Pill
        draw.rounded_rectangle([(65, height - 120), (width - 65, height - 70)], radius=12, fill=(30, 41, 59))
        footer_text = "✨ 4K Master Render  •  2x Revision Guarantee  •  Remote Production Hub Yogyakarta"
        draw.text((85, height - 102), footer_text, fill=(148, 163, 184))

        img.save(filepath, "JPEG", quality=92)
        logger.info(f"[GeminiEngine] Studio canvas thumbnail saved: {filepath}")

    def generate_custom_image(
        self,
        prompt: str,
        brand_name: str = "Studio",
        location: str = "Indonesia",
        aspect_ratio: str = "16:9",
        style: str = "photorealistic"
    ) -> Dict[str, Any]:
        """
        Standalone Interactive Image Generator.
        Generates images for marketing, featured thumbnails, or social graphics.
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

        # Create styled visual
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
        draw.rounded_rectangle([(50, 50), (min(width - 50, 580), 100)], radius=12, fill=(67, 56, 202))
        draw.text((65, 66), badge_text, fill=(255, 255, 255))

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

        # Track in gallery file
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
        
        # Don't store huge base64 in gallery index
        clean_record = {k: v for k, v in item.items() if k != "base64_data"}
        items.insert(0, clean_record)
        try:
            with open(gallery_file, "w") as f:
                json.dump(items[:100], f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save gallery index: {e}")

    def list_gallery_images(self) -> List[Dict[str, Any]]:
        """Returns list of all generated images in the gallery."""
        gallery_file = "data/image_gallery.json"
        if os.path.exists(gallery_file):
            try:
                with open(gallery_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Scan folder as fallback
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
