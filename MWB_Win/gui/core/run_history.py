"""
Gestion d'un historique JSON des exécutions d'analyse.
@jcharlesDS (2026)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _history_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    hist_dir = root / "logs"
    hist_dir.mkdir(parents=True, exist_ok=True)
    return hist_dir / "run_history.json"


def load_run_history() -> list[dict[str, Any]]:
    path = _history_path()
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    if isinstance(data, list):
        return data
    return []


def append_run_history(entry: dict[str, Any]) -> None:
    history = load_run_history()
    history.insert(0, entry)  # plus récent en premier
    history = history[:500] # garder une taille raisonnable

    path = _history_path()
    path.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_run_history() -> None:
    """Supprime l'historique des exécutions."""
    path = _history_path()
    if path.exists():
        path.unlink()


def build_run_entry(
    status: str,
    duration_seconds: float,
    config: dict[str, Any],
    details: str = "",
) -> dict[str, Any]:
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,  # success | error | stopped
        "duration_seconds": round(max(duration_seconds, 0.0), 2),
        "language": config.get("language", ""),
        "use_gpu": bool(config.get("use_gpu", False)),
        "threads": config.get("threads", ""),
        "minsup": config.get("list_minsup_percent", []),
        "details": details,
    }
