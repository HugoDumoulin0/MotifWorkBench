"""
Classe de base abstraite pour les annotateurs morphosyntaxiques.

@jcharlesDS (2026)
"""

from abc import ABC, abstractmethod
from typing import Callable, List


class BaseAnnotator(ABC):
    """Interface commune pour tous les annotateurs."""

    def __init__(self):
        self._log_callback: Callable[[str], None] | None = None

    def set_log_callback(self, log_callback: Callable[[str], None] | None) -> None:
        """Enregistre un callback de log optionnel."""
        self._log_callback = log_callback

    def get_resolved_model_name(self, language: str, **kwargs) -> str:
        """Retourne le nom du modèle effectivement choisi, si disponible."""
        return ""

    def _log(self, message: str) -> None:
        """Émet un message via le callback si présent, sinon sur stdout."""
        if self._log_callback:
            self._log_callback(message)
        else:
            print(message)
    
    @abstractmethod
    def check_installation(self) -> bool:
        """
        Vérifie si l'outil est installé.
        
        Returns:
            True si installé, False sinon
        """
        pass
    
    @abstractmethod
    def get_installation_instructions(self) -> str:
        """
        Retourne les instructions d'installation si l'outil manque.
        
        Returns:
            Message d'aide pour installer l'outil
        """
        pass
    
    @abstractmethod
    def check_models(self, language: str, **kwargs) -> bool:
        """
        Vérifie si les modèles pour la langue sont présents.
        Télécharge automatiquement si absents.
        
        Args:
            language: Code langue (fr, en, etc.)
            **kwargs: Paramètres additionnels spécifiques à l'annotateur
        
        Returns:
            True si modèles disponibles, False si erreur
        """
        pass
    
    @abstractmethod
    def annotate_file(self, input_path: str, output_path: str, language: str, use_gpu: bool = False):
        """
        Annote un fichier texte et produit un fichier CoNLL-U.
        
        Args:
            input_path: Chemin du fichier texte brut
            output_path: Chemin du fichier CoNLL-U de sortie
            language: Code langue (fr, en, etc.)
            use_gpu: Utiliser le GPU si disponible
        """
        pass
    
    @abstractmethod
    def get_available_languages(self) -> List[str]:
        """
        Liste des langues supportées par cet annotateur.
        
        Returns:
            Liste de codes langue (ex: ["fr", "en", "es"])
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Nom de l'annotateur.
        
        Returns:
            Nom de l'outil (ex: "Stanza", "spaCy")
        """
        pass
    
    @abstractmethod
    def supports_gpu(self) -> bool:
        """
        Indique si l'annotateur supporte l'accélération GPU.
        
        Returns:
            True si GPU supporté, False sinon
        """
        pass
