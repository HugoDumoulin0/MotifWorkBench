"""
Système modulaire d'annotation linguistique.
Supporte SpaCy et Stanza avec détection/installation automatique des modèles.
@jcharlesDS (2026)
"""

from .base import BaseAnnotator
from .stanza_annotator import StanzaAnnotator
from .spacy_annotator import SpacyAnnotator

# Registre des annotateurs disponibles
ANNOTATORS = {
    "stanza": StanzaAnnotator(),
    "spacy": SpacyAnnotator(),
}

def get_annotator(name: str) -> BaseAnnotator:
    """Retourne l'annotateur demandé."""
    if name not in ANNOTATORS:
        raise ValueError(f"Annotateur '{name}' inconnu. Disponibles: {list(ANNOTATORS.keys())}")
    return ANNOTATORS[name]

__all__ = ["BaseAnnotator", "get_annotator", "ANNOTATORS"]
