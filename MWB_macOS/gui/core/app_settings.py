"""
Gestion centralisée des paramètres de l'application.
"""

from __future__ import annotations

import json
from pathlib import Path


DEFAULT_APP_SETTINGS = {
    "log_level": "normal",
    "log_retention_days": 30,
    "closed_pattern_display_mode": "motif",  # motif | words
}


def get_settings_file(project_root: Path) -> Path:
    return project_root / "logs" / "app_settings.json"


def load_app_settings(project_root: Path) -> dict:
    settings = dict(DEFAULT_APP_SETTINGS)
    settings_file = get_settings_file(project_root)

    if settings_file.exists():
        try:
            data = json.loads(settings_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                settings.update(data)
        except Exception:
            pass

    return settings


def save_app_settings(project_root: Path, settings: dict) -> None:
    settings_file = get_settings_file(project_root)
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    merged = dict(DEFAULT_APP_SETTINGS)
    merged.update(settings)
    settings_file.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
