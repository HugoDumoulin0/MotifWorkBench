"""
Page Concordancier : Analyse et visualisation des concordances.
@jcharlesDS (2026)
"""

from pathlib import Path
import json
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QLineEdit, QTableWidget, QComboBox,
    QTableWidgetItem, QRadioButton, QButtonGroup, QHeaderView,
    QSizePolicy, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from gui.widgets.base_page import BasePage, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT
from gui.core.analysis_paths import get_analyses_root

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.concordancer import (
    search_concordances, format_concordances_for_display, enrich_concordances_with_metadata, get_metadata_columns
)
from src import formate_patterns, tools

class ConcordancerPage(BasePage):
    """Recherche un terme dans le corpus CWB et affiche les concordances."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = Path(__file__).resolve().parents[2]
        self._load_registry_path()
        self._load_preferences()
        self._closed_motifs = []
        self._last_search_label = ""
        self._last_search_type = ""
        self._metadata_columns = []
        self._enriched_data = []
        self._build_ui()

    def _load_preferences(self):
        """Charge les préférences utiles au concordancier."""
        self._closed_motif_display_mode = "matched_words"
        settings_file = self._project_root / "app_settings.json"
        if not settings_file.exists():
            return

        try:
            with open(settings_file, "r", encoding="utf-8") as handle:
                settings = json.load(handle)
            self._closed_motif_display_mode = settings.get(
                "closed_motif_concordance_display",
                "matched_words",
            )
        except Exception:
            self._closed_motif_display_mode = "matched_words"
    
    def _load_registry_path(self):
        """Charge le chemin du registry CWB depuis la dernière analyse."""
        last_analysis_file = self._project_root / "logs" / "last_analysis.json"
        
        if last_analysis_file.exists():
            try:
                with open(last_analysis_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    self._registry_path = info.get("cwb_registry")
                    if self._registry_path and Path(self._registry_path).exists():
                        return
            except Exception:
                pass

        latest_registry = self._find_latest_analysis_registry()
        if latest_registry is not None:
            self._registry_path = str(latest_registry)
            return

        self._registry_path = ""

    def _load_closed_motifs(self):
        """Charge les motifs clos de la dernière analyse pour usage dans le concordancier."""
        self._closed_motifs = []
        last_analysis_file = self._project_root / "logs" / "last_analysis.json"
        if not last_analysis_file.exists():
            return

        try:
            with open(last_analysis_file, "r", encoding="utf-8") as handle:
                info = json.load(handle)
        except Exception:
            return

        patterns_results = info.get("patterns_results")
        if not patterns_results:
            return

        patterns_root = Path(patterns_results)
        closed_dir = patterns_root / "Closed"
        analysis_root = patterns_root.parent
        lexicon_path = analysis_root / "Lexiques" / "dico_str_to_int_all_items.pk"

        if not closed_dir.exists() or not lexicon_path.exists():
            return

        closed_files = sorted(closed_dir.glob("*_sorted_closed.pk"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not closed_files:
            return

        try:
            lexic_int_str = formate_patterns.make_dict_int_to_str(str(lexicon_path))
            motifs = tools.from_pk_corpus_to_list(str(closed_files[0]))
            for motif in motifs:
                motif_str = formate_patterns.from_int_to_str(motif, lexic_int_str)
                cqp_pattern = str(tools.read_req_CQP(motif_str))
                self._closed_motifs.append({
                    "label": cqp_pattern,
                    "pattern": cqp_pattern,
                })
        except Exception:
            self._closed_motifs = []

    def _find_latest_analysis_registry(self):
        """Retourne le registry de l'analyse la plus récente disposant d'un corpus CWB."""
        analyses_root = get_analyses_root()
        if not analyses_root.exists():
            return None

        candidate_registries = []
        for registry_path in analyses_root.glob("*/*/cwb-corpus/registry"):
            merged_file = registry_path / "merged"
            if merged_file.exists():
                try:
                    candidate_registries.append((merged_file.stat().st_mtime, registry_path))
                except OSError:
                    continue

        if not candidate_registries:
            return None

        candidate_registries.sort(key=lambda item: item[0], reverse=True)
        return candidate_registries[0][1]
    
    def showEvent(self, event):
        """Recharge le registry_path à chaque affichage de la page."""
        super().showEvent(event)
        self._load_registry_path()
        self._load_preferences()
        self._load_closed_motifs()
        self._refresh_closed_motifs_combo()
        self._refresh_registry_label()
        self._refresh_closed_motif_display_label()

    def _refresh_registry_label(self):
        """Met à jour le libellé visible du registry CWB utilisé."""
        registry_path = Path(self._registry_path) if self._registry_path else None
        if registry_path and registry_path.exists():
            status = "actif"
            color = "#047857"
        else:
            status = "introuvable"
            color = "#b45309"

        path_text = self._registry_path if self._registry_path else "(non défini)"
        self._registry_label.setText(
            f"Registry CWB utilisé : {path_text} ({status})"
        )
        self._registry_label.setStyleSheet(
            f"color: {color}; background-color: transparent; font-size: 9pt;"
        )

    def _refresh_closed_motif_display_label(self):
        """Met à jour le libellé du mode d'affichage des motifs."""
        if self._closed_motif_display_mode == "motif":
            label_text = "Affichage des motifs : motif"
        else:
            label_text = "Affichage des motifs : mots trouvés"

        self._closed_motif_display_label.setText(label_text)
        self._closed_motif_display_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background-color: transparent; font-size: 9pt; font-style: italic;"
        )
    
    # --- Construction UI ---
    
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
            "Concordancier",
            "Recherchez un terme et explorez ses occurrences dans les textes."
        ))
        
        # Paramètres de recherche
        search_group = self.make_group("Recherche")
        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(12)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(12)

        mode_label = QLabel("Mode :")
        mode_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        mode_label.setFont(QFont("Segoe UI", 10))
        mode_row.addWidget(mode_label)

        self._mode_group = QButtonGroup()

        self._radio_free_mode = QRadioButton("Recherche libre")
        self._radio_free_mode.setChecked(True)
        self._radio_free_mode.toggled.connect(self._update_search_mode_ui)
        self._radio_free_mode.setStyleSheet(f"""
            QRadioButton {{
                color: {TEXT_PRIMARY};
                background-color: transparent;
                spacing: 5px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid #9ca3af;
                border-radius: 9px;
                background-color: #ffffff;
            }}
            QRadioButton::indicator:checked {{
                background-color: {ACCENT};
                border-color: {ACCENT};
            }}
        """)
        self._mode_group.addButton(self._radio_free_mode, 0)
        mode_row.addWidget(self._radio_free_mode)

        self._radio_closed_mode = QRadioButton("Motifs enregistrés")
        self._radio_closed_mode.toggled.connect(self._update_search_mode_ui)
        self._radio_closed_mode.setStyleSheet(self._radio_free_mode.styleSheet())
        self._mode_group.addButton(self._radio_closed_mode, 1)
        mode_row.addWidget(self._radio_closed_mode)

        self._radio_cqp_mode = QRadioButton("CQP")
        self._radio_cqp_mode.toggled.connect(self._update_search_mode_ui)
        self._radio_cqp_mode.setStyleSheet(self._radio_free_mode.styleSheet())
        self._mode_group.addButton(self._radio_cqp_mode, 2)
        mode_row.addWidget(self._radio_cqp_mode)
        mode_row.addStretch()
        search_layout.addLayout(mode_row)

        # Ligne 1: Champ de recherche + Bouton
        self._free_search_row = QWidget()
        row1 = QHBoxLayout(self._free_search_row)
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(8)
        
        self._query_input = QLineEdit()
        self._query_input.setPlaceholderText("Entrez un terme à rechercher...")
        self._query_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #1f2937;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 10px;
            }
        """)
        self._query_input.returnPressed.connect(self._run_search)
        row1.addWidget(self._query_input, 4)
        
        self._search_btn = QPushButton("Rechercher")
        self._search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._search_btn.setMinimumHeight(38)
        self._search_btn.clicked.connect(self._run_search)
        self._search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: #4a4a6a;
            }}
            QPushButton:pressed {{
                background-color: #2a2a4a;
            }}
        """)
        row1.addWidget(self._search_btn, 1)
        search_layout.addWidget(self._free_search_row)

        self._cqp_hint_label = QLabel(
            "Entrez directement un motif CQP valide, sans le nom du corpus ni des commandes comme "
            "MERGED;, show, cat ou exit;."
        )
        self._cqp_hint_label.setWordWrap(True)
        self._cqp_hint_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background-color: transparent; font-size: 9pt; font-style: italic;"
        )
        search_layout.addWidget(self._cqp_hint_label)
        
        # Ligne 2: Boutons radio pour le type de recherche
        self._free_search_type_row = QWidget()
        row2 = QHBoxLayout(self._free_search_type_row)
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(12)
        
        type_label = QLabel("Type de recherche:")
        type_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        type_label.setFont(QFont("Segoe UI", 10))
        row2.addWidget(type_label)
        
        self._search_type_group = QButtonGroup()
        
        self._radio_word = QRadioButton("Mot")
        self._radio_word.setChecked(True)
        self._radio_word.setStyleSheet(f"""
            QRadioButton {{
                color: {TEXT_PRIMARY};
                background-color: transparent;
                spacing: 5px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid #9ca3af;
                border-radius: 9px;
                background-color: #ffffff;
            }}
            QRadioButton::indicator:checked {{
                background-color: {ACCENT};
                border-color: {ACCENT};
            }}
            QRadioButton::indicator:hover {{
                border-color: {ACCENT};
            }}
        """)
        self._search_type_group.addButton(self._radio_word, 0)
        row2.addWidget(self._radio_word)
        
        self._radio_lemma = QRadioButton("Lemme")
        self._radio_lemma.setStyleSheet(f"""
            QRadioButton {{
                color: {TEXT_PRIMARY};
                background-color: transparent;
                spacing: 5px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid #9ca3af;
                border-radius: 9px;
                background-color: #ffffff;
            }}
            QRadioButton::indicator:checked {{
                background-color: {ACCENT};
                border-color: {ACCENT};
            }}
            QRadioButton::indicator:hover {{
                border-color: {ACCENT};
            }}
        """)
        self._search_type_group.addButton(self._radio_lemma, 1)
        row2.addWidget(self._radio_lemma)
        
        self._radio_pos = QRadioButton("Catégorie (POS)")
        self._radio_pos.setStyleSheet(f"""
            QRadioButton {{
                color: {TEXT_PRIMARY};
                background-color: transparent;
                spacing: 5px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid #9ca3af;
                border-radius: 9px;
                background-color: #ffffff;
            }}
            QRadioButton::indicator:checked {{
                background-color: {ACCENT};
                border-color: {ACCENT};
            }}
            QRadioButton::indicator:hover {{
                border-color: {ACCENT};
            }}
        """)
        self._search_type_group.addButton(self._radio_pos, 2)
        row2.addWidget(self._radio_pos)
        
        row2.addStretch()
        search_layout.addWidget(self._free_search_type_row)

        self._closed_motif_row = QWidget()
        row_motif = QHBoxLayout(self._closed_motif_row)
        row_motif.setContentsMargins(0, 0, 0, 0)
        row_motif.setSpacing(8)

        motif_label = QLabel("Motif :")
        motif_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        motif_label.setFont(QFont("Segoe UI", 10))
        row_motif.addWidget(motif_label)

        self._closed_motif_list = QListWidget()
        self._closed_motif_list.setMinimumWidth(420)
        self._closed_motif_list.setMinimumHeight(120)
        self._closed_motif_list.setMaximumHeight(140)
        self._closed_motif_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._closed_motif_list.setWordWrap(False)
        self._closed_motif_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._closed_motif_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self._closed_motif_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                color: #1f2937;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px 8px;
            }
            QListWidget::item:selected {
                background-color: #dbeafe;
                color: #1e3a8a;
            }
        """)
        self._closed_motif_list.itemDoubleClicked.connect(lambda _item: self._run_closed_motif_search())
        row_motif.addWidget(self._closed_motif_list, 1)

        self._search_motif_btn = QPushButton("Chercher le motif")
        self._search_motif_btn.setMinimumHeight(34)
        self._search_motif_btn.setMaximumHeight(34)
        self._search_motif_btn.clicked.connect(self._run_closed_motif_search)
        self._search_motif_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: #4a4a6a;
            }}
            QPushButton:disabled {{
                background-color: #d1d5db;
                color: #9ca3af;
            }}
        """)
        row_motif.addWidget(self._search_motif_btn)
        search_layout.addWidget(self._closed_motif_row)
        self._refresh_closed_motifs_combo()
        self._update_search_mode_ui()

        self._closed_motif_display_label = QLabel()
        self._closed_motif_display_label.setWordWrap(True)
        search_layout.addWidget(self._closed_motif_display_label)
        self._refresh_closed_motif_display_label()
        
        # ÉTAPE 4 : Nouvelle interface de filtrage avec colonnes/valeurs
        row3 = QHBoxLayout()
        row3.setSpacing(12)
        
        filter_label = QLabel("Filtrer par:")
        filter_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        filter_label.setFont(QFont("Segoe UI", 10))
        row3.addWidget(filter_label)
        
        # Dropdown : Sélection de la colonne de métadonnées
        self._filter_column_combo = QComboBox()
        self._filter_column_combo.setMaxVisibleItems(15)  # Limite la hauteur du dropdown
        self._filter_column_combo.setEnabled(False)
        self._filter_column_combo.setPlaceholderText("Colonne...")
        self._filter_column_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #1f2937;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 10px;
                min-width: 140px;
            }
            QComboBox:disabled {
                background-color: #f3f4f6;
                color: #9ca3af;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self._filter_column_combo.currentTextChanged.connect(self._on_filter_column_changed)
        row3.addWidget(self._filter_column_combo)
        
        # Dropdown : Sélection de la valeur
        self._filter_value_combo = QComboBox()
        self._filter_value_combo.setMaxVisibleItems(15)  # Limite la hauteur du dropdown
        self._filter_value_combo.setEnabled(False)
        self._filter_value_combo.setPlaceholderText("Valeur...")
        self._filter_value_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #1f2937;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 10px;
                min-width: 140px;
            }
            QComboBox:disabled {
                background-color: #f3f4f6;
                color: #9ca3af;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self._filter_value_combo.currentTextChanged.connect(self._apply_filters)
        row3.addWidget(self._filter_value_combo)
        
        row3.addStretch()
        search_layout.addLayout(row3)
        
        # Ligne 4 : Ordre, Export CSV, Graphique
        row4 = QHBoxLayout()
        row4.setSpacing(12)
        
        order_label = QLabel("Ordre:")
        order_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        order_label.setFont(QFont("Segoe UI", 10))
        row4.addWidget(order_label)
        
        self._order_combo = QComboBox()
        self._order_combo.addItems(["A → Z", "Z → A"])
        self._order_combo.setEnabled(False)
        self._order_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #1f2937;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 10px;
                min-width: 100px;
            }
            QComboBox:disabled {
                background-color: #f3f4f6;
                color: #9ca3af;
            }
        """)
        self._order_combo.currentIndexChanged.connect(self._apply_sorting)
        row4.addWidget(self._order_combo)
        
        row4.addStretch()
        
        # Bouton Export CSV
        self._export_csv_btn = QPushButton("Exporter CSV")
        self._export_csv_btn.setEnabled(False)
        self._export_csv_btn.setMinimumHeight(32)
        self._export_csv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._export_csv_btn.clicked.connect(self._export_to_csv)
        self._export_csv_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: #4a4a6a;
            }}
            QPushButton:disabled {{
                background-color: #d1d5db;
                color: #9ca3af;
            }}
        """)
        row4.addWidget(self._export_csv_btn)
        
        # Bouton Graphique de distribution
        self._chart_btn = QPushButton("Distribution")
        self._chart_btn.setEnabled(False)
        self._chart_btn.setMinimumHeight(32)
        self._chart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._chart_btn.clicked.connect(self._show_distribution_chart)
        self._chart_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: #4a4a6a;
            }}
            QPushButton:disabled {{
                background-color: #d1d5db;
                color: #9ca3af;
            }}
        """)
        row4.addWidget(self._chart_btn)
        
        search_layout.addLayout(row4)

        self._registry_label = QLabel()
        self._registry_label.setWordWrap(True)
        search_layout.addWidget(self._registry_label)
        self._refresh_registry_label()
        
        layout.addWidget(search_group)
        
        # Résultats
        results_group = self.make_group("Concordances")
        results_layout = QVBoxLayout(results_group)
        
        self._stats_label = QLabel("Aucune recherche lancée.")
        self._stats_label.setFont(QFont("Segoe UI", 10))
        self._stats_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        results_layout.addWidget(self._stats_label)
        
        self._results_table = QTableWidget()
        self._results_table.setMinimumHeight(500)
        
        # Configuration initiale (4 colonnes)
        self._results_table.setColumnCount(4)
        self._results_table.setHorizontalHeaderLabels(["Contexte gauche", "Terme", "Contexte droit", "Source"])
        
        # Activer le tri
        self._results_table.setSortingEnabled(True)
        
        # Configuration des colonnes pour un meilleur affichage
        header = self._results_table.horizontalHeader()
        header.setStretchLastSection(True)  # La dernière colonne s'étend pour remplir l'espace
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Contexte gauche
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Terme
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Contexte droit
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Source - s'étend pour combler
        
        # Définir les largeurs par défaut
        self._results_table.setColumnWidth(0, 350)  # Contexte gauche
        self._results_table.setColumnWidth(2, 350)  # Contexte droit
        
        self._results_table.setAlternatingRowColors(True)
        self._results_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #e5e7eb;
                border: 1px solid #d1d5db;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 6px;
                color: #111827;
            }
            QTableWidget::item:selected {
                background-color: #dbeafe;
                color: #1e3a8a;
            }
            QHeaderView::section {
                background-color: #f3f4f6;
                color: #374151;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #d1d5db;
                font-weight: bold;
            }
            QTableWidget::item:alternate {
                background-color: #f9fafb;
            }
        """)
        results_layout.addWidget(self._results_table, 1)  # stretch factor = 1 pour prendre l'espace
        layout.addWidget(results_group, 1)  # stretch factor = 1 pour expansion
        
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _refresh_closed_motifs_combo(self):
        self._closed_motif_list.clear()
        if not self._closed_motifs:
            item = QListWidgetItem("Aucun motif disponible")
            item.setData(Qt.ItemDataRole.UserRole, "")
            self._closed_motif_list.addItem(item)
            self._search_motif_btn.setEnabled(False)
            return

        for motif in self._closed_motifs:
            item = QListWidgetItem(motif["label"])
            item.setData(Qt.ItemDataRole.UserRole, motif["pattern"])
            self._closed_motif_list.addItem(item)
        self._closed_motif_list.setCurrentRow(0)
        self._search_motif_btn.setEnabled(True)

    def _filter_visible_metadata_columns(self, columns):
        """Masque les colonnes de comptage redondantes dans le concordancier."""
        visible_columns = list(columns)

        if "num_words" in visible_columns and "word_count" in visible_columns:
            visible_columns.remove("word_count")

        if "num_sents" in visible_columns and "sentence_count" in visible_columns:
            visible_columns.remove("sentence_count")
        elif "num_sent" in visible_columns and "sentence_count" in visible_columns:
            visible_columns.remove("sentence_count")

        return visible_columns

    def _update_search_mode_ui(self):
        free_mode = self._radio_free_mode.isChecked()
        cqp_mode = self._radio_cqp_mode.isChecked()
        self._free_search_row.setVisible(free_mode or cqp_mode)
        self._free_search_type_row.setVisible(free_mode)
        self._closed_motif_row.setVisible(self._radio_closed_mode.isChecked())
        self._cqp_hint_label.setVisible(cqp_mode)

        if cqp_mode:
            self._query_input.setPlaceholderText('Ex: [lemma="go"] []{0,3} [pos="NOUN"]')
            self._search_btn.setText("Exécuter")
        elif free_mode:
            self._query_input.setPlaceholderText("Entrez un terme à rechercher...")
            self._search_btn.setText("Rechercher")

    def _validate_cqp_query(self, query: str) -> str:
        """Valide sommairement une requête CQP saisie par l'utilisateur."""
        stripped = query.strip()
        if not stripped:
            return "Veuillez entrer une requête CQP."

        forbidden_tokens = [";", "exit", "show", "cat ", "dump", "set ", "tabulate", "group ", "count ", "size "]
        lowered = stripped.lower()
        if any(token in lowered for token in forbidden_tokens):
            return (
                "La requête CQP doit contenir uniquement le motif à chercher, "
                "sans commandes CQP complètes."
            )

        return ""
    
    def _run_search(self):
        query = self._query_input.text().strip()
        
        if not query:
            self._stats_label.setText("Veuillez entrer un terme à rechercher.")
            self._results_table.setRowCount(0)
            return

        if self._radio_cqp_mode.isChecked():
            validation_error = self._validate_cqp_query(query)
            if validation_error:
                self._stats_label.setText(validation_error)
                self._results_table.setRowCount(0)
                return
            self._execute_search(query, "cqp", motif_label="requête CQP")
            return
        
        # Déterminer le type de recherche
        if self._radio_word.isChecked():
            search_type = "word"
        elif self._radio_lemma.isChecked():
            search_type = "lemma"
        else:
            search_type = "pos"

        self._execute_search(query, search_type)

    def _run_closed_motif_search(self):
        if not self._closed_motifs:
            self._stats_label.setText("Aucun motif disponible pour la dernière analyse.")
            return

        current_item = self._closed_motif_list.currentItem()
        if current_item is None:
            self._stats_label.setText("Sélectionnez un motif.")
            return

        motif_label = current_item.text().strip()
        pattern = current_item.data(Qt.ItemDataRole.UserRole)
        if not pattern:
            self._stats_label.setText("Sélectionnez un motif.")
            return

        self._execute_search(pattern, "cqp", motif_label=motif_label)

    def _execute_search(self, query: str, search_type: str, motif_label: str = ""):
        search_label = query
        if search_type == "cqp":
            search_label = motif_label or "requête CQP"
        self._last_search_label = search_label
        self._last_search_type = search_type
        
        # Afficher un message de chargement
        self._stats_label.setText(f"Recherche en cours de '{search_label}' ({search_type})...")
        self._results_table.setRowCount(0)
        self._search_btn.setEnabled(False)
        self._search_motif_btn.setEnabled(False)

        if not self._registry_path or not Path(self._registry_path).exists():
            self._stats_label.setText(
                "Registry CWB introuvable. Lancez d'abord une analyse complète terminée, puis rouvrez le concordancier."
            )
            self._search_btn.setEnabled(True)
            self._search_motif_btn.setEnabled(bool(self._closed_motifs))
            return
        
        try:
            # Lancer la recherche CQP
            concordances = search_concordances(
                query=query,
                search_type=search_type,
                context_words=10,
                registry_path=self._registry_path
            )

            if search_type == "cqp" and self._closed_motif_display_mode == "motif":
                motif_text = motif_label or query
                concordances = [
                    (left_context, motif_text, right_context, source_id)
                    for left_context, _keyword, right_context, source_id in concordances
                ]
            
            if not concordances:
                self._stats_label.setText(
                    f"Aucune occurrence trouvée dans le corpus. Registry utilisé : {self._registry_path}"
                )
                self._enriched_data = []
                self._metadata_columns = []
                self._update_filters([])
                return
            
            # Enrichir avec métadonnées
            self._enriched_data = enrich_concordances_with_metadata(concordances)
            
            # Détecter les colonnes de métadonnées disponibles
            if self._enriched_data:
                first_item = self._enriched_data[0]
                base_cols = ['left_context', 'keyword', 'right_context', 'source_id']
                raw_metadata_columns = [k for k in first_item.keys() if k not in base_cols]
                self._metadata_columns = self._filter_visible_metadata_columns(raw_metadata_columns)
                print(f"[Concordancier] Colonnes détectées dans les données enrichies : {list(first_item.keys())}")
                print(f"[Concordancier] Colonnes de métadonnées : {self._metadata_columns}")
            else:
                self._metadata_columns = []
                print("[Concordancier] Aucune donnée enrichie")
            
            # Mettre à jour les filtres
            self._update_filters(self._metadata_columns)
            
            # Configurer le tableau avec colonnes dynamiques
            base_headers = ["Contexte gauche", "Terme", "Contexte droit", "Source"]
            all_headers = base_headers + self._metadata_columns
            self._results_table.setColumnCount(len(all_headers))
            self._results_table.setHorizontalHeaderLabels(all_headers)
            
            # Configurer les largeurs de colonnes
            header = self._results_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Contexte gauche
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Terme
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Contexte droit
            
            # Source et métadonnées : ResizeToContents
            for i in range(3, len(all_headers)):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
            # Définir largeurs par défaut pour contextes
            self._results_table.setColumnWidth(0, 300)
            self._results_table.setColumnWidth(2, 300)
            
            # Remplir le tableau
            self._populate_table()
            
            # Mettre à jour les statistiques
            self._update_stats()
            
        except Exception as e:
            self._stats_label.setText(f"Erreur lors de la recherche: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            self._search_btn.setEnabled(True)
            self._search_motif_btn.setEnabled(bool(self._closed_motifs))
    
    def _populate_table(self):
        """Remplit le tableau avec les données enrichies."""
        self._results_table.setSortingEnabled(False)  # Désactiver le tri pendant remplissage
        self._results_table.setRowCount(len(self._enriched_data))
        
        for row, item in enumerate(self._enriched_data):
            # Contexte gauche (aligné à droite)
            item_left = QTableWidgetItem(item['left_context'])
            item_left.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._results_table.setItem(row, 0, item_left)
            
            # Terme trouvé (gras, centré)
            item_keyword = QTableWidgetItem(item['keyword'])
            item_keyword.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            item_keyword.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._results_table.setItem(row, 1, item_keyword)
            
            # Contexte droit (aligné à gauche)
            item_right = QTableWidgetItem(item['right_context'])
            item_right.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._results_table.setItem(row, 2, item_right)
            
            # Source
            item_source = QTableWidgetItem(item['source_id'])
            item_source.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._results_table.setItem(row, 3, item_source)
            
            # Colonnes de métadonnées
            for col_idx, col_name in enumerate(self._metadata_columns, start=4):
                value = str(item.get(col_name, ""))
                item_meta = QTableWidgetItem(value)
                item_meta.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._results_table.setItem(row, col_idx, item_meta)
        
        self._results_table.setSortingEnabled(True) 
    
    def _update_filters(self, metadata_columns):
        """Met à jour le dropdown des colonnes de métadonnées disponibles."""
        # Réinitialiser les dropdowns
        self._filter_column_combo.clear()
        self._filter_value_combo.clear()
        self._filter_column_combo.setEnabled(False)
        self._filter_value_combo.setEnabled(False)
        self._order_combo.setEnabled(False)
        self._export_csv_btn.setEnabled(False)
        self._chart_btn.setEnabled(False)
        
        if not metadata_columns or not self._enriched_data:
            return
        
        # Remplir le dropdown des colonnes
        self._filter_column_combo.addItem("Toutes les occurrences")  # Option par défaut
        self._filter_column_combo.addItems(metadata_columns)
        self._filter_column_combo.setEnabled(True)
        
        # Activer les boutons d'export et graphique
        self._export_csv_btn.setEnabled(True)
        self._chart_btn.setEnabled(True)
    
    def _on_filter_column_changed(self, column_name: str):
        """Met à jour les valeurs disponibles quand on change de colonne."""
        self._filter_value_combo.clear()
        
        if not column_name or column_name == "Toutes les occurrences":
            self._filter_value_combo.setEnabled(False)
            self._order_combo.setEnabled(False)
            # Afficher toutes les lignes
            for row in range(self._results_table.rowCount()):
                self._results_table.setRowHidden(row, False)
            self._update_stats()
            return
        
        # Extraire les valeurs uniques pour cette colonne
        values = sorted(set(str(item.get(column_name, "")) for item in self._enriched_data))
        values = [v for v in values if v]  # Retirer les valeurs vides
        
        # Bloquer les signaux pendant le remplissage pour éviter les appels inutiles
        self._filter_value_combo.blockSignals(True)
        self._filter_value_combo.addItem("Toutes les valeurs")
        self._filter_value_combo.addItems(values)
        self._filter_value_combo.setCurrentIndex(0)  # Sélectionner "Toutes les valeurs" par défaut
        self._filter_value_combo.blockSignals(False)
        self._filter_value_combo.setEnabled(True)
        self._order_combo.setEnabled(True)
        
        # Appliquer le filtre pour afficher toutes les lignes (car "Toutes les valeurs" est sélectionné)
        self._apply_filters()
    
    def _apply_filters(self):
        """Applique le filtre sélectionné et cache les lignes non-conformes."""
        if not self._enriched_data:
            return
        
        column_name = self._filter_column_combo.currentText()
        filter_value = self._filter_value_combo.currentText()
        
        # Si pas de filtre actif, afficher toutes les lignes
        if not column_name or column_name == "Toutes les occurrences" or filter_value == "Toutes les valeurs":
            for row in range(self._results_table.rowCount()):
                self._results_table.setRowHidden(row, False)
            self._update_stats()
            return
        
        # Trouver l'index de la colonne dans les métadonnées
        if column_name not in self._metadata_columns:
            return
        
        col_idx = self._metadata_columns.index(column_name) + 4  # +4 pour left/keyword/right/source
        
        # Filtrer les lignes
        visible_count = 0
        for row in range(self._results_table.rowCount()):
            cell_item = self._results_table.item(row, col_idx)
            cell_value = cell_item.text() if cell_item else ""
            show = (cell_value == filter_value)
            self._results_table.setRowHidden(row, not show)
            if show:
                visible_count += 1
        
        self._update_stats()
    
    def _apply_sorting(self):
        """Applique le tri A->Z ou Z->A sur la colonne filtrée."""
        column_name = self._filter_column_combo.currentText()
        if not column_name or column_name == "Toutes les occurrences":
            return
        
        if column_name not in self._metadata_columns:
            return
        
        col_idx = self._metadata_columns.index(column_name) + 4
        order = Qt.SortOrder.AscendingOrder if self._order_combo.currentText() == "A → Z" else Qt.SortOrder.DescendingOrder
        self._results_table.sortItems(col_idx, order)
    
    def _update_stats(self):
        """Met à jour les statistiques affichées."""
        if not self._enriched_data:
            return
        
        total = len(self._enriched_data)
        visible = sum(1 for row in range(self._results_table.rowCount()) 
                     if not self._results_table.isRowHidden(row))

        query = self._last_search_label or self._query_input.text().strip()
        search_type = self._last_search_type or "word"
        
        if self._metadata_columns:
            meta_info = f" avec métadonnées ({', '.join(self._metadata_columns)})"
        else:
            meta_info = " (aucune métadonnée chargée - lancez une analyse d'abord)"
        
        self._stats_label.setText(
            f"{visible} / {total} occurrence(s) affichée(s) pour '{query}' ({search_type}){meta_info}."
        )
    
    def _export_to_csv(self):
        """Exporte les concordances visibles en CSV."""
        if not self._enriched_data:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Export impossible", "Aucune concordance à exporter.")
            return
        
        from PyQt6.QtWidgets import QFileDialog
        import csv
        
        # Demander le fichier de destination
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Exporter les concordances", 
            str(self._project_root / "concordances.csv"),
            "CSV (*.csv)"
        )
        
        if not file_path:
            return
        
        # Collecter les lignes visibles
        rows_to_export = []
        for row in range(self._results_table.rowCount()):
            if not self._results_table.isRowHidden(row):
                row_data = {}
                row_data['left_context'] = self._results_table.item(row, 0).text()
                row_data['keyword'] = self._results_table.item(row, 1).text()
                row_data['right_context'] = self._results_table.item(row, 2).text()
                row_data['source_id'] = self._results_table.item(row, 3).text()
                
                # Ajouter les colonnes de métadonnées
                for col_idx, col_name in enumerate(self._metadata_columns, start=4):
                    item = self._results_table.item(row, col_idx)
                    row_data[col_name] = item.text() if item else ""
                
                rows_to_export.append(row_data)
        
        # Écrire le CSV
        if rows_to_export:
            fieldnames = ['left_context', 'keyword', 'right_context', 'source_id'] + self._metadata_columns
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows_to_export)
            
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Export réussi", f"{len(rows_to_export)} concordance(s) exportée(s) vers :\n{file_path}")
    
    def _show_distribution_chart(self):
        """Affiche un graphique de distribution des occurrences par métadonnée."""
        column_name = self._filter_column_combo.currentText()
        
        if not column_name or column_name == "Toutes les occurrences":
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Sélection requise", "Veuillez sélectionner une colonne de métadonnées pour afficher la distribution.")
            return
        
        if not self._enriched_data:
            return
        
        # Compter les occurrences par valeur
        from collections import Counter
        values = [str(item.get(column_name, "")) for item in self._enriched_data if item.get(column_name)]
        distribution = Counter(values)
        
        if not distribution:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Pas de données", f"Aucune donnée pour la colonne '{column_name}'.")
            return
        
        # Créer un graphique simple avec matplotlib
        try:
            import matplotlib
            matplotlib.use('Qt5Agg')
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
            from PyQt6.QtWidgets import QDialog, QVBoxLayout
            
            # Créer une fenêtre de dialogue
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Distribution : {column_name}")
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(8)
            
            # Trier les données par fréquence décroissante
            sorted_items = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
            labels = [item[0] for item in sorted_items]
            counts = [item[1] for item in sorted_items]
            
            # Tronquer les labels très longs pour meilleure lisibilité
            def truncate_label(label, max_length=50):
                return label if len(str(label)) <= max_length else str(label)[:max_length-3] + "..."
            
            labels = [truncate_label(l) for l in labels]
            
            # Nombre d'éléments
            num_items = len(labels)
            
            # Logique selon le nombre d'éléments
            if num_items <= 15:
                # ≤ 15 éléments : Graphique vertical standard
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(labels, counts, color='#5a5a8a')
                ax.set_xlabel(column_name, fontsize=12)
                ax.set_ylabel('Nombre d\'occurrences', fontsize=12)
                ax.set_title(f'Distribution des occurrences par {column_name}', fontsize=14, fontweight='bold')
                # Rotation 45° avec alignement à droite
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                
                # Pas de scroll, fenêtre standard
                canvas = FigureCanvasQTAgg(fig)
                layout.addWidget(canvas)
                dialog.resize(800, 650)
                
            else:
                # > 15 éléments : Graphique horizontal avec scroll
                fig_height = max(8, num_items * 0.4)
                fig, ax = plt.subplots(figsize=(9.5, fig_height))  # Largeur réduite à 9.5 pour tenir dans la fenêtre
                
                # Barres horizontales
                y_positions = range(len(labels))
                ax.barh(y_positions, counts, color='#5a5a8a', height=0.5)  # Espacement 0.5
                ax.set_yticks(y_positions)
                
                # Taille de police adaptée selon le nombre d'éléments
                if num_items > 50:
                    fontsize_labels = 7
                elif num_items > 30:
                    fontsize_labels = 8
                else:
                    fontsize_labels = 9
                
                ax.set_yticklabels(labels, fontsize=fontsize_labels)
                ax.set_xlabel('Nombre d\'occurrences', fontsize=12)
                ax.set_ylabel(column_name, fontsize=12)
                ax.set_title(f'Distribution des occurrences par {column_name}', fontsize=14, fontweight='bold')
                ax.invert_yaxis()  # Le plus grand en haut
                
                # Ajuster les marges - réduire la largeur pour tenir dans la fenêtre
                plt.subplots_adjust(left=0.25, right=0.98, top=0.98, bottom=0.03)
                
                # Canvas dans QWidget container
                canvas = FigureCanvasQTAgg(fig)
                canvas.setMinimumHeight(int(fig_height * 100))  # Hauteur canvas = 12 (en fait fig_height * 100 pixels)
                canvas.setMinimumWidth(950)  # Largeur fixe pour correspondre à la fenêtre
                
                canvas_widget = QWidget()
                canvas_layout = QVBoxLayout(canvas_widget)
                canvas_layout.setContentsMargins(0, 0, 0, 0)
                canvas_layout.addWidget(canvas)
                
                # Container dans QScrollArea
                from PyQt6.QtWidgets import QScrollArea
                from PyQt6.QtCore import Qt as QtCore_Qt
                scroll = QScrollArea()
                scroll.setWidget(canvas_widget)
                scroll.setWidgetResizable(False)  # Important : False pour respecter la taille du canvas
                scroll.setVerticalScrollBarPolicy(QtCore_Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
                scroll.setHorizontalScrollBarPolicy(QtCore_Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                
                # Ajouter le scroll avec stretch factor pour qu'il prenne tout l'espace disponible
                layout.addWidget(scroll, 1)
                
                # Fenêtre adaptée à la largeur du graphique
                dialog.resize(1000, 750)
            
            # Bouton pour sauvegarder le graphique
            btn_save = QPushButton("Enregistrer le graphique")
            btn_save.setMinimumHeight(34)
            btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_save.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ACCENT};
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 14px;
                }}
                QPushButton:hover {{
                    background-color: #4a4a6a;
                }}
            """)
            
            def save_chart():
                from PyQt6.QtWidgets import QFileDialog
                file_path, _ = QFileDialog.getSaveFileName(
                    dialog,
                    "Enregistrer le graphique",
                    str(self._project_root / f"distribution_{column_name}.png"),
                    "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)"
                )
                if file_path:
                    fig.savefig(file_path, dpi=300, bbox_inches='tight')
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(dialog, "Sauvegarde réussie", f"Graphique enregistré :\n{file_path}")
            
            btn_save.clicked.connect(save_chart)
            layout.addWidget(btn_save)
            
            dialog.exec()
            
        except ImportError:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Matplotlib requis", "Installez matplotlib pour afficher les graphiques : pip install matplotlib")
