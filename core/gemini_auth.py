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
    1. Automatic 1-Click detection from Antigravity / Gemini Desktop (~/.gemini/jetski-standalone-oauth-token)
    2. Multi-Account Google OAuth & API Key Pool with automatic rotation and quota failover
    """

    def __init__(self, accounts_path: str = ACCOUNTS_FILE):
        self.accounts_path = accounts_path
        os.makedirs(os.path.dirname(self.accounts_path), exist_ok=True)
        self.accounts: List[Dict[str, Any]] = []
        self.current_index = 0
        self.load_accounts()
        
        # Auto-detect Antigravity login on startup if accounts is empty
        if not self.accounts:
            self.auto_connect_antigravity()

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

    def auto_connect_antigravity(self) -> Optional[Dict[str, Any]]:
        """
        Detects existing active Antigravity / Gemini Desktop token on this Mac.
        """
        token_path = os.path.expanduser("~/.gemini/jetski-standalone-oauth-token")
        if not os.path.exists(token_path):
            return None

        try:
            with open(token_path, "r") as f:
                data = json.load(f)

            access_token = data.get("token")
            id_token = data.get("id_token", "")
            
            # Extract email from JWT payload without external library
            email = "antigravity-user@google.com"
            parts = id_token.split(".")
            if len(parts) >= 2:
                try:
                    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
                    email = payload.get("email", email)
                except Exception:
                    pass

            account = {
                "id": f"antigravity-{email}",
                "email": email,
                "auth_type": "antigravity_desktop",
                "access_token": access_token,
                "token_path": token_path,
                "is_active": True,
                "source": "Antigravity Desktop Login"
            }

            # Update or append
            existing = next((a for a in self.accounts if a["email"] == email), None)
            if not existing:
                self.accounts.append(account)
            else:
                existing["access_token"] = access_token
                existing["is_active"] = True

            self.save_accounts()
            logger.info(f"[GeminiAuth] Auto-connected Antigravity account: {email}")
            return account
        except Exception as e:
            logger.warning(f"[GeminiAuth] Could not read Antigravity token: {e}")
            return None

    def add_account(self, email: str, credential: str, auth_type: str = "api_key") -> Dict[str, Any]:
        """
        Adds an additional Google Gemini account (API Key or OAuth Token) for multi-account pooling.
        """
        clean_cred = credential.strip()
        account_id = f"acc-{len(self.accounts)+1}"
        
        # Test if valid
        valid = self.verify_credential(clean_cred, auth_type)
        if not valid["valid"]:
            return {"success": False, "error": valid.get("error", "Credential test failed")}

        new_acc = {
            "id": account_id,
            "email": email.strip() or f"account-{len(self.accounts)+1}@google.com",
            "auth_type": auth_type, # 'api_key' or 'oauth_token'
            "credential": clean_cred,
            "is_active": True,
            "source": "Manual Google Account Connection"
        }

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

    def get_accounts_summary(self) -> List[Dict[str, Any]]:
        """Returns safe list of accounts for UI display."""
        # Re-check Antigravity token on refresh
        token_path = os.path.expanduser("~/.gemini/jetski-standalone-oauth-token")
        has_antigravity = os.path.exists(token_path)

        summary = []
        for idx, acc in enumerate(self.accounts):
            cred = acc.get("credential") or acc.get("access_token", "")
            masked = f"{cred[:6]}...{cred[-4:]}" if len(cred) > 10 else "***"
            summary.append({
                "id": acc.get("id"),
                "email": acc.get("email"),
                "auth_type": acc.get("auth_type"),
                "source": acc.get("source"),
                "is_current": idx == self.current_index,
                "masked_credential": masked
            })

        return {
            "has_local_antigravity": has_antigravity,
            "accounts_count": len(self.accounts),
            "accounts": summary
        }

    def get_active_auth_headers_or_param(self) -> Optional[Dict[str, Any]]:
        """
        Returns headers or query params for Gemini API calls.
        Rotates automatically across all connected accounts.
        """
        if not self.accounts:
            # Fallback to .env GEMINI_API_KEY if exists
            env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEYS", "")
            if env_key:
                clean_key = env_key.split(",")[0].strip()
                return {"type": "query", "param": {"key": clean_key}, "headers": {}}
            return None

        # Re-read Antigravity token if expired
        acc = self.accounts[self.current_index % len(self.accounts)]
        if acc.get("auth_type") == "antigravity_desktop":
            token_path = acc.get("token_path")
            if token_path and os.path.exists(token_path):
                try:
                    with open(token_path, "r") as f:
                        data = json.load(f)
                    acc["access_token"] = data.get("token")
                except Exception:
                    pass
            
            return {
                "type": "bearer",
                "headers": {"Authorization": f"Bearer {acc['access_token']}"},
                "param": {}
            }
        else:
            # API key or OAuth Token
            cred = acc.get("credential", "")
            if acc.get("auth_type") == "oauth_token":
                return {
                    "type": "bearer",
                    "headers": {"Authorization": f"Bearer {cred}"},
                    "param": {}
                }
            else:
                return {
                    "type": "query",
                    "param": {"key": cred},
                    "headers": {}
                }

    def rotate(self):
        """Switches to the next connected account on 429 quota exhaustion."""
        if not self.accounts:
            return
        self.current_index = (self.current_index + 1) % len(self.accounts)
        logger.info(f"[GeminiAuth] Rotated to account index {self.current_index}: {self.accounts[self.current_index].get('email')}")

    def verify_credential(self, credential: str, auth_type: str) -> Dict[str, Any]:
        """Tests validity of a credential against Gemini API."""
        try:
            if auth_type == "oauth_token":
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                headers = {
                    "Authorization": f"Bearer {credential}",
                    "Content-Type": "application/json"
                }
                params = {}
            else:
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                headers = {"Content-Type": "application/json"}
                params = {"key": credential}

            payload = {
                "contents": [{"parts": [{"text": "Ping"}]}],
                "generationConfig": {"maxOutputTokens": 3}
            }
            resp = requests.post(url, headers=headers, params=params, json=payload, timeout=8)
            if resp.status_code == 200:
                return {"valid": True}
            return {"valid": False, "error": f"HTTP {resp.status_code}: {resp.text[:120]}"}
        except Exception as e:
            return {"valid": False, "error": str(e)}
