"""
config_manager.py — Manages persistent configuration (API key) via config.json.

The config file is stored next to the executable (or script) so it persists
between sessions and is never committed to version control.
"""

import json
import os
import sys


def _get_config_dir() -> str:
    """Return the directory where config.json should live.

    When running as a PyInstaller bundle the config sits next to the .exe.
    When running as a plain script it sits in the project directory.
    """
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller .exe
        return os.path.dirname(sys.executable)
    else:
        # Running as a script
        return os.path.dirname(os.path.abspath(__file__))


CONFIG_PATH = os.path.join(_get_config_dir(), "config.json")

_DEFAULT_CONFIG = {
    "api_key": "",
}


def load_config() -> dict:
    """Load configuration from config.json. Returns defaults if missing."""
    if not os.path.exists(CONFIG_PATH):
        return dict(_DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge with defaults so new keys are always present
        merged = dict(_DEFAULT_CONFIG)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    """Save configuration dict to config.json."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
