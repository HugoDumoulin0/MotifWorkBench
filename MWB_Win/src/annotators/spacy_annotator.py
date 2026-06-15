"""
Annotateur basé sur spaCy (rapide, bon compromis).
@jcharlesDS (2026)
"""

import subprocess
import sys
from typing import List
from .base import BaseAnnotator


class SpacyAnnotator(BaseAnnotator):
    """Annotateur utilisant spaCy avec conversion CoNLL-U."""
    
    # Modèles Transformer (optimisés GPU)
    MODELS_GPU = {
        "fr": "fr_dep_news_trf",
        "en": "en_core_web_trf",
    }
    
    # Modèles Large (optimisés CPU - 5-6× plus rapides que trf en CPU)
    MODELS_CPU = {
        "fr": "fr_core_news_lg",
        "en": "en_core_web_lg",
    }
    
    def __init__(self):
        super().__init__()
        self._spacy = None
        self._spacy_conll = None
    
    def get_name(self) -> str:
        return "spaCy"
    
    def supports_gpu(self) -> bool:
        """spaCy supporte l'accélération GPU (avec modèles Transformer)."""
        return True
    
    def check_installation(self) -> bool:
        """Vérifie si spaCy et spacy-conll sont installés."""
        try:
            import spacy
            import spacy_conll
            self._spacy = spacy
            self._spacy_conll = spacy_conll
            return True
        except ImportError:
            return False
    
    def get_installation_instructions(self) -> str:
        return (
            "spaCy n'est pas installé.\n\n"
            "Pour l'installer, exécutez:\n"
            "  pip install spacy spacy-conll\n\n"
            "Ou réinstallez le programme complet avec l'installer."
        )
    
    def get_resolved_model_name(self, language: str, **kwargs) -> str:
        use_gpu = kwargs.get("use_gpu", True)
        models_dict = self.MODELS_GPU if use_gpu else self.MODELS_CPU
        return models_dict.get(language, "")

    def check_models(self, language: str, use_gpu: bool = True) -> bool:
        """
        Vérifie et télécharge les modèles spaCy si nécessaires.
        Choisit automatiquement le meilleur modèle selon GPU/CPU.
        
        Args:
            language: Code langue (fr, en)
            use_gpu: True pour modèle Transformer (GPU), False pour modèle Large (CPU)
        """
        if not self.check_installation():
            return False
        
        # Sélectionner le bon modèle selon GPU/CPU
        models_dict = self.MODELS_GPU if use_gpu else self.MODELS_CPU
        model_name = models_dict.get(language)
        
        if not model_name:
            print(f"⚠ Langue '{language}' non supportée par spaCy")
            return False
        
        model_type = "Transformer (GPU)" if use_gpu else "Large (CPU optimisé)"
        
        # Vérifier si le modèle est installé
        try:
            self._spacy.load(model_name)
            print(f"✓ Modèle spaCy '{model_name}' ({model_type}) déjà installé.")
            return True
        except OSError:
            # Modèle manquant : télécharger
            print(f"Téléchargement du modèle spaCy '{model_name}' ({model_type})...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "spacy", "download", model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                print(f"✓ Modèle '{model_name}' téléchargé avec succès.")
                return True
            except subprocess.CalledProcessError as e:
                print(f"⚠ Erreur lors du téléchargement du modèle : {e}")
                return False
    
    def annotate_file(self, input_path: str, output_path: str, language: str, use_gpu: bool = False):
        """Annote un fichier avec spaCy et génère un CoNLL-U."""
        if not self.check_installation():
            raise RuntimeError(self.get_installation_instructions())
        
        # Sélectionner le bon modèle selon GPU/CPU
        models_dict = self.MODELS_GPU if use_gpu else self.MODELS_CPU
        model_name = models_dict.get(language)
        
        if not model_name:
            raise ValueError(f"Langue '{language}' non supportée par spaCy")
        
        # Configurer l'utilisation du GPU ou CPU
        if use_gpu:
            # Tenter d'activer le GPU (silencieux si indisponible)
            try:
                self._spacy.prefer_gpu()
            except:
                pass  # GPU non disponible, continuera en CPU
        else:
            # Forcer l'utilisation du CPU
            self._spacy.require_cpu()
        
        # Charger le modèle avec le composant CoNLL-U
        nlp = self._spacy.load(model_name)
        
        # Ajouter le formateur CoNLL-U avec configuration par défaut
        nlp.add_pipe("conll_formatter", last=True, config={
            "field_names": {},  # Utilise les noms de champs par défaut
            "conversion_maps": {}
        })
        
        # Lire le texte
        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Annoter
        doc = nlp(text)
        
        # Écrire en CoNLL-U
        conll_output = doc._.conll_str
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(conll_output)
    
    def get_available_languages(self) -> List[str]:
        """Langues supportées (restreint à FR/EN avec modèles Transformer)."""
        return ["fr", "en"]
