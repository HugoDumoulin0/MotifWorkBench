"""
Lancement et préparation de Shiny pour affichage embarqué.
@jcharlesDS (2026)
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
from typing import Any

_SHINY_PROCESS: subprocess.Popen | None = None


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def last_results_json_path() -> Path:
    out = project_root() / "logs" / "last_results_for_shiny.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def save_results_for_shiny(results: dict[str, Any]) -> Path:
    out = last_results_json_path()
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def shiny_url(host: str = "127.0.0.1", port: int = 3838) -> str:
    return f"http://{host}:{port}"

def is_shiny_responding(host: str = "127.0.0.1", port: int = 3838, timeout: float = 1.0) -> bool:
    """Vérifie rapidement si le serveur Shiny répond sur le port."""
    url = shiny_url(host, port)
    try:
        with urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except (URLError, Exception):
        return False

def is_shiny_running(host: str = "127.0.0.1", port: int = 3838) -> bool:
    """Vérifie si Shiny tourne en testant la réponse du serveur."""
    # Vérifier d'abord le processus Python
    if _SHINY_PROCESS is not None and _SHINY_PROCESS.poll() is None:
        return True
    # Si le processus Python n'existe pas/plus, vérifier si le serveur répond quand même
    return is_shiny_responding(host, port, timeout=0.5)

def launch_shiny_embedded(
    json_path: Path,
    host: str = "127.0.0.1",
    port: int = 3838,
) -> subprocess.Popen:
    global _SHINY_PROCESS
    
    script = project_root() / "src" / "Shiny_CA.R"
    if not script.exists():
        raise FileNotFoundError(f"Script Shiny introuvable: {script}")
    if not json_path.exists():
        raise FileNotFoundError(f"JSON résultats introuvable: {json_path}")
    
    if is_shiny_running(host, port):
        return _SHINY_PROCESS

    _SHINY_PROCESS = subprocess.Popen(
        ["Rscript", str(script), str(json_path), host, str(port)],
        stdout=None,
        stderr=None,
        stdin=None,
    )
    return _SHINY_PROCESS

def stop_shiny(host: str = "127.0.0.1", port: int = 3838) -> None:
    """Arrête le serveur Shiny de manière sécurisée."""
    global _SHINY_PROCESS
    
    try:
        # Tenter de terminer le processus Python si disponible
        if _SHINY_PROCESS is not None:
            if _SHINY_PROCESS.poll() is None:
                # Terminer le processus principal
                _SHINY_PROCESS.terminate()
                try:
                    _SHINY_PROCESS.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # Si terminate() ne suffit pas, forcer l'arrêt
                    _SHINY_PROCESS.kill()
                    try:
                        _SHINY_PROCESS.wait(timeout=2)
                    except Exception:
                        pass
            _SHINY_PROCESS = None
        
        # Vérifier si le serveur répond encore
        if is_shiny_responding(host, port, timeout=0.5):
            # Le serveur répond encore, essayer de le tuer avec pkill
            import os
            if os.name != 'nt':  # Linux/macOS
                try:
                    # Essayer pkill pour tuer les processus Rscript liés à Shiny_CA.R
                    subprocess.run(
                        ['pkill', '-f', 'Shiny_CA.R'],
                        capture_output=True,
                        timeout=2
                    )
                except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
                    # pkill n'est pas disponible ou a échoué, ce n'est pas grave
                    pass
    except Exception as e:
        # Ne jamais laisser une exception crash l'application
        print(f"Avertissement lors de l'arrêt de Shiny: {e}")
        # S'assurer que _SHINY_PROCESS est None même en cas d'erreur
        _SHINY_PROCESS = None


def wait_for_shiny(host: str = "127.0.0.1", port: int = 3838, timeout_s: float = 12.0) -> bool:
    url = shiny_url(host, port)
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            with urlopen(url, timeout=1.5) as resp:
                if resp.status == 200:
                    return True
        except URLError:
            time.sleep(0.4)
        except Exception:
            time.sleep(0.4)
    return False