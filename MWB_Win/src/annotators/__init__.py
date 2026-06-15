"""
Package pour l'annotation morphosyntaxique multi-outils.
Supporte: Stanza, spaCy

@jcharlesDS (2026)
"""

from .base import BaseAnnotator
from .stanza_annotator import StanzaAnnotator
from .spacy_annotator import SpacyAnnotator

__all__ = ["BaseAnnotator", "StanzaAnnotator", "SpacyAnnotator"]


def get_annotator(tool_name: str) -> BaseAnnotator:
    """
    Factory pour obtenir le bon annotateur selon le nom.
    
    Args:
        tool_name: "stanza" ou "spacy"
    
    Returns:
        Instance de l'annotateur correspondant
    
    Raises:
        ValueError: Si le nom d'outil est inconnu
    """
    tool_name = tool_name.lower()
    
    if tool_name == "stanza":
        return StanzaAnnotator()
    elif tool_name == "spacy":
        return SpacyAnnotator()
    else:
        raise ValueError(
            f"Outil d'annotation inconnu: '{tool_name}'. "
            f"Choix possibles: stanza, spacy"
        )
