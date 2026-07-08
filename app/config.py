"""Configuration management for the Chatbot application."""

import json
import os
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()


CONFIG_FILE = Path(__file__).parent.parent / "config.json"


class MaaSConfig(BaseModel):
    """Huawei Cloud MaaS configuration."""
    url: str = ""
    api_key: str = ""
    model: str = ""


class AppConfig(BaseModel):
    """Application configuration."""
    maas: MaaSConfig = MaaSConfig()


# ─── Cached config ───────────────────────────────────────────────────
_cached_config: Optional[AppConfig] = None


def load_config(*, force_reload: bool = False) -> AppConfig:
    """Load configuration from environment variables and file (cached).

    Priority order (highest to lowest):
    1. Environment variables (MAAS_URL, MAAS_API_KEY, MAAS_MODEL)
    2. config.json file values

    The result is cached after the first call. Use force_reload=True
    to bypass the cache.
    """
    global _cached_config
    if _cached_config is not None and not force_reload:
        return _cached_config

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        config = AppConfig(**data)
    else:
        config = AppConfig()

    # Override with environment variables if set
    env_url = os.getenv("MAAS_URL", "").strip()
    if env_url:
        config.maas.url = env_url

    env_api_key = os.getenv("MAAS_API_KEY", "").strip()
    if env_api_key:
        config.maas.api_key = env_api_key

    env_model = os.getenv("MAAS_MODEL", "").strip()
    if env_model:
        config.maas.model = env_model

    _cached_config = config
    return config


def mask_api_key(api_key: str) -> str:
    """Return a masked version of the API key for display.

    Shows only the last 4 characters, replacing the rest with asterisks.
    Returns an empty string if the key is empty.
    """
    if not api_key:
        return ""
    if len(api_key) <= 4:
        return "****"
    return "*" * (len(api_key) - 4) + api_key[-4:]
