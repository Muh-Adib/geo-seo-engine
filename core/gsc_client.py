import os
import json
import logging
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger("gsc_client")

class GSCClient:
    """
    Google Search Console Connector via Service Account.
    Authenticates with official Google Service Account JSON to retrieve:
    1. Search analytics (Clicks, Impressions, CTR, Average Position)
    2. Top ranking search queries
    3. Top indexed pages / landing pages
    4. Indexing & URL verification
    """

    def __init__(self, credentials_path_or_json: Optional[str] = None):
        self.credentials_data = self._load_credentials(credentials_path_or_json)

    def _load_credentials(self, cred: Optional[str]) -> Optional[Dict[str, Any]]:
        if not cred:
            default_path = "data/gsc_service_account.json"
            if os.path.exists(default_path):
                try:
                    with open(default_path, "r") as f:
                        return json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to read default GSC credentials: {e}")
            return None

        # Try parsing as JSON string
        cred_str = cred.strip()
        if cred_str.startswith("{") and cred_str.endswith("}"):
            try:
                return json.loads(cred_str)
            except Exception as e:
                logger.error(f"Failed to parse credentials JSON string: {e}")
                return None

        # Try reading as file path
        if os.path.exists(cred_str):
            try:
                with open(cred_str, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read credentials from file {cred_str}: {e}")
                return None

        return None

    def get_access_token(self, cred_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Obtains OAuth2 access token using Google Cloud service account credentials."""
        data = cred_data or self.credentials_data
        if not data:
            return None

        try:
            from google.oauth2 import service_account
            import google.auth.transport.requests

            scopes = ["https://www.googleapis.com/auth/webmasters.readonly"]
            credentials = service_account.Credentials.from_service_account_info(
                data,
                scopes=scopes
            )
            request = google.auth.transport.requests.Request()
            credentials.refresh(request)
            return credentials.token
        except Exception as e:
            logger.error(f"GSC authentication token error: {e}")
            return None

    def test_connection(self, site_url: str, credentials_json: Optional[str] = None) -> Dict[str, Any]:
        """Tests live connection to GSC for a site property."""
        cred_data = self._load_credentials(credentials_json) if credentials_json else self.credentials_data
        if not cred_data:
            return {
                "success": False,
                "connected": False,
                "error": "Service Account JSON belum diatur. Masukkan credentials di Pengaturan Situs."
            }

        token = self.get_access_token(cred_data)
        if not token:
            return {
                "success": False,
                "connected": False,
                "error": "Gagal mengautentikasi Service Account ke Google. Periksa private_key dan client_email."
            }

        clean_site = site_url.strip()
        if not clean_site.startswith("sc-domain:") and not clean_site.endswith("/"):
            clean_site += "/"
        encoded_site = urllib.parse.quote_plus(clean_site)

        # Call GSC sites endpoint to verify access
        url = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                site_info = resp.json()
                return {
                    "success": True,
                    "connected": True,
                    "permission_level": site_info.get("permissionLevel", "siteFullUser"),
                    "site_url": clean_site,
                    "client_email": cred_data.get("client_email")
                }
            elif resp.status_code == 403:
                return {
                    "success": False,
                    "connected": False,
                    "error": f"HTTP 403: Email '{cred_data.get('client_email')}' belum ditambahkan sebagai User/Owner di Google Search Console untuk property {clean_site}.",
                    "client_email": cred_data.get("client_email")
                }
            elif resp.status_code == 404:
                return {
                    "success": False,
                    "connected": False,
                    "error": f"HTTP 404: Property '{clean_site}' tidak ditemukan di akun GSC Service Account.",
                    "client_email": cred_data.get("client_email")
                }
            else:
                return {
                    "success": False,
                    "connected": False,
                    "error": f"HTTP {resp.status_code}: {resp.text[:150]}"
                }
        except Exception as e:
            return {
                "success": False,
                "connected": False,
                "error": f"Koneksi gagal: {str(e)}"
            }

    def get_search_analytics(
        self,
        site_url: str,
        days: int = 28,
        dimensions: Optional[List[str]] = None,
        credentials_json: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves real search performance data from Google Search Console.
        Dimensions can include ['query'], ['page'], ['device'], ['country'].
        """
        cred_data = self._load_credentials(credentials_json) if credentials_json else self.credentials_data
        if not cred_data:
            return {
                "success": False,
                "configured": False,
                "error": "Service Account JSON belum dikonfigurasi.",
                "overview": {"totalClicks": 0, "totalImpressions": 0, "averageCtr": "0.0%", "averagePosition": 0.0},
                "queries": [],
                "pages": []
            }

        token = self.get_access_token(cred_data)
        if not token:
            return {
                "success": False,
                "configured": True,
                "error": "Gagal otentikasi ke Google Search Console.",
                "overview": {"totalClicks": 0, "totalImpressions": 0, "averageCtr": "0.0%", "averagePosition": 0.0},
                "queries": [],
                "pages": []
            }

        clean_site = site_url.strip()
        if not clean_site.startswith("sc-domain:") and not clean_site.endswith("/"):
            clean_site += "/"
        encoded_site = urllib.parse.quote_plus(clean_site)

        end_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=days + 2)).strftime("%Y-%m-%d")

        url = f"https://www.googleapis.com/webmasters/v3/sites/{encoded_site}/searchAnalytics/query"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Query top queries
        query_payload = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query"],
            "rowLimit": 50
        }

        # Query top pages
        page_payload = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["page"],
            "rowLimit": 50
        }

        try:
            q_resp = requests.post(url, headers=headers, json=query_payload, timeout=15)
            p_resp = requests.post(url, headers=headers, json=page_payload, timeout=15)

            if q_resp.status_code == 200:
                q_data = q_resp.json()
                q_rows = q_data.get("rows", [])
                
                p_rows = []
                if p_resp.status_code == 200:
                    p_rows = p_resp.json().get("rows", [])

                total_clicks = sum(r.get("clicks", 0) for r in q_rows)
                total_impressions = sum(r.get("impressions", 0) for r in q_rows)
                avg_ctr = f"{(total_clicks / total_impressions * 100):.2f}%" if total_impressions > 0 else "0.0%"
                avg_pos = round(sum(r.get("position", 0) for r in q_rows) / len(q_rows), 1) if q_rows else 0.0

                formatted_queries = [
                    {
                        "query": r.get("keys", [""])[0],
                        "clicks": r.get("clicks", 0),
                        "impressions": r.get("impressions", 0),
                        "ctr": f"{(r.get('ctr', 0) * 100):.2f}%",
                        "position": round(r.get("position", 0), 1)
                    }
                    for r in q_rows
                ]

                formatted_pages = [
                    {
                        "page_url": r.get("keys", [""])[0],
                        "clicks": r.get("clicks", 0),
                        "impressions": r.get("impressions", 0),
                        "ctr": f"{(r.get('ctr', 0) * 100):.2f}%",
                        "position": round(r.get("position", 0), 1)
                    }
                    for r in p_rows
                ]

                return {
                    "success": True,
                    "configured": True,
                    "site_url": clean_site,
                    "timeframe": f"{start_date} s/d {end_date}",
                    "overview": {
                        "totalClicks": total_clicks,
                        "totalImpressions": total_impressions,
                        "averageCtr": avg_ctr,
                        "averagePosition": avg_pos
                    },
                    "queries": formatted_queries,
                    "pages": formatted_pages
                }
            elif q_resp.status_code == 403:
                return {
                    "success": False,
                    "configured": True,
                    "error": f"HTTP 403: Akun service account '{cred_data.get('client_email')}' belum diberikan izin akses ke properti {clean_site} di Search Console.",
                    "overview": {"totalClicks": 0, "totalImpressions": 0, "averageCtr": "0.0%", "averagePosition": 0.0},
                    "queries": [],
                    "pages": []
                }
            else:
                return {
                    "success": False,
                    "configured": True,
                    "error": f"HTTP {q_resp.status_code}: {q_resp.text[:150]}",
                    "overview": {"totalClicks": 0, "totalImpressions": 0, "averageCtr": "0.0%", "averagePosition": 0.0},
                    "queries": [],
                    "pages": []
                }
        except Exception as e:
            logger.error(f"GSC searchAnalytics query exception: {e}")
            return {
                "success": False,
                "configured": True,
                "error": f"Gagal mengambil data dari Google Search Console: {str(e)}",
                "overview": {"totalClicks": 0, "totalImpressions": 0, "averageCtr": "0.0%", "averagePosition": 0.0},
                "queries": [],
                "pages": []
            }
