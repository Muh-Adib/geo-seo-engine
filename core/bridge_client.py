import re
import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class WordPressBridgeClient:
    """
    Client for interacting with WordPress sites.
    Supports:
    1. Direct REST Bridge Plugin (`POST /wp-json/seo-engine/v1/publish` via `X-SEO-Engine-Key`)
    2. Session Auth (`POST /pawon/` or `/wp-login.php` + Nonce + REST API)
    """

    def __init__(self, timeout: int = 25):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })

    def publish_article(
        self,
        brand_data: Dict[str, Any],
        article_payload: Dict[str, Any],
        login_credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Attempts publishing via Bridge Plugin endpoint first; if not configured or failing,
        falls back to Session Authentication if credentials provided.
        """
        endpoint = brand_data.get("wp_endpoint_url")
        secret_key = brand_data.get("api_secret_key", "unicam-geo-secret-key-2026")
        domain = brand_data.get("domain_url", "").rstrip("/")

        # Method 1: Bridge Plugin
        if endpoint:
            try:
                res = self.publish_via_bridge(endpoint, secret_key, article_payload)
                if res.get("success"):
                    return res
                logger.warning(f"[BridgeClient] Bridge endpoint returned non-success: {res.get('error')}. Checking fallback.")
            except Exception as e:
                logger.warning(f"[BridgeClient] Bridge endpoint exception: {e}")

        # Method 2: Session-based WordPress REST Auth
        if login_credentials and login_credentials.get("username") and login_credentials.get("password"):
            login_path = login_credentials.get("login_path", "/pawon/")
            return self.publish_via_session(
                domain_url=domain,
                username=login_credentials["username"],
                password=login_credentials["password"],
                login_path=login_path,
                article_payload=article_payload
            )

        return {
            "success": False,
            "error": "No valid publishing method succeeded (Bridge plugin endpoint unreachable and no session credentials provided)."
        }

    def publish_via_bridge(
        self,
        endpoint_url: str,
        secret_key: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calls `POST /wp-json/seo-engine/v1/publish` with `X-SEO-Engine-Key`.
        """
        headers = {
            "X-SEO-Engine-Key": secret_key,
            "Content-Type": "application/json"
        }
        
        request_body = {
            "title": payload.get("title"),
            "content": payload.get("content_html"),
            "slug": payload.get("slug"),
            "status": payload.get("status", "publish"),
            "meta_description": payload.get("meta_description", ""),
            "primary_focus_keyword": payload.get("primary_keyword", ""),
            "tags": payload.get("tags", []),
            "categories": payload.get("categories", ["Insights"]),
            "schedule_date": payload.get("schedule_date"),
            "featured_image_base64": payload.get("featured_image_base64"),
            "featured_image_filename": payload.get("featured_image_filename", "featured-thumbnail.jpg")
        }

        try:
            resp = self.session.post(endpoint_url, json=request_body, headers=headers, timeout=self.timeout)
            if resp.status_code in [200, 201]:
                data = resp.json()
                return {
                    "success": True,
                    "post_id": data.get("post_id"),
                    "url": data.get("url"),
                    "slug": data.get("slug"),
                    "status": data.get("status"),
                    "tags_count": data.get("tags_count", len(payload.get("tags", []))),
                    "featured_image_url": data.get("featured_image_url"),
                    "raw": data
                }
            elif resp.status_code == 403:
                return {
                    "success": False,
                    "error": f"HTTP 403 Forbidden: Secret Key tidak cocok. Periksa pengaturan Secret Key di WordPress Admin (menu SEO Engine) atau pastikan Secret Key di pengaturan situs ini sudah sesuai."
                }
            elif resp.status_code == 404:
                return {
                    "success": False,
                    "error": f"HTTP 404 Not Found: Plugin Unicam SEO Bridge belum terpasang atau belum diaktifkan di situs {endpoint_url}. Unduh dan aktifkan unicam-seo-bridge.zip di WordPress."
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {resp.status_code}: {resp.text[:300]}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Bridge request failed: {str(e)}"
            }

    def login_and_get_nonce(
        self,
        domain_url: str,
        username: str,
        password: str,
        login_path: str = "/pawon/"
    ) -> Optional[str]:
        """
        Logs into WordPress using standard login form at custom or standard path,
        then extracts REST API nonce from wp-admin.
        """
        base_url = domain_url.rstrip("/")
        login_url = f"{base_url}{login_path}" if login_path.startswith("/") else f"{base_url}/{login_path}"

        try:
            # 1. Fetch login form to capture cookies
            get_resp = self.session.get(login_url, timeout=self.timeout)
            
            # 2. Submit credentials
            login_data = {
                "log": username,
                "pwd": password,
                "wp-submit": "Log In",
                "redirect_to": f"{base_url}/wp-admin/",
                "testcookie": "1"
            }
            
            post_resp = self.session.post(login_url, data=login_data, timeout=self.timeout, allow_redirects=True)
            
            # 3. Request wp-admin to obtain rest nonce
            admin_resp = self.session.get(f"{base_url}/wp-admin/", timeout=self.timeout)
            nonce_match = re.search(r'wpApiSettings\s*=\s*\{[^}]*"nonce"\s*:\s*"([a-zA-Z0-9]+)"', admin_resp.text)
            if nonce_match:
                nonce = nonce_match.group(1)
                logger.info(f"[BridgeClient] Nonce acquired: {nonce}")
                return nonce
            
            # Alternative nonce match
            alt_match = re.search(r'"nonce":"([a-zA-Z0-9]{10})"', admin_resp.text)
            if alt_match:
                return alt_match.group(1)

            # Check if logged in by looking for admin bar
            if "wp-admin" in post_resp.url or "wp-admin-bar" in admin_resp.text:
                # Try fetching nonce directly from heartbeat or localized scripts
                return "session_active"
            
            return None
        except Exception as e:
            logger.error(f"[BridgeClient] Login error: {e}")
            return None

    def publish_via_session(
        self,
        domain_url: str,
        username: str,
        password: str,
        login_path: str,
        article_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publishes post via session cookies + standard REST API /wp/v2/posts.
        """
        nonce = self.login_and_get_nonce(domain_url, username, password, login_path)
        if not nonce:
            return {
                "success": False,
                "error": "Failed to log in to WordPress or retrieve authentication nonce."
            }

        base_url = domain_url.rstrip("/")
        rest_url = f"{base_url}/wp-json/wp/v2/posts"

        headers = {}
        if nonce != "session_active":
            headers["X-WP-Nonce"] = nonce

        # Standard WP REST API payload
        post_data = {
            "title": article_payload.get("title"),
            "content": article_payload.get("content_html"),
            "slug": article_payload.get("slug"),
            "status": article_payload.get("status", "draft")
        }

        try:
            resp = self.session.post(rest_url, json=post_data, headers=headers, timeout=self.timeout)
            if resp.status_code in [200, 201]:
                data = resp.json()
                post_id = data.get("id")
                link = data.get("link")
                return {
                    "success": True,
                    "post_id": post_id,
                    "url": link,
                    "slug": data.get("slug"),
                    "status": data.get("status"),
                    "tags_count": 0, # Standard WP API requires separate tag creation or taxonomy IDs
                    "note": "Published via session auth fallback"
                }
            else:
                return {
                    "success": False,
                    "error": f"REST API failed ({resp.status_code}): {resp.text[:300]}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Session publish error: {str(e)}"
            }

    def fetch_recent_articles(self, brand_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieves recent articles from the brand website to feed the internal link graph.
        """
        endpoint = brand_data.get("wp_endpoint_url")
        secret_key = brand_data.get("api_secret_key", "unicam-geo-secret-key-2026")
        domain = brand_data.get("domain_url", "").rstrip("/")

        # Try Bridge endpoint first
        if endpoint:
            articles_url = endpoint.replace("/publish", "/articles")
            try:
                resp = self.session.get(articles_url, headers={"X-SEO-Engine-Key": secret_key}, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("articles", [])
            except Exception:
                pass

        # Try standard public REST endpoint
        try:
            resp = self.session.get(f"{domain}/wp-json/wp/v2/posts?per_page=10&_fields=id,title,slug,link", timeout=10)
            if resp.status_code == 200:
                posts = resp.json()
                return [
                    {
                        "id": p.get("id"),
                        "title": p.get("title", {}).get("rendered", "") if isinstance(p.get("title"), dict) else str(p.get("title", "")),
                        "slug": p.get("slug", ""),
                        "url": p.get("link", "")
                    }
                    for p in posts
                ]
        except Exception:
            pass

        return []
