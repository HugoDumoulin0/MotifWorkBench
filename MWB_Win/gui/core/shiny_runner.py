"""
Lancement et préparation de Shiny pour affichage embarqué.
@jcharlesDS (2026)
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

try:
    from src.r_runtime import resolve_rscript
except ModuleNotFoundError:
    from r_runtime import resolve_rscript

_SHINY_PROCESS: subprocess.Popen | None = None


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def shiny_log_path() -> Path:
    log_path = project_root() / "logs" / "shiny_runner.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def _read_shiny_log_tail(max_chars: int = 3000) -> str:
    log_path = shiny_log_path()
    if not log_path.exists():
        return ""
    try:
        content = log_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    return content[-max_chars:].strip()


def last_results_json_path() -> Path:
    out = project_root() / "logs" / "last_results_for_shiny.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def _validate_results_for_shiny(results: dict[str, Any]) -> None:
    invalid_entries: list[str] = []

    for key, raw_path in results.items():
        if not isinstance(raw_path, str):
            continue

        key_lower = key.lower()
        if "internal_clustering" not in key_lower or "motif" not in key_lower:
            continue

        if not raw_path.endswith("_FUS.tsv"):
            invalid_entries.append(f"{key} -> {raw_path}")

    if invalid_entries:
        details = "\n".join(invalid_entries[:10])
        raise ValueError(
            "Export Shiny invalide: des jeux de donnees motifs avec clustering interne "
            "ne pointent pas vers des fichiers _FUS.tsv.\n"
            f"{details}"
        )


def save_results_for_shiny(results: dict[str, Any]) -> Path:
    _validate_results_for_shiny(results)
    out = last_results_json_path()
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def shiny_url(host: str = "127.0.0.1", port: int = 3838) -> str:
    return f"http://{host}:{port}"


def is_shiny_responding(host: str = "127.0.0.1", port: int = 3838, timeout: float = 1.0) -> bool:
    """Vérifie rapidement si le serveur Shiny répond sur le port."""
    try:
        with urlopen(shiny_url(host, port), timeout=timeout) as response:
            return response.status == 200
    except (URLError, Exception):
        return False


def is_shiny_running(host: str = "127.0.0.1", port: int = 3838) -> bool:
    """Vérifie si Shiny tourne en testant le processus puis la réponse HTTP."""
    if _SHINY_PROCESS is not None and _SHINY_PROCESS.poll() is None:
        return True
    return is_shiny_responding(host, port, timeout=0.5)


def launch_shiny_embedded(
    json_path: Path,
    host: str = "127.0.0.1",
    port: int = 3838,
) -> subprocess.Popen | None:
    global _SHINY_PROCESS

    script = project_root() / "src" / "Shiny_CA.R"
    if not script.exists():
        raise FileNotFoundError(f"Script Shiny introuvable: {script}")
    if not json_path.exists():
        raise FileNotFoundError(f"JSON résultats introuvable: {json_path}")

    if is_shiny_running(host, port):
        return _SHINY_PROCESS

    rscript = resolve_rscript()
    log_path = shiny_log_path()
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0

    with log_path.open("a", encoding="utf-8", errors="ignore") as log_handle:
        log_handle.write(
            f"\n=== Shiny launch {time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"host={host} port={port} ===\n"
        )
        log_handle.write(f"Rscript: {rscript}\n")
        log_handle.write(f"Script: {script}\n")
        log_handle.write(f"JSON: {json_path}\n")
        log_handle.flush()

        _SHINY_PROCESS = subprocess.Popen(
            [rscript, str(script), str(json_path), host, str(port)],
            stdout=log_handle,
            stderr=log_handle,
            stdin=subprocess.DEVNULL,
            cwd=str(project_root()),
            creationflags=creationflags,
        )

    time.sleep(0.25)
    if _SHINY_PROCESS.poll() is not None:
        details = _read_shiny_log_tail()
        message = "Le processus Shiny s'est arrêté immédiatement."
        if details:
            message += f"\nConsultez {log_path}.\n\nDernières lignes:\n{details}"
        else:
            message += f"\nConsultez {log_path}."
        raise RuntimeError(message)

    return _SHINY_PROCESS


def stop_shiny(host: str = "127.0.0.1", port: int = 3838) -> None:
    """Arrête le serveur Shiny de manière sécurisée."""
    global _SHINY_PROCESS

    try:
        if _SHINY_PROCESS is not None:
            if _SHINY_PROCESS.poll() is None:
                _SHINY_PROCESS.terminate()
                try:
                    _SHINY_PROCESS.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    _SHINY_PROCESS.kill()
                    try:
                        _SHINY_PROCESS.wait(timeout=2)
                    except Exception:
                        pass
            _SHINY_PROCESS = None

        if is_shiny_responding(host, port, timeout=0.5) and os.name != "nt":
            try:
                subprocess.run(
                    ["pkill", "-f", "Shiny_CA.R"],
                    capture_output=True,
                    timeout=2,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
                pass
    except Exception as error:
        print(f"Avertissement lors de l'arrêt de Shiny: {error}")
        _SHINY_PROCESS = None


def wait_for_shiny(host: str = "127.0.0.1", port: int = 3838, timeout_s: float = 12.0) -> bool:
    start = time.time()
    while time.time() - start < timeout_s:
        if _SHINY_PROCESS is not None and _SHINY_PROCESS.poll() is not None:
            return False
        try:
            with urlopen(shiny_url(host, port), timeout=1.5) as response:
                if response.status == 200:
                    return True
        except URLError:
            time.sleep(0.4)
        except Exception:
            time.sleep(0.4)
    return False
