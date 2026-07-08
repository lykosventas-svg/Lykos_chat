"""Configuration management for the Chatbot application."""

import json
import os
from pathlib import Path
from pydantic import BaseModel
from typing import Optional


CONFIG_FILE = Path(__file__).parent.parent / "config.json"


class MaaSConfig(BaseModel):
    """Huawei Cloud MaaS configuration."""
    url: str = ""
    api_key: str = ""
    model: str = ""


class AppConfig(BaseModel):
    """Application configuration."""
    maas: MaaSConfig = MaaSConfig()


def load_config() -> AppConfig:
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AppConfig(**data)
    return AppConfig()


def save_config(config: AppConfig) -> None:
    """Save configuration to file."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
