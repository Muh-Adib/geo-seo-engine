import os
import json
import base64
import logging
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger("gemini_auth")

ACCOUNTS_FILE = "data/gemini_accounts.json"

class GeminiAuthManager:
    """
    Manages multi-account authentication for Google Gemini & Imagen.
    Supports:
    1. Multi-Account Google Gemini API Key Pool with automatic rotation and quota failover.
    2. Transparent token verification and diagnostic status reporting.
    3. Detection of local Antigravity/Gemini Desktop session with permission diagnostic.
    """

    def __init__(self, accounts_path: str = ACCOUNTS_FILE):
        self.accounts_path = accounts_path
        os.makedirs(os.path.dirname(self.accounts_path), exist_ok=True)
        self.accounts: List[Dict[str, Any]] = []
        self.current_index = 0
        self.load_accounts()
        
        # Load from .env if accounts empty
        if not self.accounts:
            self.load_from_env()

    def load_from_env(self):
        """Loads GEMINI_API_KEY from environment or .env if present."""
        env_keys = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEYS", "")
        if env_keys:
            for idx, raw_key in enumerate(env_keys.split(",")):
                clean_key = raw_key.strip()
                if clean_key:
                    self.accounts.append({
                        "id": f"env-key-{idx+1}",
                        "email": f"gemini-key-{idx+1}",
                        "auth_type": "api_key",
                        "credential": clean_key,
                        "is_active": True,
                        "source": "Environment (.env)",
                        "status": "active"
                    })
            self.save_accounts()

    def load_accounts(self):
        """Loads saved multi-account credentials from storage."""
        if os.path.exists(self.accounts_path):
            try:
                with open(self.accounts_path, "r") as f:
                    self.accounts = json.load(f)
            except Exception as e:
                logger.error(f"Error loading gemini accounts: {e}")
                self.accounts = []
        else:
            self.accounts = []

    def save_accounts(self):
        """Persists accounts to storage."""
        try:
            with open(self.accounts_path, "w") as f:
                json.dump(self.accounts, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving gemini accounts: {e}")

    def add_account(self, email: str, credential: str, auth_type: str = "api_key") -> Dict[str, Any]:
        """
        Adds a Google Gemini API Key or OAuth token with live verification.
        """
        clean_cred = credential.strip()
        if not clean_cred:
            return {"success": False, "error": "API Key / Credential cannot be empty."}

        account_id = f"acc-{len(self.accounts)+1}"
        
        # Live test against Google Gemini API
        test_res = self.verify_credential(clean_cred, auth_type)
        if not test_res.get("valid"):
            return {
                "success": False,
                "error": f"Verifikasi gagal: {test_res.get('error')}. Pastikan API Key aktif di Google AI Studio (aistudio.google.com)."
            }

        new_acc = {
            "id": account_id,
            "email": email.strip() or f"gemini-{len(self.accounts)+1}@ai.google",
            "auth_type": auth_type,
            "credential": clean_cred,
            "is_active": True,
            "source": "Google AI Studio API Key",
            "model_tested": test_res.get("model", "gemini-2.0-flash"),
            "status": "verified"
        }

        # Check if already exists
        for acc in self.accounts:
            if acc.get("credential") == clean_cred:
                acc["is_active"] = True
                acc["status"] = "verified"
                self.save_accounts()
                return {"success": True, "account": acc, "message": "Akun sudah ada dan status diperbarui menjadi verified."}

        self.accounts.append(new_acc)
        self.save_accounts()
        return {"success": True, "account": new_acc}

    def remove_account(self, account_id: str) -> bool:
        """Removes an account by ID."""
        initial_len = len(self.accounts)
        self.accounts = [a for a in self.accounts if a.get("id") != account_id and a.get("email") != account_id]
        if len(self.accounts) < initial_len:
            self.save_accounts()
            return True
        return False

    def get_accounts_summary(self) -> Dict[str, Any]:
        """Returns safe list of accounts with connection diagnostics for UI."""
        token_path = os.path.expanduser("~/.gemini/jetski-standalone-oauth-token")
        has_antigravity = os.path.exists(token_path)

        summary = []
        for idx, acc in enumerate(self.accounts):
            cred = acc.get("credential") or acc.get("access_token", "")
            masked = f"{cred[:7]}...{cred[-4:]}" if len(cred) > 12 else "***"
            summary.append({
                "id": acc.get("id"),
                "email": acc.get("email"),
                "auth_type": acc.get("auth_type"),
                "source": acc.get("source"),
                "is_current": idx == self.current_index,
                "is_active": acc.get("is_active", True),
                "status": acc.get("status", "ready"),
                "model_tested": acc.get("model_tested", "gemini-2.0-flash"),
                "masked_credential": masked
            })

        active_count = len([a for a in summary if a.get("is_active")])

        return {
            "has_local_antigravity": has_antigravity,
            "accounts_count": len(self.accounts),
            "active_accounts": active_count,
            "accounts": summary
        }

    def get_active_auth_headers_or_param(self) -> Optional[Dict[str, Any]]:
        """
        Returns headers or query params for Gemini API calls.
        Rotates automatically across verified accounts.
        """
        if not self.accounts:
            env_key = os.getenv("GEMINI_API_KEY")
            if env_key:
                return {"type": "query", "param": {"key": env_key.strip()}, "headers": {}}
            return None

        # Filter active accounts
        active_pool = [a for a in self.accounts if a.get("is_active", True)]
        if not active_pool:
            return None

        acc = active_pool[self.current_index % len(active_pool)]
        cred = acc.get("credential") or acc.get("access_token", "")

        if acc.get("auth_type") == "oauth_token" or acc.get("auth_type") == "antigravity_desktop":
            return {
                "type": "bearer",
                "headers": {"Authorization": f"Bearer {cred}"},
                "param": {},
                "account_id": acc.get("id"),
                "email": acc.get("email")
            }
        else:
            return {
                "type": "query",
                "param": {"key": cred},
                "headers": {},
                "account_id": acc.get("id"),
                "email": acc.get("email")
            }

    def rotate(self):
        """Switches to the next connected account on 429 quota exhaustion."""
        if not self.accounts:
            return
        self.current_index = (self.current_index + 1) % len(self.accounts)
        logger.info(f"[GeminiAuth] Rotated to account index {self.current_index}: {self.accounts[self.current_index].get('email')}")

    def verify_credential(self, credential: str, auth_type: str = "api_key") -> Dict[str, Any]:
        """Tests validity of a credential against Google Gemini API."""
        models_to_test = ["gemini-2.0-flash", "gemini-1.5-flash"]
        clean_cred = credential.strip()

        for model in models_to_test:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                if auth_type in ["oauth_token", "antigravity_desktop"]:
                    headers = {
                        "Authorization": f"Bearer {clean_cred}",
                        "Content-Type": "application/json"
                    }
                    params = {}
                else:
                    headers = {"Content-Type": "application/json"}
                    params = {"key": clean_cred}

                payload = {
                    "contents": [{"parts": [{"text": "Hello, respond with OK"}]}],
                    "generationConfig": {"maxOutputTokens": 5}
                }
                resp = requests.post(url, headers=headers, params=params, json=payload, timeout=8)
                if resp.status_code == 200:
                    return {"valid": True, "model": model, "status": "200 OK"}
                elif resp.status_code == 429:
                    return {"valid": True, "model": model, "status": "Quota Exceeded (429), Key is valid"}
            except Exception as e:
                logger.warning(f"Error testing model {model}: {e}")

        # If both failed, make one final call to capture error message
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
            if auth_type in ["oauth_token", "antigravity_desktop"]:
                headers = {"Authorization": f"Bearer {clean_cred}", "Content-Type": "application/json"}
                params = {}
            else:
                headers = {"Content-Type": "application/json"}
                params = {"key": clean_cred}
            resp = requests.post(url, headers=headers, params=params, json={"contents": [{"parts": [{"text": "Ping"}]}]}, timeout=6)
            error_msg = f"HTTP {resp.status_code}: {resp.json().get('error', {}).get('message', resp.text[:120])}"
            return {"valid": False, "error": error_msg}
        except Exception as e:
            return {"valid": False, "error": str(e)}
