"""
Worker thread pour exécuter l'analyse en arrière-plan.
Envoie des signaux pour mettre à jour l'UI.
"""

from PyQt6.QtCore import QThread, pyqtSignal
import os
import sys

# Ajoute le dossier src au path pour importer les modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import run_analysis, AnalysisCancelled
from gui.core.analysis_paths import (
    generate_config_id, 
    create_analysis_structure,
    find_existing_analysis,
    get_analysis_root,
    resolve_analysis_subdir,
)

class AnalysisWorker(QThread):
    """
    Worker thread qui exécute l'analyse sans bloquer l'interface utilisateur.
    
    Signaux:
        progress : (str, int) -> émis à chaque étape, contient le nom et le pourcentage d'avancement.
        log : (str) -> émis pour chaque log
        finished : () -> émis lorsque l'analyse est terminée
        error : (str) -> émis en cas d'erreur
    """
    
    # Signaux
    progress = pyqtSignal(str, int) # (étape, pourcentage)
    log = pyqtSignal(str) # (message)
    finished = pyqtSignal(dict) # (résultats)
    error = pyqtSignal(str) # (message d'erreur)
    stopped = pyqtSignal(str) # (message d'arrêt)
    
    def __init__(self, config):
        """
        config: dict contenant les paramètres de l'analyse 
        """
        super().__init__()
        self.config = config
        # Ajouter le mode GUI pour éviter le lancement automatique de Shiny
        self.config["mode"] = "gui"
        self._stop_requested = False
        
        # Extraire le nom du groupe d'analyses de la config
        self.analysis_group_name = config.get(
            "analysis_group_name",
            config.get("corpus_name", "analyse_sans_nom")
        )
        # Alias temporaire pour compatibilité locale
        self.corpus_name = self.analysis_group_name
        
        # Chercher si une analyse avec cette configuration existe déjà
        existing_config_id = find_existing_analysis(self.analysis_group_name, config)
        
        if existing_config_id:
            # Réutiliser l'analyse existante
            self.config_id = existing_config_id
            self.reusing_existing = True
            # Reconstruire le dictionnaire paths à partir du dossier existant
            root = get_analysis_root(self.analysis_group_name, self.config_id)
            # Calculer path_metadata depuis config["path_corpus"]
            from pathlib import Path
            path_corpus = config.get("path_corpus", "")
            if not path_corpus:
                raise ValueError("path_corpus manquant dans la configuration. Veuillez sélectionner un corpus.")
            path_metadata = Path(path_corpus) / "metadata.tsv"
            self.paths = {
                "root": root,
                "tagged_stanza": resolve_analysis_subdir(root, "textes_tagged", "Textes_tagged_stanza"),
                "tagged_for_dmt4": resolve_analysis_subdir(root, "textes_tagged_for_dmt4", "Textes_tagged_stanza_for_dmt4"),
                "textes_vrt": root / "textesVRT",
                "cwb_corpus": root / "cwb-corpus",
                "dmt4_files": root / "DMT4_files",
                "lexiques": root / "Lexiques",
                "clustering_results": root / "Clustering_results",
                "patterns_results": root / "Patterns_results",
                # Note: les logs sont écrits dans ./logs/ à la racine du projet
                "underscore_fix": root / "underscore_fix",
                "prepared_import": root / "_import_prepared",
                "shared_cache_root": root.parent / "_cache",
                "path_metadata": path_metadata
            }
            if config.get("earlySelection"):
                self.paths["early_selection"] = root / "earlySelection"
        else:
            # Créer une nouvelle analyse
            self.config_id = generate_config_id(config)
            self.reusing_existing = False
            # Créer la structure de dossiers pour cette analyse
            self.paths = create_analysis_structure(self.analysis_group_name, self.config_id, config)

    def run(self):
        """
        Exécute l'analyse. Appelé automatiquement par QThread.start().
        """
        try:
            # Informer l'utilisateur du mode utilisé
            if self.reusing_existing:
                self._on_log(f"Réutilisation de l'analyse : {self.analysis_group_name}/{self.config_id}")
                self._on_log("   Les fichiers existants seront conservés ou mis à jour si nécessaire.")
            else:
                self._on_log(f"Nouvelle analyse : {self.analysis_group_name}/{self.config_id}")
            
            self._on_log(f"Dossier de sortie : {self.paths['root']}/")
            self._on_log("-" * 75)
            
            # Appelle la fonction d'analyse principale
            results = run_analysis(
                self.config,
                progress_callback=self._on_progress,
                log_callback=self._on_log,
                paths=self.paths,
                cancel_callback=self.is_stop_requested,
            )
            
            # Envoie les résultats finaux
            if self._stop_requested:
                self.stopped.emit("Analyse arrêtée par l'utilisateur.")
            else:
                self.finished.emit(results)
            
        except AnalysisCancelled as e:
            self.stopped.emit(str(e))
            
        except Exception as e:
            # Capture toute erreur et l'envoie à l'UI
            error_msg = f"Erreur lors de l'analyse : {str(e)}"
            self.error.emit(error_msg)

    def _on_progress(self, etape, pourcentage):
        """
        Callback appelé par run_analysis à chaque étape.
        """
        self.progress.emit(etape, pourcentage)

    def _on_log(self, message):
        """
        Callback appelé par run_analysis pour chaque message de log.
        """
        self.log.emit(message)

    def is_stop_requested(self) -> bool:
        """Indique si un arrêt propre a été demandé."""
        return self._stop_requested

    def stop(self):
        """
        Demande l'arrêt du worker sans bloquer l'interface.
        """
        self._stop_requested = True
