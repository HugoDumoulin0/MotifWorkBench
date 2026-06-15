"""
Page d'analyse de l'application.
Lance la procédure de recherche et de calcul des motifs séquentiels fréquents tout en montrant
la progression en direct de cette dernière.
@jcharlesDS (2026)
"""

import json
from time import perf_counter
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
from gui.core.worker import AnalysisWorker
from gui.core.run_history import append_run_history, build_run_entry
from gui.core.shiny_runner import save_results_for_shiny

class AnalysisPage(BasePage):
    """Page de lancement et suivi de l'analyse."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = Path(__file__).resolve().parents[2]
        self._worker = None
        self._run_started_at = None
        self._config_page = None  # Référence à ConfigPage (sera définie par main_window)
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
        self._config_label.setFont(QFont("Segoe UI", 10))
        self._config_label.setWordWrap(True)
        config_layout.addWidget(self._config_label)
        layout.addWidget(config_group)
        
        # Bouton de lancement
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self._launch_btn = QPushButton("Lancer l'analyse")
        self._launch_btn.setMinimumHeight(44)
        self._launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._launch_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
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
        self._stop_btn.setFont(QFont("Segoe UI", 11))
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
        self._progress_label.setFont(QFont("Segoe UI", 10))
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
                font-size: 11px;
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
        self._export_logs_btn.setFont(QFont("Segoe UI", 9))
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
        
    def update_config(self, config: dict):
        """
        Met à jour la configuration affichée (appelé depuis ConfigPage).
        """
        self._current_config = config
        
        profile_name = config.get("_display_profile_name", "Configuration appliquée")
        self._config_label.setText(self._build_config_summary(config, profile_name))

    def _format_annotator_display(self, annotator_tool: str) -> str:
        return {
            'spacy': 'spaCy',
            'stanza': 'Stanza',
        }.get(annotator_tool, annotator_tool)

    def _get_spacy_model_display(self, language: str, use_gpu: bool) -> str:
        language = (language or "").strip()
        if not language:
            return "N/A"

        spacy_gpu = {
            "fr": "fr_dep_news_trf",
            "en": "en_core_web_trf",
        }
        spacy_cpu = {
            "fr": "fr_core_news_lg",
            "en": "en_core_web_lg",
        }
        presets = spacy_gpu if use_gpu else spacy_cpu
        if language in presets:
            return presets[language]
        if "_" in language:
            return language
        if use_gpu:
            return f"{language}_dep_news_trf (essai auto)"
        return f"{language}_core_news_lg (essai auto)"

    def _get_annotator_model_display(self, config: dict) -> str:
        resolved_model = config.get("_resolved_annotator_model", "").strip()
        if resolved_model:
            return resolved_model

        annotator_tool = config.get("annotator_tool", "spacy")
        language = config.get("language", "")
        use_gpu = config.get("use_gpu", False)

        if annotator_tool == "spacy":
            return self._get_spacy_model_display(language, use_gpu)
        if annotator_tool == "stanza":
            device = "GPU" if use_gpu else "CPU"
            return f"Pipeline Stanza ({language}, {device})"
        return "N/A"

    def _build_config_summary(self, config: dict, profile_name: str) -> str:
        """Construit le résumé affiché dans le bloc Configuration actuelle."""
        annotator_tool = config.get('annotator_tool', 'spacy')
        annotator_display = self._format_annotator_display(annotator_tool)
        model_display = self._get_annotator_model_display(config)

        summary = f"<b>Profil :</b> {profile_name}<br>"
        summary += f"<b>Langue :</b> {config.get('language', 'N/A')}<br>"
        summary += f"<b>Outil d'annotation :</b> {annotator_display}<br>"
        summary += f"<b>Modèle NLP :</b> {model_display}<br>"
        summary += f"<b>GPU :</b> {'Oui' if config.get('use_gpu', False) else 'Non'}<br>"
        summary += f"<b>Threads :</b> {config.get('threads', 'N/A')}<br>"
        summary += f"<b>Minsup (%):</b> {config.get('list_minsup_percent', [])}<br>"
        summary += f"<b>Itemset min :</b> {config.get('list_itemset_min', [])}<br>"
        summary += f"<b>Gap min/max :</b> {config.get('list_gap_min', [])} / {config.get('list_gap_max', [])}<br>"
        summary += f"<b>Early selection :</b> {'Oui' if config.get('earlySelection', False) else 'Non'}<br>"
        summary += f"<b>Clustering interne :</b> {'Oui' if config.get('internal_clustering', False) else 'Non'}<br>"
        summary += f"<b>Métadonnées :</b> {config.get('list_metadata', 'N/A')}"
        return summary
        
    # --- Lancement ---
    def _on_launch(self):
        """Lance l'analyse."""
        if self._config_page:
            if self._config_page.has_unapplied_changes():
                changes = self._config_page.get_unapplied_changes_summary()
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Modifications non appliquées")
                msg.setText("Des paramètres ont été modifiés sans être appliqués.")
                details = "\n".join(f"• {line}" for line in changes) if changes else ""
                msg.setInformativeText(
                    "Paramètres modifiés :\n"
                    f"{details}\n\n"
                    "Que souhaitez-vous faire avant de lancer l'analyse ?"
                )
                apply_btn = msg.addButton("Appliquer et lancer", QMessageBox.ButtonRole.AcceptRole)
                launch_btn = msg.addButton("Lancer sans appliquer", QMessageBox.ButtonRole.ActionRole)
                cancel_btn = msg.addButton("Annuler", QMessageBox.ButtonRole.RejectRole)
                msg.setDefaultButton(apply_btn)
                msg.exec()

                clicked = msg.clickedButton()
                if clicked == cancel_btn:
                    return
                if clicked == apply_btn:
                    self._config_page._on_apply(silent=True)
                    config = self._config_page.get_config()
                else:
                    config = self._config_page.get_config()
            else:
                config = self._config_page.get_config()
        else:
            config = self._current_config

        self._current_config = config
        
        self._launch_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._progress_bar.setValue(0)
        self._progress_label.setText("Démarrage...")
        self._logs_text.clear()

        self._run_started_at = perf_counter()
        self._worker = AnalysisWorker(config)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._on_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.stopped.connect(self._on_stopped)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_stop(self):
        """Arrête l'analyse."""
        if self._worker:
            self._logs_text.append("[INFO] Demande d'arrêt envoyée. L'analyse va s'interrompre proprement...")
            self._worker.stop()
            self._stop_btn.setEnabled(False)
            self._progress_label.setText("Arrêt demandé...")
    
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
        self._logs_text.append(message)
        # Scroll vers la fin
        scrollbar = self._logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_finished(self, results: dict):
        """L'analyse est terminée."""
        worker = self._worker
        self._launch_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        if self._current_config:
            self.update_config(self._current_config)
        self._progress_label.setText("Analyse terminée avec succès")
        self._logs_text.append("\n[ANALYSE TERMINÉE]")
        
        try:
            json_path = save_results_for_shiny(results)
            self._logs_text.append(f"[SHINY] JSON prêt: {json_path}")
        except Exception as exc:
            self._logs_text.append(f"[SHINY] Erreur JSON Shiny: {exc}")
        
        # Sauvegarder les chemins de la dernière analyse pour la page Résultats
        if worker and hasattr(worker, 'paths') and worker.paths:
            last_analysis_info = {
                "analysis_group_name": worker.analysis_group_name,
                "corpus_name": worker.analysis_group_name,
                "config_id": worker.config_id,
                "path_corpus": worker.config.get("path_corpus", ""),
                "patterns_results": str(worker.paths["patterns_results"]),
                "clustering_results": str(worker.paths["clustering_results"]),
                "cwb_registry": str(worker.paths["cwb_corpus"]) + "/registry",
                "logs": "./logs",
                "path_metadata": str(worker.paths["path_metadata"])
            }
            last_analysis_file = self._project_root / "logs" / "last_analysis.json"
            last_analysis_file.parent.mkdir(parents=True, exist_ok=True)
            with open(last_analysis_file, 'w', encoding='utf-8') as f:
                json.dump(last_analysis_info, f, indent=2, ensure_ascii=False)

        self._worker = None

        duration = 0.0
        if self._run_started_at is not None:
            duration = perf_counter() - self._run_started_at
        
        append_run_history(
            build_run_entry(
                status="success",
                duration_seconds=duration,
                config=self._current_config,
                details="Analyse terminée avec succès."
            )
        )

    def _on_error(self, error_msg: str):
        """Une erreur s'est produite."""
        self._launch_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._worker = None
        if self._current_config:
            self.update_config(self._current_config)
        self._progress_label.setText("Erreur lors de l'analyse")
        self._logs_text.append(f"\n[ERREUR]\n{error_msg}")

        duration = 0.0
        if self._run_started_at is not None:
            duration = perf_counter() - self._run_started_at

        append_run_history(
            build_run_entry(
                status="error",
                duration_seconds=duration,
                config=self._current_config,
                details=error_msg[:400]  # limiter la taille des détails pour éviter les entrées trop volumineuses
            )
        )

    def _on_stopped(self, message: str):
        """L'analyse a été arrêtée proprement par l'utilisateur."""
        self._launch_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._worker = None
        if self._current_config:
            self.update_config(self._current_config)
        self._progress_label.setText("Analyse arrêtée")
        self._logs_text.append(f"\n[ANALYSE ARRÊTÉE]\n{message}")

        duration = 0.0
        if self._run_started_at is not None:
            duration = perf_counter() - self._run_started_at

        append_run_history(
            build_run_entry(
                status="stopped",
                duration_seconds=duration,
                config=self._current_config,
                details=message
            )
        )
