"""
Annotateur basé sur Stanza (précision maximale).

@jcharlesDS (2026)
"""

import inspect
import os
from typing import List
from .base import BaseAnnotator


class StanzaAnnotator(BaseAnnotator):
    """Annotateur utilisant Stanza (Stanford NLP)."""
    
    def __init__(self):
        super().__init__()
        self._stanza = None
        self._DownloadMethod = None
        self._CoNLL = None
        self._pipelines = {}
        self._force_cpu_after_oom = False
    
    def get_name(self) -> str:
        return "Stanza"
    
    def supports_gpu(self) -> bool:
        """Stanza supporte l'accélération GPU."""
        return True
    
    def check_installation(self) -> bool:
        """Vérifie si Stanza est installé."""
        try:
            import stanza
            from stanza.pipeline.core import DownloadMethod
            from stanza.utils.conll import CoNLL
            self._stanza = stanza
            self._DownloadMethod = DownloadMethod
            self._CoNLL = CoNLL
            return True
        except ImportError:
            return False
    
    def get_installation_instructions(self) -> str:
        return (
            "Stanza n'est pas installé.\n\n"
            "Pour l'installer, exécutez:\n"
            "  pip install stanza\n\n"
            "Ou réinstallez le programme complet avec l'installer."
        )

    def _build_pipeline(self, language: str, use_gpu: bool):
        """Construit un pipeline Stanza avec une configuration prudente."""
        pipeline_kwargs = {
            "lang": language,
            "use_gpu": use_gpu,
        }

        pipeline_sig = inspect.signature(self._stanza.Pipeline)
        if "download_method" in pipeline_sig.parameters:
            pipeline_kwargs["download_method"] = self._DownloadMethod.REUSE_RESOURCES
        if "depparse_min_length_to_batch_separately" in pipeline_sig.parameters:
            pipeline_kwargs["depparse_min_length_to_batch_separately"] = 150
        if "depparse_batch_size" in pipeline_sig.parameters:
            pipeline_kwargs["depparse_batch_size"] = 400

        return self._stanza.Pipeline(**pipeline_kwargs)

    def _get_pipeline(self, language: str, use_gpu: bool):
        """Retourne un pipeline mis en cache pour la langue et le device demandés."""
        effective_use_gpu = use_gpu and not self._force_cpu_after_oom
        key = (language, effective_use_gpu)
        if key not in self._pipelines:
            self._pipelines[key] = self._build_pipeline(language, effective_use_gpu)
        return self._pipelines[key], effective_use_gpu

    def _is_cuda_oom(self, error: Exception) -> bool:
        """Détecte une erreur mémoire CUDA/PyTorch."""
        message = str(error).lower()
        return "cuda out of memory" in message or "out of memory" in message

    def _clear_torch_cuda_cache(self):
        """Libère le cache CUDA PyTorch si disponible."""
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
    
    def check_models(self, language: str, **kwargs) -> bool:
        """
        Vérifie et télécharge les modèles Stanza si nécessaires.
        """
        if not self.check_installation():
            return False
        
        try:
            download_sig = inspect.signature(self._stanza.download)
            if "download_method" in download_sig.parameters:
                # Anciennes versions / certaines versions intermédiaires
                self._stanza.download(
                    language,
                    download_method=self._DownloadMethod.REUSE_RESOURCES
                )
            else:
                # API plus récente: download() ne prend plus download_method
                self._stanza.download(language)
            return True
        except Exception as e:
            print(f"⚠ Erreur lors de la vérification des modèles Stanza : {e}")
            return False
    
    def annotate_file(self, input_path: str, output_path: str, language: str, use_gpu: bool = False):
        """Annote un fichier avec Stanza."""
        if not self.check_installation():
            raise RuntimeError(self.get_installation_instructions())

        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

        # Lire le texte
        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()

        try:
            nlp, effective_use_gpu = self._get_pipeline(language, use_gpu=use_gpu)
            doc = nlp(text)
        except Exception as e:
            if use_gpu and self._is_cuda_oom(e):
                print("⚠ Mémoire GPU insuffisante avec Stanza, nouvelle tentative en CPU...")
                self._clear_torch_cuda_cache()
                self._force_cpu_after_oom = True
                # Éviter de réutiliser un pipeline GPU déjà instable pour la suite.
                self._pipelines.pop((language, True), None)
                nlp, _ = self._get_pipeline(language, use_gpu=False)
                doc = nlp(text)
                if effective_use_gpu:
                    print("⚠ Les fichiers suivants seront annotés en CPU pour éviter de nouveaux OOM GPU.")
            else:
                raise
        
        # Écrire en CoNLL-U
        self._CoNLL.write_doc2conll(doc, output_path)
    
    def get_available_languages(self) -> List[str]:
        """Langues supportées (restreint à FR/EN pour garantir la qualité)."""
        return ["fr", "en"]
