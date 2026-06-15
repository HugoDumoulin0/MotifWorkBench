"""
Page d'analyse de l'application.
Lance la procédure de recherche et de calcul des motifs séquentiels fréquents tout en montrant
la progression en direct de cette dernière.
@jcharlesDS (2026)
"""

import json
import time
import html
import re
import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QProgressBar, QTextEdit, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from gui.widgets.base_page import BasePage, TEXT_PRIMARY
from gui.config.settings import load_profile, list_profiles, DEFAULT_CONFIG
from gui.core.gpu_detect import detect_gpu
from gui.core.worker import AnalysisWorker
from gui.core.run_history import append_run_history, build_run_entry
from gui.core.shiny_runner import save_results_for_shiny

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from annotators import get_annotator

class AnalysisPage(BasePage):
    """Page de lancement et suivi de l'analyse."""

    LOG_LEVEL_LABELS = {
        0: "MIN",
        1: "INFO",
        2: "DETAIL",
        3: "DEBUG",
    }

    LOG_LEVEL_STYLES = {
        0: ("#7c2d12", "#ffedd5"),
        1: ("#1f2937", "#e5e7eb"),
        2: ("#1d4ed8", "#dbeafe"),
        3: ("#6b7280", "#f3f4f6"),
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = Path(__file__).resolve().parents[2]
        self._gpu_available, self._gpu_description = detect_gpu()
        self._worker = None
        self._run_started_at = None
        self._config_page = None  # Référence à ConfigPage (sera définie par main_window)
        self._stop_requested = False
        self._history_recorded = False
        self._current_profile_label = "Défaut"
        self._build_ui()
        self._load_config()
    
    def set_config_page(self, config_page):
        """Définit la référence à ConfigPage pour obtenir la config actuelle."""
        self._config_page = config_page
    
    # --- Construction ---
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)
        
        
        # Titre
        layout.addWidget(self.make_title(
            "Lancer l'analyse",
            "Configurez les paramètres et démarrez le processus."
        ))
        
        # Configuration actuelle
        config_group = self.make_group("Configuration actuelle")
        config_layout = QVBoxLayout(config_group)
        self._config_label = QLabel("Chargement...")
        self._config_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        self._config_label.setFont(QFont("Helvetica Neue", 11))
        self._config_label.setWordWrap(True)
        config_layout.addWidget(self._config_label)
        layout.addWidget(config_group)
        
        # Bouton de lancement
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self._launch_btn = QPushButton("Lancer l'analyse")
        self._launch_btn.setMinimumHeight(44)
        self._launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._launch_btn.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        self._launch_btn.clicked.connect(self._on_launch)
        self._launch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #10b981;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
            QPushButton:pressed {{
                background-color: #047857;
            }}
            QPushButton:disabled {{
                background-color: #9ca3af;
                color: #d1d5db;
            }}
        """)
        btn_layout.addWidget(self._launch_btn, stretch=1)

        self._stop_btn = QPushButton("Arrêter")
        self._stop_btn.setMinimumHeight(44)
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.setFont(QFont("Helvetica Neue", 12))
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)
        self._stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ef4444;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: #dc2626;
            }}
            QPushButton:pressed {{
                background-color: #b91c1c;
            }}
            QPushButton:disabled {{
                background-color: #9ca3af;
                color: #d1d5db;
            }}
        """)
        btn_layout.addWidget(self._stop_btn, stretch=1)

        layout.addLayout(btn_layout)
        
        # Progression
        progress_group = self.make_group("Progression")
        progress_layout = QVBoxLayout(progress_group)

        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                background-color: #f3f4f6;
                height: 28px;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self._progress_bar)
        progress_layout.addSpacing(3)

        self._progress_label = QLabel("En attente...")
        self._progress_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        self._progress_label.setFont(QFont("Helvetica Neue", 11))
        progress_layout.addWidget(self._progress_label)

        layout.addWidget(progress_group)

        # Logs
        logs_group = self.make_group("Logs")
        logs_layout = QVBoxLayout(logs_group)

        self._logs_text = QTextEdit()
        self._logs_text.setReadOnly(True)
        self._logs_text.setMinimumHeight(300)
        self._logs_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #f9fafb;
                color: {TEXT_PRIMARY};
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Courier New';
                font-size: 12px;
            }}
            QMenu {{
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item:selected {{
                background-color: #3b82f6;
                color: #ffffff;
            }}
        """)
        logs_layout.addWidget(self._logs_text)
        
        # Bouton d'export des logs
        export_btn_layout = QHBoxLayout()
        export_btn_layout.addStretch()
        
        self._export_logs_btn = QPushButton("Exporter les logs")
        self._export_logs_btn.setMinimumHeight(34)
        self._export_logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._export_logs_btn.setFont(QFont("Helvetica Neue", 10))
        self._export_logs_btn.clicked.connect(self._export_logs)
        self._export_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
            QPushButton:pressed {
                background-color: #4338ca;
            }
        """)
        export_btn_layout.addWidget(self._export_logs_btn)
        logs_layout.addLayout(export_btn_layout)

        layout.addWidget(logs_group)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)
        
    # --- Configuration ---
    
    def _load_config(self):
        """Charge le dernier profil ou la config par défaut"""
        try:
            profiles = list_profiles()
            if profiles:
                config = load_profile(profiles[0])
                profile_name = profiles[0]
            else:
                config = DEFAULT_CONFIG
                profile_name = "Défaut"
        except Exception:
            config = DEFAULT_CONFIG
            profile_name = "Défaut"

        self._config_label.setText(self._build_config_summary(config, profile_name))
        self._current_config = config
        self._current_profile_label = profile_name
        
    def update_config(self, config: dict, profile_label: str = "Configuration appliquée"):
        """
        Met à jour la configuration affichée (appelé depuis ConfigPage).
        """
        self._current_config = config
        self._current_profile_label = profile_label
        self._config_label.setText(self._build_config_summary(config, profile_label))

    def _resolve_model_name(self, config: dict) -> str:
        actual_model_name = str(config.get("actual_model_name", "")).strip()
        if actual_model_name:
            return actual_model_name

        annotator_key = config.get("annotator", "spacy")
        language = str(config.get("language", "")).strip().lower()
        use_gpu = bool(config.get("use_gpu", False))

        try:
            annotator = get_annotator(annotator_key)
            return annotator.get_model_name(language, use_gpu)
        except Exception:
            return "indéterminé"

    def _normalize_runtime_config(self, config: dict) -> dict:
        normalized = dict(config)
        if not self._gpu_available:
            normalized["use_gpu"] = False
        return normalized

    def _build_config_summary(self, config: dict, profile_label: str) -> str:
        config = self._normalize_runtime_config(config)
        annotator_names = {
            "spacy": "SpaCy",
            "stanza": "Stanza",
        }
        input_type_labels = {
            "raw_txt": "Corpus brut (.txt)",
            "annotated_conllu": "Corpus annoté (.conllu)",
            "prepared_zip": "Archive préparée (.zip)",
        }
        annotator_display = annotator_names.get(config.get("annotator", "spacy"), config.get("annotator", "N/A"))
        model_name = self._resolve_model_name(config)
        input_type = config.get("input_type", "raw_txt")
        input_source_path = str(config.get("input_source_path", "")).strip()

        summary = f"<b>Profil :</b> {profile_label}<br>"
        summary += f"<b>Type d'entrée :</b> {input_type_labels.get(input_type, input_type)}<br>"
        if input_type != "raw_txt":
            summary += f"<b>Source importée :</b> {html.escape(input_source_path or 'Non renseignée')}<br>"
        summary += f"<b>Langue :</b> {config.get('language', 'N/A')}<br>"
        summary += f"<b>Outil d'annotation :</b> {annotator_display}<br>"
        summary += f"<b>Modèle :</b> {model_name}<br>"
        summary += f"<b>GPU :</b> {'Oui' if config.get('use_gpu', False) else 'Non'}<br>"
        summary += f"<b>Threads :</b> {config.get('threads', 'N/A')}<br>"
        summary += f"<b>Minsup (%):</b> {config.get('list_minsup_percent', [])}<br>"
        summary += f"<b>Itemset min :</b> {config.get('list_itemset_min', [])}<br>"
        summary += f"<b>Gap min/max :</b> {config.get('list_gap_min', [])} / {config.get('list_gap_max', [])}<br>"
        summary += f"<b>Early selection :</b> {'Oui' if config.get('earlySelection', False) else 'Non'}<br>"
        summary += f"<b>Clustering interne :</b> {'Oui' if config.get('internal_clustering', False) else 'Non'}<br>"
        summary += f"<b>Métadonnées :</b> {config.get('list_metadata', 'N/A')}"
        return summary

    def _format_config_value(self, value):
        if isinstance(value, bool):
            return "Oui" if value else "Non"
        if isinstance(value, list):
            return ", ".join(str(v) for v in value) if value else "(vide)"
        return str(value) if value not in (None, "") else "(vide)"

    def _build_config_diff_summary(self, applied_config: dict, current_config: dict) -> str:
        labels = [
            ("selected_corpus", "Corpus"),
            ("input_type", "Type d'entrée"),
            ("input_source_path", "Source importée"),
            ("language", "Langue"),
            ("annotator", "Outil d'annotation"),
            ("use_gpu", "GPU"),
            ("list_minsup_percent", "Minsup (%)"),
            ("list_itemset_min", "Itemset min"),
            ("list_gap_min", "Gap min"),
            ("list_gap_max", "Gap max"),
            ("Lemma", "Lemmes"),
            ("Pos", "POS"),
            ("Dep", "Dépendances"),
            ("Form", "Formes"),
            ("Feats", "Traits morphologiques"),
            ("list_metadata", "Métadonnées"),
            ("earlySelection", "Early selection"),
            ("seuil_early_selection", "Seuil early selection"),
            ("filter_specifs", "Filtrer par spécificités"),
            ("partition_cible", "Partition cible"),
            ("seuil_banalité", "Seuil de banalité"),
            ("early_pos4lemma", "POS early selection"),
            ("user_input_list", "Liste manuelle de lemmes"),
            ("liste_earlyselection_lemma", "Lemmes ciblés"),
            ("internal_clustering", "Clustering interne"),
            ("threads", "Threads"),
            ("specifs", "Spécificités"),
            ("liste_seuils_lemma", "Seuils lemmes"),
            ("downhill_pos4lemma", "POS pour lemmes"),
            ("liste_seuils_bigrams", "Seuils bigrams"),
        ]

        changes = []
        for key, label in labels:
            before = self._normalize_runtime_config(applied_config).get(key)
            after = self._normalize_runtime_config(current_config).get(key)
            if before != after:
                changes.append(
                    f"• <b>{html.escape(label)}</b> : "
                    f"{html.escape(self._format_config_value(before))} → "
                    f"{html.escape(self._format_config_value(after))}"
                )

        if not changes:
            return "Des modifications non appliquées ont été détectées, mais aucun écart lisible n'a pu être résumé."

        return "<br>".join(changes)

    def _confirm_unapplied_changes(self, applied_config: dict, current_config: dict) -> str:
        box = QMessageBox(self)
        box.setWindowTitle("Modifications non appliquées")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setText("Des modifications n'ont pas encore été appliquées.")
        box.setInformativeText(
            "Choisissez si vous voulez appliquer ces changements avant de lancer l'analyse."
        )
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setDetailedText("")
        box.setStyleSheet("QLabel{min-width:480px;}")

        summary = self._build_config_diff_summary(applied_config, current_config)
        box.setInformativeText(
            "Choisissez si vous voulez appliquer ces changements avant de lancer l'analyse.<br><br>"
            f"{summary}"
        )

        btn_apply = box.addButton("Appliquer et lancer", QMessageBox.ButtonRole.AcceptRole)
        btn_launch = box.addButton("Lancer sans appliquer", QMessageBox.ButtonRole.DestructiveRole)
        btn_cancel = box.addButton("Annuler", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(btn_apply)
        box.exec()

        clicked = box.clickedButton()
        if clicked is btn_apply:
            return "apply"
        if clicked is btn_launch:
            return "launch"
        return "cancel"
        
    # --- Lancement ---
    def _on_launch(self):
        """Lance l'analyse."""
        # Obtenir la configuration actuelle depuis ConfigPage (pour inclure les changements non appliqués)
        if self._config_page:
            current_config = self._config_page.get_current_config()
            applied_config = self._config_page.get_config()
            if self._config_page.has_unapplied_changes():
                decision = self._confirm_unapplied_changes(applied_config, current_config)
                if decision == "cancel":
                    return
                if decision == "apply":
                    config = self._config_page.apply_current_config_silently("Configuration appliquée")
                else:
                    config = current_config
            else:
                config = current_config
        else:
            config = self._current_config
        
        self._launch_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._progress_bar.setValue(0)
        self._progress_label.setText("Démarrage...")
        self._logs_text.clear()
        self._stop_requested = False
        self._history_recorded = False

        self._run_started_at = time.time()
        self._worker = AnalysisWorker(config)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._on_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.stopped.connect(self._on_stopped)
        self._worker.start()

    def _on_stop(self):
        """Arrête l'analyse."""
        if self._worker and self._worker.isRunning() and not self._stop_requested:
            self._stop_requested = True
            self._launch_btn.setEnabled(False)
            self._stop_btn.setEnabled(False)
            self._progress_label.setText("Arrêt demandé...")
            self._logs_text.append("[ARRÊT] Demande d'arrêt envoyée. Attente d'un point de sortie sûr...")
            self._worker.stop()
    
    def _export_logs(self):
        """Exporte les logs dans un fichier .txt"""
        try:
            # Récupérer le contenu des logs
            logs_content = self._logs_text.toPlainText()
            
            if not logs_content.strip():
                QMessageBox.information(
                    self,
                    "Logs vides",
                    "Il n'y a pas de logs à exporter."
                )
                return
            
            # Créer le dossier logs s'il n'existe pas
            from pathlib import Path
            logs_dir = Path(__file__).resolve().parents[2] / "Data" / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Nom de fichier par défaut avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_path = logs_dir / f"logs_analyse_{timestamp}.txt"
            
            # Ouvrir le dialogue de sauvegarde
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exporter les logs",
                str(default_path),
                "Fichiers texte (*.txt);;Tous les fichiers (*)"
            )
            
            if file_path:
                # Sauvegarder les logs
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(logs_content)
                
                QMessageBox.information(
                    self,
                    "Export réussi",
                    f"Les logs ont été exportés avec succès vers :\n{file_path}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur d'export",
                f"Une erreur s'est produite lors de l'export des logs :\n{str(e)}"
            )

    def _on_progress(self, message: str, percent: int):
        """Met à jour la progression."""
        self._progress_bar.setValue(percent)
        self._progress_label.setText(f"{message} ({percent}%)")

    def _on_log(self, message: str):
        """Ajoute un message de log."""
        self._logs_text.append(self._format_log_html(message))
        # Scroll vers la fin
        scrollbar = self._logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _format_log_html(self, message: str) -> str:
        match = re.match(r"^\[\[LEVEL:(\d+)]]\s?(.*)$", message, re.DOTALL)
        if not match:
            return html.escape(message)

        level = int(match.group(1))
        content = match.group(2)
        label = self.LOG_LEVEL_LABELS.get(level, "LOG")
        fg_color, bg_color = self.LOG_LEVEL_STYLES.get(level, ("#1f2937", "#e5e7eb"))

        return (
            f"<span style='display:inline-block; min-width:52px; "
            f"padding:2px 6px; border-radius:4px; "
            f"background:{bg_color}; color:{fg_color}; font-weight:bold;'>"
            f"{html.escape(label)}</span>"
            f"&nbsp;&nbsp;<span style='color:#111827;'>{html.escape(content)}</span>"
        )

    def _on_finished(self, results: dict):
        """L'analyse est terminée."""
        if self._stop_requested:
            return
        self._launch_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._progress_label.setText("Analyse terminée avec succès")
        self._logs_text.append("\n[ANALYSE TERMINÉE]")
        
        try:
            json_path = save_results_for_shiny(results)
            self._logs_text.append(f"[SHINY] JSON prêt: {json_path}")
        except Exception as exc:
            self._logs_text.append(f"[SHINY] Erreur JSON Shiny: {exc}")
        
        # Sauvegarder les chemins de la dernière analyse pour la page Résultats
        if hasattr(self._worker, 'paths') and self._worker.paths:
            last_analysis_info = {
                "analysis_group_name": self._worker.analysis_group_name,
                "config_id": self._worker.config_id,
                "patterns_results": str(self._worker.paths["patterns_results"]),
                "clustering_results": str(self._worker.paths["clustering_results"]),
                "logs": str(self._worker.paths["logs"])
            }
            last_analysis_file = self._project_root / "logs" / "last_analysis.json"
            last_analysis_file.parent.mkdir(parents=True, exist_ok=True)
            with open(last_analysis_file, 'w', encoding='utf-8') as f:
                json.dump(last_analysis_info, f, indent=2, ensure_ascii=False)

        if self._worker is not None:
            self._current_config = dict(self._worker.config)
            self._config_label.setText(self._build_config_summary(self._current_config, self._current_profile_label))

        duration = 0.0
        if self._run_started_at is not None:
            duration = time.time() - self._run_started_at
        
        self._record_history_once("success", duration, "Analyse terminée avec succès.")
        self._worker = None

    def _on_error(self, error_msg: str):
        """Une erreur s'est produite."""
        if self._stop_requested and "arrêtée par l'utilisateur" in error_msg.lower():
            self._on_stopped(error_msg)
            return
        self._launch_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._progress_label.setText("Erreur lors de l'analyse")
        self._logs_text.append(f"\n[ERREUR]\n{error_msg}")

        duration = 0.0
        if self._run_started_at is not None:
            duration = time.time() - self._run_started_at

        self._record_history_once("error", duration, error_msg[:400])
        self._worker = None

    def _on_stopped(self, message: str):
        """L'analyse a été arrêtée proprement."""
        self._launch_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._progress_label.setText("Analyse arrêtée")
        self._logs_text.append(f"\n[ARRÊT]\n{message}")

        duration = 0.0
        if self._run_started_at is not None:
            duration = time.time() - self._run_started_at

        self._record_history_once("stopped", duration, "Analyse arrêtée par l'utilisateur.")
        self._worker = None

    def _record_history_once(self, status: str, duration_seconds: float, details: str):
        """Écrit l'historique une seule fois, même si plusieurs signaux arrivent."""
        if self._history_recorded:
            return
        append_run_history(
            build_run_entry(
                status=status,
                duration_seconds=duration_seconds,
                config=self._current_config,
                details=details
            )
        )
        self._history_recorded = True
