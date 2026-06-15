"""
Détection du GPU disponible pour accélérer l'annotation Stanza
@jcharlesDS (2026)
"""

def detect_gpu() -> tuple[bool, str]:
    """
    Détecte si un GPU compatible est disponible pour Stanza.
    Retourne un tuple (gpu_disponible [bool], description [str]).
    """
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            return True, f"{name} (CUDA)"
        if torch.backends.mps.is_available():
            return True, "Apple Silicon (MPS)"
    except ImportError:
        return False, "PyTorch non installé, impossible de détecter le GPU"
    
    # Aucun GPU compatible trouvé
    return False, "Aucun GPU compatible détecté, passage en mode CPU."