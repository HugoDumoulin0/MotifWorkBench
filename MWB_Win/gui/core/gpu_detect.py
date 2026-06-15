"""
Détection du GPU disponible pour accélérer l'annotation Stanza.
@jcharlesDS (2026)
"""

from __future__ import annotations

import subprocess


def _detect_nvidia_gpu_name() -> str | None:
    """Retourne le nom du premier GPU NVIDIA vu par le pilote, si disponible."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0:
        return None

    lines = [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
    return lines[0] if lines else None


def detect_gpu() -> tuple[bool, str]:
    """
    Détecte si un GPU compatible est disponible pour l'annotation.
    Retourne un tuple (gpu_disponible [bool], description [str]).
    """
    try:
        import torch

        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            return True, f"{name} (CUDA)"

        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return True, "Apple Silicon (MPS)"

        nvidia_name = _detect_nvidia_gpu_name()
        if nvidia_name:
            torch_version = getattr(torch, "__version__", "inconnue")
            cuda_runtime = getattr(torch.version, "cuda", None)
            if "+cpu" in torch_version or not cuda_runtime:
                return False, f"GPU NVIDIA détecté ({nvidia_name}) mais PyTorch CPU-only installé ({torch_version})."
            return False, f"GPU NVIDIA détecté ({nvidia_name}) mais CUDA n'est pas activé dans PyTorch."

    except ImportError:
        return False, "PyTorch non installé, impossible de détecter le GPU."

    return False, "Aucun GPU compatible détecté, passage en mode CPU."
