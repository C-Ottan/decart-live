"""Configuration and settings persistence for Decart/Reactor Live Pro.
Stores settings locally in the user's local profile and project directory.
Direct API key connection without intermediate license server.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".decart_live_pro"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_default_config() -> Dict[str, Any]:
    return {
        "api_key": os.getenv("REACTOR_API_KEY", os.getenv("DECART_API_KEY", "")),
        "telegram_url": "https://t.me/p3g4z3us",
        "model": "Realtime Video PRO",
        "editing_type": "style_transfer",
        "reference_image": "",
        "camera_index": 0,
        "target_fps": 30,
        "zoom_factor": 1.0,
        "show_pip": False,
    }


def load_config() -> Dict[str, Any]:
    """Load config from local disk or return defaults."""
    config = get_default_config()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            print(f"[Config] Error loading config: {e}")

    # Fallback to environment variable if saved api_key is empty
    if not config.get("api_key"):
        env_key = os.getenv("REACTOR_API_KEY", os.getenv("DECART_API_KEY", ""))
        if env_key:
            config["api_key"] = env_key

    config["telegram_url"] = "https://t.me/p3g4z3us"
    return config


def save_config(config: Dict[str, Any]):
    """Save config to local disk."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"[Config] Error saving config: {e}")
