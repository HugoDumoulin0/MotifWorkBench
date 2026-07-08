"""
Page Paramètres de l'application.
Gestion des préférences globales de MotifWorkBench.
@jcharlesDS (2026)
"""

import json
import os
import sys
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QComboBox, QSpinBox, QCheckBox,
    QMessageBox, QListWidget, QAbstractItemView, QDialog
)
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import Qt, QUrl, QTimer

from gui.widgets.base_page import BasePage, TEXT_PRIMARY, ACCENT, TEXT_SECONDARY
from gui.core.analysis_paths import (
    get_default_analyses_root,
    list_analysis_group_names,
    list_configs_for_analysis_group,
    delete_analysis_configs,
)


class AnalysisCleanupDialog(QDialog):
    """Fenêtre dédiée à la suppression des configurations d'analyses."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des analyses")
        self.setMinimumSize(760, 460)
        self._build_ui()
        self._refresh_analysis_management()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Gestion des analyses")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827;")
        layout.addWidget(title)

        desc = QLabel("Sélectionnez un groupe d'analyses puis une ou plusieurs configurations à supprimer.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(desc)

        group_row = QHBoxLayout()
        group_label = QLabel("Groupe d'analyses :")
        group_label.setFixedWidth(140)
        group_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        group_row.addWidget(group_label)

        self._analysis_group_combo = QComboBox()
        self._analysis_group_combo.currentTextChanged.connect(self._refresh_analysis_configs_list)
        group_row.addWidget(self._analysis_group_combo, stretch=1)

        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setMinimumHeight(38)
        btn_refresh.setFixedWidth(110)
        btn_refresh.setFont(QFont("Segoe UI", 10))
        btn_refresh.clicked.connect(self._refresh_analysis_management)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: #2c2c3c;
                color: #ffffff;
                border: 1px solid #3c3c4c;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #3c3c4c;
                border-color: {ACCENT};
            }}
        """)
        group_row.addWidget(btn_refresh)
        layout.addLayout(group_row)

        self._analysis_configs_list = QListWidget()
        self._analysis_configs_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._analysis_configs_list.setMinimumHeight(260)
        self._analysis_configs_list.setStyleSheet(f"""
            QListWidget {{
                background: #ffffff;
                color: {TEXT_PRIMARY};
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 6px;
            }}
            QListWidget::item {{
                padding: 6px 4px;
            }}
            QListWidget::item:selected {{
                background: #e9eefc;
                color: {TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self._analysis_configs_list)

        self._analysis_configs_hint = QLabel("")
        self._analysis_configs_hint.setWordWrap(True)
        self._analysis_configs_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 9pt;")
        layout.addWidget(self._analysis_configs_hint)

        buttons = QHBoxLayout()
        self._select_all_btn = QPushButton("Tout sélectionner")
        self._select_all_btn.setFixedHeight(36)
        self._select_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2c2c3c;
                color: #ffffff;
                border: 1px solid #3c3c4c;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #3c3c4c;
                border-color: {ACCENT};
            }}
        """)
        self._select_all_btn.clicked.connect(self._select_all_analysis_configs)
        buttons.addWidget(self._select_all_btn)

        self._delete_btn = QPushButton("Supprimer la sélection")
        self._delete_btn.setFixedHeight(36)
        self._delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        self._delete_btn.clicked.connect(self._delete_selected_analysis_configs)
        buttons.addWidget(self._delete_btn)

        buttons.addStretch()

        btn_close = QPushButton("Fermer")
        btn_close.setMinimumHeight(38)
        btn_close.setFont(QFont("Segoe UI", 10))
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #6b83d4;
            }}
        """)
        buttons.addWidget(btn_close)
        layout.addLayout(buttons)

    def _refresh_analysis_management(self):
        current_group = self._analysis_group_combo.currentText()

        self._analysis_group_combo.blockSignals(True)
        self._analysis_group_combo.clear()
        self._analysis_group_combo.addItems(list_analysis_group_names())
        self._analysis_group_combo.blockSignals(False)

        if current_group:
            idx = self._analysis_group_combo.findText(current_group)
            if idx >= 0:
                self._analysis_group_combo.setCurrentIndex(idx)

        self._refresh_analysis_configs_list(self._analysis_group_combo.currentText())

    def _refresh_analysis_configs_list(self, analysis_group_name: str):
        self._analysis_configs_list.clear()

        if not analysis_group_name:
            self._analysis_configs_hint.setText("Aucun groupe d'analyses disponible dans le dossier sélectionné.")
            self._select_all_btn.setEnabled(False)
            self._delete_btn.setEnabled(False)
            return

        configs = list_configs_for_analysis_group(analysis_group_name)
        if not configs:
            self._analysis_configs_hint.setText("Ce groupe ne contient aucune configuration.")
            self._select_all_btn.setEnabled(False)
            self._delete_btn.setEnabled(False)
            return

        for config_info in configs:
            created_at = config_info.get("created_at", "Date inconnue")
            config_id = config_info.get("config_id", "")
            self._analysis_configs_list.addItem(f"{config_id} | {created_at}")

        self._analysis_configs_hint.setText(
            f"{len(configs)} configuration(s) dans « {analysis_group_name} ». Sélection multiple possible."
        )
        self._select_all_btn.setEnabled(True)
        self._delete_btn.setEnabled(True)

    def _select_all_analysis_configs(self):
        """Sélectionne toutes les configurations affichées."""
        self._analysis_configs_list.selectAll()

    def _delete_selected_analysis_configs(self):
        analysis_group_name = self._analysis_group_combo.currentText().strip()
        selected_items = self._analysis_configs_list.selectedItems()

        if not analysis_group_name or not selected_items:
            QMessageBox.information(self, "Info", "Sélectionnez au moins une configuration à supprimer.")
            return

        config_ids = [item.text().split(" | ", 1)[0].strip() for item in selected_items]
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Supprimer les configurations sélectionnées ?\n\n" + "\n".join(config_ids),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            deleted_count = delete_analysis_configs(analysis_group_name, config_ids)
            QMessageBox.information(self, "Succès", f"{deleted_count} configuration(s) supprimée(s).")
            self._refresh_analysis_management()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de supprimer les configurations : {e}")


class CorpusCleanupDialog(QDialog):
    """Fenêtre dédiée à la gestion des corpus."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = Path(__file__).resolve().parents[2]
        self._corpus_root = self._project_root / "Data" / "Corpus"
        self.setWindowTitle("Gestion des corpus")
        self.setMinimumSize(760, 460)
        self._build_ui()
        self._refresh_corpus_list()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Gestion des corpus")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827;")
        layout.addWidget(title)

        desc = QLabel("Sélectionnez un ou plusieurs dossiers de corpus à supprimer.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(desc)

        top_row = QHBoxLayout()
        root_label = QLabel(f"Dossier : {self._corpus_root}")
        root_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        root_label.setWordWrap(True)
        top_row.addWidget(root_label, stretch=1)

        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setMinimumHeight(38)
        btn_refresh.setFixedWidth(110)
        btn_refresh.setFont(QFont("Segoe UI", 10))
        btn_refresh.clicked.connect(self._refresh_corpus_list)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: #2c2c3c;
                color: #ffffff;
                border: 1px solid #3c3c4c;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #3c3c4c;
                border-color: {ACCENT};
            }}
        """)
        top_row.addWidget(btn_refresh)
        layout.addLayout(top_row)

        self._corpus_list = QListWidget()
        self._corpus_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._corpus_list.setMinimumHeight(260)
        self._corpus_list.setStyleSheet(f"""
            QListWidget {{
                background: #ffffff;
                color: {TEXT_PRIMARY};
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 6px;
            }}
            QListWidget::item {{
                padding: 6px 4px;
            }}
            QListWidget::item:selected {{
                background: #e9eefc;
                color: {TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self._corpus_list)

        self._corpus_hint = QLabel("")
        self._corpus_hint.setWordWrap(True)
        self._corpus_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 9pt;")
        layout.addWidget(self._corpus_hint)

        buttons = QHBoxLayout()
        self._select_all_btn = QPushButton("Tout sélectionner")
        self._select_all_btn.setMinimumHeight(38)
        self._select_all_btn.setFont(QFont("Segoe UI", 10))
        self._select_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2c2c3c;
                color: #ffffff;
                border: 1px solid #3c3c4c;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #3c3c4c;
                border-color: {ACCENT};
            }}
        """)
        self._select_all_btn.clicked.connect(self._select_all_corpora)
        buttons.addWidget(self._select_all_btn)

        self._delete_btn = QPushButton("Supprimer la sélection")
        self._delete_btn.setMinimumHeight(38)
        self._delete_btn.setFont(QFont("Segoe UI", 10))
        self._delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        self._delete_btn.clicked.connect(self._delete_selected_corpora)
        buttons.addWidget(self._delete_btn)

        buttons.addStretch()

        btn_close = QPushButton("Fermer")
        btn_close.setMinimumHeight(38)
        btn_close.setFont(QFont("Segoe UI", 10))
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #6b83d4;
            }}
        """)
        buttons.addWidget(btn_close)
        layout.addLayout(buttons)

    def _refresh_corpus_list(self):
        self._corpus_list.clear()
        self._corpus_root.mkdir(parents=True, exist_ok=True)

        corpus_dirs = []
        for item in sorted(self._corpus_root.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                txt_count = len(list(item.glob("*.txt")))
                metadata_exists = (item / "metadata.tsv").exists()
                corpus_dirs.append((item.name, txt_count, metadata_exists))

        if not corpus_dirs:
            self._corpus_hint.setText("Aucun corpus disponible.")
            self._select_all_btn.setEnabled(False)
            self._delete_btn.setEnabled(False)
            return

        for name, txt_count, metadata_exists in corpus_dirs:
            metadata_label = "metadata" if metadata_exists else "sans metadata"
            self._corpus_list.addItem(f"{name} | {txt_count} texte(s) | {metadata_label}")

        self._corpus_hint.setText(
            f"{len(corpus_dirs)} corpus disponible(s). Sélection multiple possible."
        )
        self._select_all_btn.setEnabled(True)
        self._delete_btn.setEnabled(True)

    def _select_all_corpora(self):
        """Sélectionne tous les corpus affichés."""
        self._corpus_list.selectAll()

    def _delete_selected_corpora(self):
        selected_items = self._corpus_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Info", "Sélectionnez au moins un corpus à supprimer.")
            return

        corpus_names = [item.text().split(" | ", 1)[0].strip() for item in selected_items]
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Supprimer les corpus sélectionnés ?\n\n" + "\n".join(corpus_names),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            deleted_count = 0
            for corpus_name in corpus_names:
                corpus_path = self._corpus_root / corpus_name
                if corpus_path.exists() and corpus_path.is_dir():
                    shutil.rmtree(corpus_path)
                    deleted_count += 1

            QMessageBox.information(self, "Succès", f"{deleted_count} corpus supprimé(s).")
            self._refresh_corpus_list()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de supprimer les corpus : {e}")


class AppSettingsPage(BasePage):
    """Page de configuration des paramètres de l'application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = Path(__file__).resolve().parents[2]
        self._settings_file = self._project_root / "app_settings.json"
        
        self._load_settings()
        self._build_ui()
    
    def _load_settings(self):
        """Charge les paramètres depuis le fichier JSON."""
        default_settings = {
            "log_level": "Normal",
            "log_retention_days": 30,
            "models_cache_path": str(Path.home() / ".cache"),
            "auto_check_model_updates": False,
            "analyses_root_path": str(get_default_analyses_root()),
            "closed_motif_concordance_display": "matched_words",
            "prompt_prepared_archive_on_first_analysis": True,
        }
        
        if self._settings_file.exists():
            try:
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._settings = {**default_settings, **loaded}
            except Exception:
                self._settings = default_settings
        else:
            self._settings = default_settings

        analyses_root = self._settings.get("analyses_root_path", str(get_default_analyses_root()))
        self._analyses_root_path = str(Path(analyses_root).expanduser())
    
    def _save_settings(self):
        """Sauvegarde les paramètres dans le fichier JSON."""
        try:
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de sauvegarder les paramètres : {e}")
    
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
            "Paramètres de l'application",
            "Configuration globale de MotifWorkBench"
        ))
        
        # Section 1 : Chemins et accès rapides
        layout.addWidget(self._build_paths_section())
        
        # Section 2 : Modèles NLP
        layout.addWidget(self._build_models_section())
        
        # Section 3 : Logs et diagnostic
        layout.addWidget(self._build_logs_section())
        
        # Section 4 : Avancé
        layout.addWidget(self._build_advanced_section())
        
        # Spacer
        layout.addStretch()
        
        # Bouton de sauvegarde en bas
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        btn_save = QPushButton("Enregistrer les paramètres")
        btn_save.setFont(QFont("Segoe UI", 10))
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setFixedHeight(40)
        btn_save.setMinimumWidth(220)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #6b83d4;
            }}
        """)
        btn_save.clicked.connect(self._on_save_clicked)
        save_layout.addWidget(btn_save)
        
        layout.addLayout(save_layout)
        
        scroll.setWidget(content)
        outer.addWidget(scroll)
        
        # Calculer les tailles de cache après le chargement de l'UI
        QTimer.singleShot(100, self._refresh_disk_usage)

    def _detect_stanza_cache_path(self) -> Path:
        """Détecte le dossier réellement utilisé par Stanza pour ses ressources."""
        candidate_paths: list[Path] = []

        configured_cache_root = self._settings.get("models_cache_path", "").strip()
        if configured_cache_root:
            candidate_paths.append(Path(configured_cache_root).expanduser() / "stanza")

        env_path = os.environ.get("STANZA_RESOURCES_DIR", "").strip()
        if env_path:
            candidate_paths.append(Path(env_path).expanduser())

        try:
            from stanza.resources.common import DEFAULT_MODEL_DIR
            candidate_paths.append(Path(DEFAULT_MODEL_DIR).expanduser())
        except Exception:
            pass

        xdg_cache_home = os.environ.get("XDG_CACHE_HOME", "").strip()
        if xdg_cache_home:
            candidate_paths.append(Path(xdg_cache_home).expanduser() / "stanza")

        candidate_paths.extend([
            Path.home() / ".cache" / "stanza",
            Path.home() / "stanza_resources",
            Path.home() / ".stanza_resources",
        ])

        seen: set[Path] = set()
        for candidate in candidate_paths:
            resolved = candidate.expanduser()
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved.exists():
                return resolved

        return candidate_paths[0] if candidate_paths else (Path.home() / ".cache" / "stanza")

    def _get_directory_size(self, path: Path) -> int:
        """Calcule la taille totale d'un dossier."""
        if not path.exists():
            return 0
        return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

    def _format_display_path(self, path: str | Path) -> str:
        """Uniformise l'affichage des chemins dans l'interface."""
        target = Path(path).expanduser()
        if not target.is_absolute():
            target = (self._project_root / target).resolve()

        try:
            relative_to_project = target.relative_to(self._project_root)
            return f"/{relative_to_project.as_posix()}"
        except ValueError:
            pass

        try:
            relative_to_home = target.relative_to(Path.home())
            return f"~/{relative_to_home.as_posix()}"
        except ValueError:
            pass

        return target.as_posix()
    
    def _build_paths_section(self):
        """Section : Chemins et accès rapides."""
        group = self.make_group("Chemins et accès rapides")
        layout = QVBoxLayout(group)
        layout.setSpacing(16)
        
        # Corpus
        layout.addWidget(self._build_corpus_settings_block())
        
        # Analyses
        layout.addWidget(self._build_analyses_settings_block())
        
        # Logs
        layout.addWidget(self._make_folder_row(
            "Logs",
            "logs/",
            "Historique des exécutions et messages de diagnostic de l'application",
            self._open_logs_folder
        ))
        
        return group
    
    def _build_models_section(self):
        """Section : Modèles NLP."""
        group = self.make_group("Modèles NLP")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Description
        desc = QLabel("Emplacements des caches des différents outils d'annotation")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10pt;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Stanza
        stanza_layout = QHBoxLayout()
        stanza_label = QLabel("Stanza :")
        stanza_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 10pt; font-weight: bold;")
        stanza_label.setFixedWidth(80)
        stanza_layout.addWidget(stanza_label)
        
        stanza_path = self._detect_stanza_cache_path()
        self._stanza_path_label = QLabel(self._format_display_path(stanza_path))
        self._stanza_path_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 9pt; font-family: 'Courier New';")
        stanza_layout.addWidget(self._stanza_path_label, stretch=1)
        
        self._stanza_size_label = QLabel("...")
        self._stanza_size_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 9pt;")
        self._stanza_size_label.setFixedWidth(100)
        self._stanza_size_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        stanza_layout.addWidget(self._stanza_size_label)
        
        layout.addLayout(stanza_layout)
        
        # SpaCy
        spacy_layout = QHBoxLayout()
        spacy_label = QLabel("SpaCy :")
        spacy_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 10pt; font-weight: bold;")
        spacy_label.setFixedWidth(80)
        spacy_layout.addWidget(spacy_label)
        
        # Déterminer le chemin spaCy en demandant directement au module
        try:
            import spacy
            spacy_path = Path(spacy.__file__).parent.parent
        except ImportError:
            spacy_path = Path.home() / ".local" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        self._spacy_path_label = QLabel(self._format_display_path(spacy_path) + "/...")
        self._spacy_path_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 9pt; font-family: 'Courier New';")
        spacy_layout.addWidget(self._spacy_path_label, stretch=1)
        
        self._spacy_size_label = QLabel("...")
        self._spacy_size_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 9pt;")
        self._spacy_size_label.setFixedWidth(100)
        self._spacy_size_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        spacy_layout.addWidget(self._spacy_size_label)
        
        layout.addLayout(spacy_layout)
        
        # Total
        total_layout = QHBoxLayout()
        total_label = QLabel("Total :")
        total_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 10pt; font-weight: bold;")
        total_label.setFixedWidth(80)
        total_layout.addWidget(total_label)
        
        total_layout.addStretch()
        
        self._total_size_label = QLabel("...")
        self._total_size_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 10pt; font-weight: bold;")
        self._total_size_label.setFixedWidth(100)
        self._total_size_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_layout.addWidget(self._total_size_label)
        
        layout.addLayout(total_layout)
        
        # Bouton actualiser
        refresh_layout = QHBoxLayout()
        btn_refresh_disk = QPushButton("Actualiser")
        btn_refresh_disk.setFixedWidth(120)
        btn_refresh_disk.setFixedHeight(32)
        btn_refresh_disk.setStyleSheet(f"""
            QPushButton {{
                background-color: #2c2c3c;
                color: #ffffff;
                border: 1px solid #3c3c4c;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #3c3c4c;
                border-color: {ACCENT};
            }}
        """)
        btn_refresh_disk.clicked.connect(self._refresh_disk_usage)
        refresh_layout.addWidget(btn_refresh_disk)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        # Nettoyage
        clean_layout = QHBoxLayout()
        btn_clean_cache = QPushButton("Nettoyer le cache des modèles")
        btn_clean_cache.setFixedHeight(35)
        btn_clean_cache.setFixedWidth(220)
        btn_clean_cache.setStyleSheet(f"""
            QPushButton {{
                background-color: #2c2c3c;
                color: #ffffff;
                border: 1px solid #3c3c4c;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #3c3c4c;
                border-color: {ACCENT};
            }}
        """)
        btn_clean_cache.clicked.connect(self._clean_models_cache)
        clean_layout.addWidget(btn_clean_cache)
        clean_layout.addStretch()
        
        layout.addLayout(clean_layout)
        
        # Calcul initial de l'espace disque
        self._refresh_disk_usage()
        
        return group
    
    def _build_logs_section(self):
        """Section : Logs et diagnostic."""
        group = self.make_group("Logs et diagnostic")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Niveau de verbosité
        level_layout = QHBoxLayout()
        level_label = QLabel("Niveau de verbosité :")
        level_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 10pt;")
        level_label.setFixedWidth(150)
        level_layout.addWidget(level_label)
        
        self._log_level_combo = QComboBox()
        self._log_level_combo.addItems(["Minimal", "Normal", "Détaillé", "Debug"])
        self._log_level_combo.setCurrentText(self._settings.get("log_level", "Normal"))
        self._log_level_combo.setFixedWidth(150)
        level_layout.addWidget(self._log_level_combo)
        level_layout.addStretch()
        
        layout.addLayout(level_layout)
        
        # Durée de conservation
        retention_layout = QHBoxLayout()
        retention_label = QLabel("Conservation des logs :")
        retention_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 10pt;")
        retention_label.setFixedWidth(150)
        retention_layout.addWidget(retention_label)
        
        self._retention_spin = QSpinBox()
        self._retention_spin.setRange(1, 365)
        self._retention_spin.setValue(self._settings.get("log_retention_days", 30))
        self._retention_spin.setSuffix(" jours")
        self._retention_spin.setFixedWidth(150)
        retention_layout.addWidget(self._retention_spin)
        retention_layout.addStretch()
        
        layout.addLayout(retention_layout)
        
        # Bouton de nettoyage
        buttons_layout = QHBoxLayout()
        
        btn_clean_logs = QPushButton("Nettoyer les anciens logs")
        btn_clean_logs.setFixedHeight(35)
        btn_clean_logs.setFixedWidth(200)
        btn_clean_logs.setStyleSheet(f"""
            QPushButton {{
                background-color: #2c2c3c;
                color: #ffffff;
                border: 1px solid #3c3c4c;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #3c3c4c;
                border-color: {ACCENT};
            }}
        """)
        btn_clean_logs.clicked.connect(self._clean_old_logs)
        buttons_layout.addWidget(btn_clean_logs)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        return group
    
    def _build_advanced_section(self):
        """Section : Avancé."""
        group = self.make_group("Avancé")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Description
        desc = QLabel("Actions avancées et réinitialisation")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10pt;")
        layout.addWidget(desc)

        prepared_archive_row = QHBoxLayout()
        self._prepared_archive_prompt_checkbox = QCheckBox(
            "Proposer une archive préparée après la première analyse complète d'un nouveau corpus"
        )
        self._prepared_archive_prompt_checkbox.setChecked(
            self._settings.get("prompt_prepared_archive_on_first_analysis", True)
        )
        prepared_archive_row.addWidget(self._prepared_archive_prompt_checkbox)
        prepared_archive_row.addStretch()
        layout.addLayout(prepared_archive_row)

        prepared_archive_hint = QLabel(
            "L'archive ZIP contient `textes_tagged` et `underscore_fix` pour une réutilisation "
            "ou un partage plus simple."
        )
        prepared_archive_hint.setWordWrap(True)
        prepared_archive_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 9pt;")
        layout.addWidget(prepared_archive_hint)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        btn_reset = QPushButton("Réinitialiser tous les paramètres")
        btn_reset.setFixedHeight(35)
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        btn_reset.clicked.connect(self._reset_settings)
        buttons_layout.addWidget(btn_reset)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        return group

    def _build_analyses_settings_block(self):
        """Bloc compact dédié au dossier parent d'analyses."""
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: #ffffff;
                border: 1px solid #3a3a4a;
                border-radius: 6px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        title = QLabel("Analyses")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000; border: none; background: transparent;")
        layout.addWidget(title)

        desc = QLabel("Dossier contenant les résultats des analyses")
        desc.setFont(QFont("Segoe UI", 9))
        desc.setStyleSheet("color: #555555; border: none; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        path_row = QHBoxLayout()
        path_label = QLabel("Dossier parent :")
        path_label.setFixedWidth(120)
        path_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        path_row.addWidget(path_label)

        self._analyses_root_label = QLabel(self._format_display_path(self._analyses_root_path))
        self._analyses_root_label.setFont(QFont("Courier New", 9))
        self._analyses_root_label.setStyleSheet("color: #333333; border: none; background: transparent;")
        self._analyses_root_label.setWordWrap(True)
        path_row.addWidget(self._analyses_root_label, stretch=1)

        btn_open_root = QPushButton("Ouvrir")
        btn_open_root.setMinimumHeight(38)
        btn_open_root.setFixedWidth(100)
        btn_open_root.setFont(QFont("Segoe UI", 10))
        btn_open_root.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #6b83d4;
            }}
        """)
        btn_open_root.clicked.connect(self._open_analyses_folder)
        path_row.addWidget(btn_open_root)

        btn_manage = QPushButton("Gérer les analyses")
        btn_manage.setMinimumHeight(38)
        btn_manage.setFixedWidth(170)
        btn_manage.setFont(QFont("Segoe UI", 10))
        btn_manage.setStyleSheet(f"""
            QPushButton {{
                background-color: #2c2c3c;
                color: #ffffff;
                border: 1px solid #3c3c4c;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #3c3c4c;
                border-color: {ACCENT};
            }}
        """)
        btn_manage.clicked.connect(self._open_analysis_cleanup_dialog)
        path_row.addWidget(btn_manage)

        layout.addLayout(path_row)
        return container

    def _build_corpus_settings_block(self):
        """Bloc compact dédié aux corpus."""
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: #ffffff;
                border: 1px solid #3a3a4a;
                border-radius: 6px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        title = QLabel("Corpus")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000; border: none; background: transparent;")
        layout.addWidget(title)

        desc = QLabel("Contient les corpus utilisés pour les analyses.")
        desc.setFont(QFont("Segoe UI", 9))
        desc.setStyleSheet("color: #555555; border: none; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        path_row = QHBoxLayout()
        path_label = QLabel("Dossier :")
        path_label.setFixedWidth(120)
        path_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        path_row.addWidget(path_label)

        corpus_root_label = QLabel(self._format_display_path(self._project_root / "Data" / "Corpus"))
        corpus_root_label.setFont(QFont("Courier New", 9))
        corpus_root_label.setStyleSheet("color: #333333; border: none; background: transparent;")
        corpus_root_label.setWordWrap(True)
        path_row.addWidget(corpus_root_label, stretch=1)

        btn_open = QPushButton("Ouvrir")
        btn_open.setMinimumHeight(38)
        btn_open.setFixedWidth(100)
        btn_open.setFont(QFont("Segoe UI", 10))
        btn_open.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #6b83d4;
            }}
        """)
        btn_open.clicked.connect(self._open_corpus_folder)
        path_row.addWidget(btn_open)

        btn_manage = QPushButton("Gérer les corpus")
        btn_manage.setMinimumHeight(38)
        btn_manage.setFixedWidth(160)
        btn_manage.setFont(QFont("Segoe UI", 10))
        btn_manage.setStyleSheet(f"""
            QPushButton {{
                background-color: #2c2c3c;
                color: #ffffff;
                border: 1px solid #3c3c4c;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #3c3c4c;
                border-color: {ACCENT};
            }}
        """)
        btn_manage.clicked.connect(self._open_corpus_cleanup_dialog)
        path_row.addWidget(btn_manage)

        layout.addLayout(path_row)
        return container
    
    # === Helpers ===
    
    def _make_folder_row(self, name, path, description, callback):
        """Crée une ligne avec nom, chemin, description et bouton d'ouverture."""
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: #ffffff;
                border: 1px solid #3a3a4a;
                border-radius: 6px;
                padding: 12px;
            }}
        """)
        
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(12, 10, 12, 10)
        row_layout.setSpacing(12)
        
        # Colonne gauche : Infos
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Nom du dossier
        name_label = QLabel(name)
        name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #000000; border: none; background: transparent;")
        info_layout.addWidget(name_label)
        
        # Chemin
        path_label = QLabel(self._format_display_path(path))
        path_label.setFont(QFont("Courier New", 9))
        path_label.setStyleSheet("color: #333333; border: none; background: transparent;")
        info_layout.addWidget(path_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setStyleSheet("color: #555555; border: none; background: transparent;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        row_layout.addLayout(info_layout, stretch=1)
        
        # Bouton à droite
        btn = QPushButton("Ouvrir")
        btn.setFont(QFont("Segoe UI", 10))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(36)
        btn.setFixedWidth(100)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #6b83d4;
            }}
        """)
        btn.clicked.connect(callback)
        row_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        return container
    
    def _make_folder_button(self, text, callback):
        """Crée un bouton stylisé pour ouvrir un dossier."""
        btn = QPushButton(text)
        btn.setFont(QFont("Segoe UI", 10))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(40)
        btn.setMinimumWidth(160)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2c2c3c;
                color: {TEXT_PRIMARY};
                border: 1px solid #3c3c4c;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #3c3c4c;
                border-color: {ACCENT};
            }}
        """)
        btn.clicked.connect(callback)
        return btn
    
    # === Slots ===
    
    def _open_corpus_folder(self):
        """Ouvre le dossier Data/Corpus."""
        folder = self._project_root / "Data" / "Corpus"
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
    
    def _open_analyses_folder(self):
        """Ouvre le dossier parent des analyses."""
        folder = Path(self._settings.get("analyses_root_path", str(get_default_analyses_root())))
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _open_analysis_cleanup_dialog(self):
        """Ouvre la fenêtre dédiée à la gestion des analyses."""
        dialog = AnalysisCleanupDialog(self)
        dialog.exec()

    def _open_corpus_cleanup_dialog(self):
        """Ouvre la fenêtre dédiée à la gestion des corpus."""
        dialog = CorpusCleanupDialog(self)
        dialog.exec()
    
    def _open_logs_folder(self):
        """Ouvre le dossier logs."""
        folder = self._project_root / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
    
    def _refresh_disk_usage(self):
        """Calcule l'espace disque utilisé par les modèles (par outil)."""
        # Mettre à jour les labels en "Calcul..."
        self._stanza_size_label.setText("Calcul...")
        self._spacy_size_label.setText("Calcul...")
        self._total_size_label.setText("Calcul...")
        
        # Force repaint
        self._stanza_size_label.repaint()
        self._spacy_size_label.repaint()
        self._total_size_label.repaint()
        
        try:
            # Chemins des modèles
            stanza_cache = self._detect_stanza_cache_path()
            
            # Pour SpaCy, demander directement à Python où il est installé
            # (fonctionne en dev comme en production)
            try:
                import spacy
                spacy_cache = Path(spacy.__file__).parent.parent  # Remonte au site-packages
            except ImportError:
                # Fallback si spaCy n'est pas installé
                spacy_cache = Path.home() / ".local" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
            
            # Calculer la taille de chaque cache
            stanza_size = self._get_directory_size(stanza_cache)
            # Pour SpaCy, on cherche les modèles fr_* et en_* dans site-packages
            spacy_size = 0
            if spacy_cache.exists():
                for model_dir in spacy_cache.glob("*"):
                    if model_dir.is_dir() and (model_dir.name.startswith("fr_") or model_dir.name.startswith("en_")):
                        spacy_size += self._get_directory_size(model_dir)
            total_size = stanza_size + spacy_size
            
            # Fonction pour formater la taille
            def format_size(size_bytes):
                if size_bytes == 0:
                    return "0 Mo"
                elif size_bytes > 1_000_000_000:
                    return f"{size_bytes / 1_000_000_000:.2f} Go"
                else:
                    return f"{size_bytes / 1_000_000:.2f} Mo"
            
            # Mettre à jour les labels
            self._stanza_size_label.setText(format_size(stanza_size))
            self._spacy_size_label.setText(format_size(spacy_size))
            self._total_size_label.setText(format_size(total_size))
            
        except Exception as e:
            self._stanza_size_label.setText("Erreur")
            self._spacy_size_label.setText("Erreur")
            self._total_size_label.setText(f"Erreur : {e}")
    
    def _clean_models_cache(self):
        """Nettoie le cache des modèles."""
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer tous les modèles téléchargés ?\n"
            "Ils devront être retéléchargés lors de la prochaine utilisation.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import shutil
                stanza_cache = self._detect_stanza_cache_path()
                
                if stanza_cache.exists():
                    shutil.rmtree(stanza_cache)
                
                QMessageBox.information(self, "Succès", "Cache des modèles nettoyé avec succès.")
                self._refresh_disk_usage()
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Impossible de nettoyer le cache : {e}")
    
    def _clean_old_logs(self):
        """Nettoie les anciens fichiers de logs."""
        retention_days = self._retention_spin.value()
        logs_folder = self._project_root / "logs"
        
        if not logs_folder.exists():
            QMessageBox.information(self, "Info", "Aucun dossier de logs trouvé.")
            return
        
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            deleted_count = 0
            
            for log_file in logs_folder.glob("*.log"):
                if log_file.is_file():
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        log_file.unlink()
                        deleted_count += 1
            
            QMessageBox.information(
                self,
                "Succès",
                f"{deleted_count} fichier(s) de logs supprimé(s)."
            )
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de nettoyer les logs : {e}")

    def _reset_settings(self):
        """Réinitialise tous les paramètres aux valeurs par défaut."""
        reply = QMessageBox.question(
            self,
            "Confirmer la réinitialisation",
            "Êtes-vous sûr de vouloir réinitialiser tous les paramètres ?\n"
            "Cette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self._settings_file.exists():
                self._settings_file.unlink()
            self._load_settings()
            
            # Recharger l'UI
            self._log_level_combo.setCurrentText(self._settings.get("log_level", "Normal"))
            self._retention_spin.setValue(self._settings.get("log_retention_days", 30))
            self._analyses_root_path = str(
                Path(self._settings.get("analyses_root_path", str(get_default_analyses_root()))).expanduser()
            )
            self._analyses_root_label.setText(self._format_display_path(self._analyses_root_path))
            self._prepared_archive_prompt_checkbox.setChecked(
                self._settings.get("prompt_prepared_archive_on_first_analysis", True)
            )
            
            QMessageBox.information(self, "Succès", "Paramètres réinitialisés avec succès.")
    
    def _on_save_clicked(self):
        """Sauvegarde tous les paramètres."""
        self._settings["log_level"] = self._log_level_combo.currentText()
        self._settings["log_retention_days"] = self._retention_spin.value()
        self._settings["analyses_root_path"] = self._analyses_root_path or str(get_default_analyses_root())
        self._settings["prompt_prepared_archive_on_first_analysis"] = self._prepared_archive_prompt_checkbox.isChecked()
        
        self._save_settings()
        QMessageBox.information(self, "Succès", "Paramètres enregistrés avec succès.")
