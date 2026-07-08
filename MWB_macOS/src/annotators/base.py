"""
Classe abstraite de base pour tous les annotateurs.
@jcharlesDS (2026)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple


class BaseAnnotator(ABC):
    """Interface commune pour tous les annotateurs linguistiques."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Retourne le nom de l'annotateur."""
        pass
    
    @abstractmethod
    def supports_gpu(self) -> bool:
        """Indique si l'annotateur supporte l'accélération GPU."""
        pass
    
    @abstractmethod
    def get_model_name(self, language: str, use_gpu: bool) -> str:
        """
        Retourne le nom du modèle à utiliser pour une langue et config GPU.
        
        Args:
            language: Code langue ('fr' ou 'en')
            use_gpu: True si GPU activé
            
        Returns:
            Nom du modèle
        """
        pass

    def resolve_model_name(self, language: str, use_gpu: bool) -> str:
        """Retourne le modèle effectivement choisi si l'annotateur sait le résoudre."""
        return self.get_model_name(language, use_gpu)
    
    @abstractmethod
    def check_model_available(self, language: str, use_gpu: bool) -> bool:
        """
        Vérifie si le modèle est disponible localement.
        
        Args:
            language: Code langue ('fr' ou 'en')
            use_gpu: True si GPU activé
            
        Returns:
            True si le modèle est installé
        """
        pass
    
    @abstractmethod
    def download_model(self, language: str, use_gpu: bool, log_callback=None):
        """
        Télécharge le modèle nécessaire.
        
        Args:
            language: Code langue ('fr' ou 'en')
            use_gpu: True si GPU activé
            log_callback: Fonction de callback pour les logs
        """
        pass
    
    @abstractmethod
    def annotate_files(
        self,
        input_files: List[Tuple[str, Path]],  # [(texte_id, path), ...]
        output_dir: Path,
        language: str,
        use_gpu: bool,
        log_callback=None,
        progress_callback=None,
        should_stop_callback=None
    ) -> str:
        """
        Annote une liste de fichiers et génère les fichiers CoNLL-U.
        
        Args:
            input_files: Liste de (texte_id, chemin_fichier_txt)
            output_dir: Dossier de sortie pour les .conllu
            language: Code langue ('fr' ou 'en')
            use_gpu: True si GPU activé
            log_callback: Fonction pour les logs
            progress_callback: Fonction pour la progression (texte_id, current, total)
            should_stop_callback: Fonction retournant True si l'analyse doit s'interrompre
        Returns:
            Nom du modèle effectivement utilisé
        """
        pass
    
    def get_display_name(self) -> str:
        """Retourne le nom affiché dans l'UI (par défaut = get_name())."""
        return self.get_name()
    
    def get_tooltip(self) -> str:
        """Retourne le tooltip pour l'UI."""
        return f"Annotation avec {self.get_name()}"
