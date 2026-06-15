"""
Annotateur Stanza (Stanford NLP).
@jcharlesDS (2026)
"""

import io
from contextlib import redirect_stderr, redirect_stdout

import stanza
from stanza.pipeline.core import DownloadMethod
from stanza.utils.conll import CoNLL
from stanza.resources.common import DEFAULT_MODEL_DIR
from pathlib import Path
from typing import List, Tuple

from .base import BaseAnnotator


class StanzaAnnotator(BaseAnnotator):
    """Annotateur utilisant Stanza (Stanford NLP)."""

    @staticmethod
    def _forward_captured_text(text: str, log_callback=None) -> None:
        if not text or not log_callback:
            return
        for line in text.splitlines():
            line = line.strip()
            if line:
                log_callback(line)
    
    def get_name(self) -> str:
        return "Stanza"
    
    def supports_gpu(self) -> bool:
        return True
    
    def get_model_name(self, language: str, use_gpu: bool) -> str:
        """Stanza utilise le même modèle pour CPU et GPU."""
        return language
    
    def check_model_available(self, language: str, use_gpu: bool) -> bool:
        """Vérifie si le modèle Stanza est installé."""
        model_dir = Path(DEFAULT_MODEL_DIR) / language
        return model_dir.exists() and len(list(model_dir.glob("*"))) > 0
    
    def download_model(self, language: str, use_gpu: bool, log_callback=None):
        """Télécharge le modèle Stanza."""
        def _log(msg):
            if log_callback:
                log_callback(msg)
        
        _log(f"Téléchargement du modèle Stanza '{language}'...")
        try:
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                stanza.download(language)
            self._forward_captured_text(stdout_buffer.getvalue(), log_callback)
            self._forward_captured_text(stderr_buffer.getvalue(), log_callback)
            _log(f"Modèle Stanza '{language}' téléchargé avec succès.")
        except Exception as e:
            _log(f"Erreur lors du téléchargement du modèle Stanza: {e}")
            raise
    
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
        """Annote les fichiers avec Stanza."""
        def _log(msg):
            if log_callback:
                log_callback(msg)
        
        # Créer le pipeline Stanza
        _log(f"Initialisation du pipeline Stanza (langue={language}, GPU={use_gpu})...")
        try:
            nlp = stanza.Pipeline(
                language,
                download_method=DownloadMethod.REUSE_RESOURCES,
                use_gpu=use_gpu
            )
        except Exception as e:
            _log(f"Erreur lors de l'initialisation de Stanza: {e}")
            raise
        
        # Annoter chaque fichier
        total = len(input_files)
        for i, (texte_id, input_path) in enumerate(input_files, 1):
            if should_stop_callback and should_stop_callback():
                _log("Annotation interrompue à la demande de l'utilisateur.")
                return language
            output_path = output_dir / f"{texte_id}.conllu"
            
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                doc = nlp(text)
                CoNLL.write_doc2conll(doc, str(output_path))
                
                _log(f"\t [{i}/{total}] {texte_id} annoté et sauvegardé: {output_path}")
                
                if progress_callback:
                    progress_callback(texte_id, i, total)
                    
            except Exception as e:
                _log(f"\t [ERREUR] {texte_id}: {e}")
                raise
        return language
    
    def get_display_name(self) -> str:
        return "Stanza"
    
    def get_tooltip(self) -> str:
        return "Stanford NLP - Haute précision, support GPU (PyTorch)"
