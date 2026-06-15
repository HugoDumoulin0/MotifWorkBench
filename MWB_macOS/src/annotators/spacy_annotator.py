"""
Annotateur SpaCy.
Utilise modèles Transformers (trf) avec GPU, modèles large (lg) pour CPU.
@jcharlesDS (2026)
"""

import spacy
from spacy_conll import init_parser
from pathlib import Path
from typing import List, Tuple
import subprocess
import sys

from .base import BaseAnnotator


class SpacyAnnotator(BaseAnnotator):
    """Annotateur utilisant SpaCy."""

    def _model_candidates(self, language: str, use_gpu: bool) -> list[str]:
        """Retourne une liste ordonnée de candidats plausibles pour SpaCy."""
        lang = language.strip().lower()
        if use_gpu:
            return [
                f"{lang}_dep_news_trf",
                f"{lang}_core_news_trf",
                f"{lang}_core_web_trf",
            ]
        return [
            f"{lang}_core_news_lg",
            f"{lang}_core_web_lg",
            f"{lang}_core_news_md",
            f"{lang}_core_web_md",
            f"{lang}_core_news_sm",
            f"{lang}_core_web_sm",
        ]
    
    def get_name(self) -> str:
        return "SpaCy"
    
    def supports_gpu(self) -> bool:
        return True
    
    def get_model_name(self, language: str, use_gpu: bool) -> str:
        """Retourne le modèle SpaCy préféré pour un code ISO donné."""
        candidates = self._model_candidates(language, use_gpu)
        return candidates[0]

    def resolve_model_name(self, language: str, use_gpu: bool) -> str:
        for candidate in self._model_candidates(language, use_gpu):
            try:
                spacy.load(candidate)
                return candidate
            except (OSError, ImportError):
                continue
        return self.get_model_name(language, use_gpu)
    
    def check_model_available(self, language: str, use_gpu: bool) -> bool:
        """Vérifie si le modèle SpaCy est installé et ses dépendances disponibles."""
        for model_name in self._model_candidates(language, use_gpu):
            try:
                nlp = spacy.load(model_name)
                # Pour les modèles Transformers, vérifier que curated_transformers est disponible
                if use_gpu and model_name.endswith('_trf'):
                    if 'curated_transformer' not in nlp.pipe_names:
                        try:
                            import spacy_curated_transformers
                        except ImportError:
                            return False
                return True
            except (OSError, ImportError):
                continue
        return False
    
    def download_model(self, language: str, use_gpu: bool, log_callback=None):
        """Télécharge le modèle SpaCy et ses dépendances."""
        def _log(msg):
            if log_callback:
                log_callback(msg)
        
        model_name = self.get_model_name(language, use_gpu)
        model_type = "Transformers" if use_gpu else "CPU"
        
        # Pour les modèles Transformers, vérifier que curated-transformers est installé
        if use_gpu and model_name.endswith('_trf'):
            try:
                import spacy_curated_transformers
            except ImportError:
                _log(f"Installation de spacy-curated-transformers (requis pour modèles GPU)...")
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "spacy-curated-transformers>=0.2.0"],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    _log(f"✓ spacy-curated-transformers installé.")
                except subprocess.CalledProcessError as e:
                    _log(f"Erreur lors de l'installation de spacy-curated-transformers: {e.stderr}")
                    raise
        
        _log(f"Téléchargement du modèle SpaCy {model_type} '{model_name}'...")
        _log(f"   (Cela peut prendre quelques minutes...)")
        
        try:
            subprocess.run(
                [sys.executable, "-m", "spacy", "download", model_name],
                check=True,
                capture_output=True,
                text=True
            )
            _log(f"Modèle SpaCy '{model_name}' téléchargé avec succès.")
        except subprocess.CalledProcessError as e:
            candidate_list = ", ".join(self._model_candidates(language, use_gpu))
            _log(f"Erreur lors du téléchargement: {e.stderr}")
            raise RuntimeError(
                f"Aucun modèle SpaCy téléchargeable n'a été trouvé pour la langue '{language}'. "
                f"Candidats essayés/prévus: {candidate_list}"
            ) from e
    
    def annotate_files(
        self,
        input_files: List[Tuple[str, Path]],
        output_dir: Path,
        language: str,
        use_gpu: bool,
        log_callback=None,
        progress_callback=None,
        should_stop_callback=None
    ) -> str:
        """Annote les fichiers avec SpaCy."""
        def _log(msg):
            if log_callback:
                log_callback(msg)
        
        model_name = self.resolve_model_name(language, use_gpu)
        model_type = "Transformers" if use_gpu and model_name.endswith("_trf") else "Pipeline"
        
        # Charger le modèle SpaCy
        _log(f"Initialisation du pipeline SpaCy {model_type} (modèle={model_name})...")
        try:
            nlp = spacy.load(model_name)
            # Ajouter le composant CoNLL-U
            # Note : field_names doit être un dict (pas None) pour spacy-conll 4.x
            nlp.add_pipe(
                "conll_formatter",
                config={
                    "field_names": {}  # Dictionnaire vide = utilise les valeurs par défaut
                }
            )
        except Exception as e:
            _log(f"Erreur lors de l'initialisation de SpaCy: {e}")
            raise
        
        # Annoter chaque fichier
        total = len(input_files)
        for i, (texte_id, input_path) in enumerate(input_files, 1):
            if should_stop_callback and should_stop_callback():
                _log("Annotation interrompue à la demande de l'utilisateur.")
                return model_name
            output_path = output_dir / f"{texte_id}.conllu"
            
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                doc = nlp(text)
                
                # Extraire le format CoNLL-U
                conllu_text = doc._.conll_str
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(conllu_text)
                
                _log(f"\t [{i}/{total}] {texte_id} annoté et sauvegardé: {output_path}")
                
                if progress_callback:
                    progress_callback(texte_id, i, total)
                    
            except Exception as e:
                _log(f"\t [ERREUR] {texte_id}: {e}")
                raise
        return model_name
    
    def get_display_name(self) -> str:
        return "SpaCy"
    
    def get_tooltip(self) -> str:
        return "SpaCy - Saisissez un code ISO langue; le projet tente un modèle SpaCy compatible"
