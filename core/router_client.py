import os
import json
import logging
import sqlite3
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger("router_client")

CONFIG_PATH = "data/router_config.json"

class LLMRouterClient:
    """
    Client for LLM Routers (specifically 9router on port 20128, OpenRouter, or any OpenAI-compatible router).
    Features:
    1. Dynamic model discovery via `GET /v1/models` (No hardcoded/fictitious model lists).
    2. Auto-detection of local 9router installation and active API keys.
    3. Standard Chat Completions for 12-block SEO article generation.
    4. Model selection & settings persistence.
    """

    def __init__(self, config_path: str = CONFIG_PATH):
        self.config_path = config_path
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        self.config = {
            "base_url": "http://127.0.0.1:20128/v1",
            "api_key": "",
            "selected_model": "ox-alpha",
            "temperature": 0.7,
            "max_tokens": 4096
        }
        self.load_config()
        self.auto_detect_9router()

    def load_config(self):
        """Loads router settings from file if present."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except Exception as e:
                logger.warning(f"Could not load router config: {e}")

    def save_config(self):
        """Persists router settings to file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save router config: {e}")

    def auto_detect_9router(self):
        """Auto-detects local 9router running at port 20128 and retrieves default key."""
        # If API key is empty, attempt to read from 9router SQLite database
        if not self.config.get("api_key"):
            nine_db_path = os.path.expanduser("~/.9router/db/data.sqlite")
            if os.path.exists(nine_db_path):
                try:
                    conn = sqlite3.connect(nine_db_path)
                    cur = conn.cursor()
                    cur.execute("SELECT key FROM apiKeys WHERE isActive = 1 ORDER BY createdAt ASC LIMIT 1;")
                    row = cur.fetchone()
                    if row and row[0]:
                        self.config["api_key"] = row[0]
                        self.save_config()
                        logger.info(f"[RouterClient] Auto-detected 9router API key: {row[0][:8]}...")
                    conn.close()
                except Exception as e:
                    logger.warning(f"Could not auto-read 9router DB: {e}")

    def check_health(self) -> Dict[str, Any]:
        """Checks if the router is reachable."""
        base_url = self.config.get("base_url", "http://127.0.0.1:20128/v1").rstrip("/")
        models_url = f"{base_url}/models"
        headers = {}
        if self.config.get("api_key"):
            headers["Authorization"] = f"Bearer {self.config['api_key']}"

        try:
            resp = requests.get(models_url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models_list = data.get("data", [])
                return {
                    "online": True,
                    "status": "connected",
                    "base_url": base_url,
                    "models_count": len(models_list),
                    "selected_model": self.config.get("selected_model")
                }
            elif resp.status_code == 401:
                return {
                    "online": True,
                    "status": "unauthorized",
                    "error": "API Key Router diperlukan atau tidak valid.",
                    "base_url": base_url
                }
            else:
                return {
                    "online": False,
                    "status": "error",
                    "error": f"HTTP {resp.status_code}: {resp.text[:120]}",
                    "base_url": base_url
                }
        except Exception as e:
            return {
                "online": False,
                "status": "offline",
                "error": f"Tidak dapat terhubung ke Router ({str(e)})",
                "base_url": base_url
            }

    def fetch_models(self, base_url: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Dynamically fetches available models from the router via GET /models.
        Returns real live models list (never hardcoded/fictitious).
        """
        url = (base_url or self.config.get("base_url", "http://127.0.0.1:20128/v1")).rstrip("/")
        models_url = f"{url}/models"
        key = api_key if api_key is not None else self.config.get("api_key", "")
        
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"

        try:
            resp = requests.get(models_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                raw_models = data.get("data", [])
                
                formatted_models = []
                for m in raw_models:
                    model_id = m.get("id") if isinstance(m, dict) else str(m)
                    owned_by = m.get("owned_by", "router") if isinstance(m, dict) else "router"
                    caps = m.get("capabilities", {}) if isinstance(m, dict) else {}
                    formatted_models.append({
                        "id": model_id,
                        "name": model_id,
                        "owned_by": owned_by,
                        "context_length": m.get("context_length", 128000),
                        "has_vision": caps.get("vision", False)
                    })

                # Sort by ID
                formatted_models.sort(key=lambda x: x["id"])
                
                # If current selected model is not in list, set to first available or 'ox-alpha'
                model_ids = [m["id"] for m in formatted_models]
                if formatted_models and self.config.get("selected_model") not in model_ids:
                    if "ox-alpha" in model_ids:
                        self.config["selected_model"] = "ox-alpha"
                    elif "kr/auto" in model_ids:
                        self.config["selected_model"] = "kr/auto"
                    else:
                        self.config["selected_model"] = formatted_models[0]["id"]
                    self.save_config()

                return {
                    "success": True,
                    "count": len(formatted_models),
                    "models": formatted_models,
                    "selected_model": self.config.get("selected_model")
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {resp.status_code}: {resp.text[:150]}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Gagal mengambil model dari Router: {str(e)}"
            }

    def update_settings(self, base_url: str, api_key: str, selected_model: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Updates and saves router configuration."""
        self.config["base_url"] = base_url.strip().rstrip("/")
        self.config["api_key"] = api_key.strip()
        self.config["selected_model"] = selected_model.strip()
        self.config["temperature"] = temperature
        self.save_config()
        return {"success": True, "config": self.config}

    def generate_chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: Optional[float] = None) -> Optional[str]:
        """
        Sends a Chat Completion request to the router.
        Handles standard OpenAI JSON output.
        """
        base_url = self.config.get("base_url", "http://127.0.0.1:20128/v1").rstrip("/")
        url = f"{base_url}/chat/completions"
        target_model = model or self.config.get("selected_model", "ox-alpha")
        temp = temperature if temperature is not None else self.config.get("temperature", 0.7)

        headers = {
            "Content-Type": "application/json"
        }
        if self.config.get("api_key"):
            headers["Authorization"] = f"Bearer {self.config['api_key']}"

        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temp,
            "stream": False
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=45)
            if resp.status_code == 200:
                # Check if JSON
                try:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"].get("content", "")
                except Exception:
                    pass

                # If returned SSE lines
                lines = resp.text.split("\n")
                collected = []
                for line in lines:
                    line = line.strip()
                    if line.startswith("data: "):
                        data_part = line[6:].strip()
                        if data_part and data_part != "[DONE]":
                            try:
                                chunk = json.loads(data_part)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                if "content" in delta:
                                    collected.append(delta["content"])
                            except Exception:
                                pass
                if collected:
                    return "".join(collected)
            else:
                logger.warning(f"[RouterClient] Error {resp.status_code}: {resp.text[:150]}")
                return None
        except Exception as e:
            logger.error(f"[RouterClient] Request exception: {e}")
            return None
