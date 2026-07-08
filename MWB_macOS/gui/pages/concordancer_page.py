"""
Page Concordancier : Analyse et visualisation des concordances.
@jcharlesDS (2026)
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QLineEdit, QTableWidget,
    QTableWidgetItem, QRadioButton, QButtonGroup, QHeaderView,
    QComboBox, QFileDialog, QMessageBox, QGroupBox, QDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from gui.widgets.base_page import BasePage, TEXT_PRIMARY, ACCENT
from gui.core.app_settings import load_app_settings, save_app_settings
from gui.core.closed_patterns import load_closed_patterns_from_last_analysis

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.concordancer import search_concordances, search_concordances_cqp_pattern, format_concordances_for_display


class DistributionDialog(QDialog):
    """Dialogue pour afficher le graphique de distribution."""
    
    def __init__(self, column_name: str, counts: dict, project_root: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Distribution par {column_name}")
        self._column_name = column_name
        self._counts = counts
        self._project_root = project_root
        
        # Ajuster la taille de la fenêtre en fonction du nombre d'éléments
        num_items = len(counts)
        if num_items > 15:
            self.setMinimumSize(1000, 700)
        else:
            self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Titre
        title = QLabel(f"Distribution des concordances par {column_name}")
        title.setFont(QFont("Helvetica Neue", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)
        
        # Canvas matplotlib
        if MATPLOTLIB_AVAILABLE:
            # Ajuster la taille de la figure en fonction du nombre d'éléments
            if num_items > 15:
                fig_height = max(12, num_items * 0.5)  # Plus d'espace par élément
                self._figure = Figure(figsize=(10, fig_height))
            else:
                self._figure = Figure(figsize=(10, 6))
            
            self._canvas = FigureCanvasQTAgg(self._figure)
            
            if num_items > 15:
                # Canvas avec sa vraie taille, dans un QScrollArea
                self._canvas.setMinimumHeight(int(fig_height * 80))
                
                # Créer un container pour le canvas
                canvas_container = QWidget()
                canvas_layout = QVBoxLayout(canvas_container)
                canvas_layout.setContentsMargins(0, 0, 0, 0)
                canvas_layout.addWidget(self._canvas)
                
                # Créer le QScrollArea
                scroll_area = QScrollArea()
                scroll_area.setWidget(canvas_container)
                scroll_area.setWidgetResizable(True)
                scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
                scroll_area.setMinimumHeight(500)
                scroll_area.setMaximumHeight(600)
                
                layout.addWidget(scroll_area)
            else:
                self._canvas.setMinimumHeight(450)
                layout.addWidget(self._canvas)
            
            self._plot_data()
        else:
            error_label = QLabel("matplotlib n'est pas disponible.")
            error_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-style: italic;")
            layout.addWidget(error_label)
        
        # Bouton d'enregistrement
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_save = QPushButton("Enregistrer le graphique")
        btn_save.setMinimumHeight(38)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #4a4a6a;
            }}
            QPushButton:pressed {{
                background-color: #2a2a4a;
            }}
        """)
        btn_save.clicked.connect(self._save_graph)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
    
    def _plot_data(self):
        """Génère le graphique de distribution avec adaptation dynamique."""
        labels = sorted(self._counts.keys())
        values = [self._counts[label] for label in labels]
        num_items = len(labels)
        
        ax = self._figure.add_subplot(111)
        
        # Utiliser un graphique horizontal si trop d'éléments
        if num_items > 15:
            ax.barh(labels, values, color='#3a3a5a')
            ax.set_ylabel(self._column_name, fontsize=12)
            ax.set_xlabel("Occurrences", fontsize=12)
            ax.set_title(f"Distribution par {self._column_name}", fontsize=14, fontweight='bold', pad=15)
            # Ajuster la taille des labels pour la lisibilité
            ax.tick_params(axis='y', labelsize=9 if num_items > 30 else 10)
        else:
            ax.bar(labels, values, color='#3a3a5a')
            ax.set_xlabel(self._column_name, fontsize=12)
            ax.set_ylabel("Occurrences", fontsize=12)
            ax.set_title(f"Distribution par {self._column_name}", fontsize=14, fontweight='bold', pad=15)
            # Rotation et alignement des labels pour éviter le chevauchement
            ax.tick_params(axis='x', rotation=45, labelsize=10)
            for label in ax.get_xticklabels():
                label.set_ha('right')
        
        self._figure.tight_layout()
        self._canvas.draw()
    
    def _save_graph(self):
        """Enregistre le graphique."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_path = self._project_root / "logs" / f"distribution_{self._column_name}_{timestamp}.png"
        
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le graphique",
            str(default_path),
            "PNG (*.png)",
        )
        if selected:
            self._figure.savefig(selected, dpi=150, bbox_inches='tight')
            QMessageBox.information(self, "Enregistrer", f"Graphique enregistré:\n{selected}")

class ConcordancerPage(BasePage):
    """Recherche un terme dans le corpus CWB et affiche les concordances."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = Path(__file__).resolve().parents[2]
        self._registry_path = self._guess_registry_path()
        self._metadata_headers = []
        self._metadata_map = {}
        self._raw_results = []
        self._displayed_results = []
        self._metadata_path_value = self._guess_metadata_path()
        self._closed_pattern_entries = []
        
        # Timer pour débouncer les filtres/tri (évite les appels répétés)
        self._filter_timer = QTimer()
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(150)  # 150ms de délai
        self._filter_timer.timeout.connect(self._apply_filters_sort_now)
        
        self._build_ui()
        self._load_metadata(show_message=False)

    def _closed_pattern_display_mode(self) -> str:
        if hasattr(self, "_display_mode_combo") and self._display_mode_combo is not None:
            data = self._display_mode_combo.currentData()
            if data:
                return str(data)
        settings = load_app_settings(self._project_root)
        return settings.get("closed_pattern_display_mode", "motif")

    def _closed_pattern_display_label(self, mode: str | None = None) -> str:
        mode = mode or self._closed_pattern_display_mode()
        return "Motifs" if mode == "motif" else "Mots correspondants"

    def _update_closed_pattern_display_hint(self) -> None:
        if not hasattr(self, "_display_mode_hint"):
            return
        label = self._closed_pattern_display_label()
        self._display_mode_hint.setText(
            f"Affichage utilisé pour les motifs enregistrés : {label}."
        )

    def _persist_closed_pattern_display_mode(self, mode: str) -> None:
        settings = load_app_settings(self._project_root)
        if settings.get("closed_pattern_display_mode") == mode:
            return
        settings["closed_pattern_display_mode"] = mode
        save_app_settings(self._project_root, settings)

    def _on_closed_pattern_display_mode_changed(self) -> None:
        mode = self._closed_pattern_display_mode()
        self._persist_closed_pattern_display_mode(mode)
        self._update_closed_pattern_display_hint()

        if self._search_mode.currentText() == "Motifs enregistrés" and self._pattern_list.currentItem() is not None:
            self._run_search()
    
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

        self._registry_status_label = QLabel()
        self._registry_status_label.setWordWrap(True)
        self._registry_status_label.setStyleSheet(
            "color: #4b5563; background-color: transparent; font-size: 12px;"
        )
        search_layout.addWidget(self._registry_status_label)
        self._refresh_registry_status()

        row0 = QHBoxLayout()
        row0.setSpacing(8)

        mode_label = QLabel("Mode :")
        mode_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        mode_label.setFont(QFont("Helvetica Neue", 11))
        row0.addWidget(mode_label)

        self._search_mode = QComboBox()
        self._search_mode.addItems(["Recherche libre", "Motifs enregistrés", "CQP"])
        self._search_mode.currentTextChanged.connect(self._on_search_mode_changed)
        self._search_mode.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #1f2937;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 10px;
                min-height: 28px;
            }
        """)
        row0.addWidget(self._search_mode, 1)
        row0.addStretch()
        search_layout.addLayout(row0)

        row0b = QHBoxLayout()
        row0b.setSpacing(8)

        display_label = QLabel("Affichage :")
        display_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        display_label.setFont(QFont("Helvetica Neue", 11))
        row0b.addWidget(display_label)

        self._display_mode_combo = QComboBox()
        self._display_mode_combo.addItem("Motifs", "motif")
        self._display_mode_combo.addItem("Mots correspondants", "words")
        current_mode = self._closed_pattern_display_mode()
        index = self._display_mode_combo.findData(current_mode)
        self._display_mode_combo.setCurrentIndex(index if index >= 0 else 0)
        self._display_mode_combo.currentIndexChanged.connect(self._on_closed_pattern_display_mode_changed)
        self._display_mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #1f2937;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 10px;
                min-height: 28px;
            }
        """)
        row0b.addWidget(self._display_mode_combo)
        row0b.addStretch()
        search_layout.addLayout(row0b)

        self._display_mode_hint = QLabel()
        self._display_mode_hint.setWordWrap(True)
        self._display_mode_hint.setStyleSheet(
            "color: #6b7280; background-color: transparent; font-size: 12px; font-style: italic;"
        )
        search_layout.addWidget(self._display_mode_hint)
        self._update_closed_pattern_display_hint()

        # Ligne 1: Champ de recherche + Bouton
        row1 = QHBoxLayout()
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
        search_layout.addLayout(row1)

        self._pattern_panel = QWidget()
        pattern_layout = QVBoxLayout(self._pattern_panel)
        pattern_layout.setContentsMargins(0, 0, 0, 0)
        pattern_layout.setSpacing(8)

        self._pattern_filter_input = QLineEdit()
        self._pattern_filter_input.setPlaceholderText("Filtrer les motifs...")
        self._pattern_filter_input.textChanged.connect(self._filter_closed_patterns)
        self._pattern_filter_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #1f2937;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 10px;
            }
        """)
        pattern_layout.addWidget(self._pattern_filter_input)

        pattern_hint = QLabel("Double-cliquez sur un motif pour afficher ses concordances en contexte.")
        pattern_hint.setWordWrap(True)
        pattern_hint.setStyleSheet("color: #6b7280; background-color: transparent; font-style: italic;")
        pattern_layout.addWidget(pattern_hint)

        self._pattern_list = QListWidget()
        self._pattern_list.setMinimumHeight(140)
        self._pattern_list.itemDoubleClicked.connect(lambda _: self._run_search())
        self._pattern_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px;
            }
            QListWidget::item:selected {
                background-color: #dbeafe;
                color: #1e3a8a;
            }
        """)
        pattern_layout.addWidget(self._pattern_list)

        self._pattern_info_label = QLabel("Aucun motif chargé.")
        self._pattern_info_label.setWordWrap(True)
        self._pattern_info_label.setStyleSheet("color: #4b5563; background-color: transparent; font-size: 12px;")
        pattern_layout.addWidget(self._pattern_info_label)

        search_layout.addWidget(self._pattern_panel)
        
        # Ligne 2: Boutons radio pour le type de recherche
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        
        type_label = QLabel("Type de recherche:")
        type_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        type_label.setFont(QFont("Helvetica Neue", 11))
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
        search_layout.addLayout(row2)

        row4 = QHBoxLayout()
        row4.setSpacing(8)

        filter_label = QLabel("Filtrer par :")
        filter_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        filter_label.setFont(QFont("Helvetica Neue", 11))
        row4.addWidget(filter_label)

        self._filter_column = QComboBox()
        self._filter_column.addItem("(Aucun filtre)")
        self._filter_column.currentTextChanged.connect(self._on_filter_column_changed)
        self._filter_column.setStyleSheet(f"""
            QComboBox {{
                background-color: #ffffff;
                color: {TEXT_PRIMARY};
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
            }}
            QComboBox:hover {{
                border: 1px solid {ACCENT};
            }}
        """)
        row4.addWidget(self._filter_column, 2)

        self._filter_value = QComboBox()
        self._filter_value.addItem("(Toutes les valeurs)")
        self._filter_value.currentTextChanged.connect(lambda _: self._schedule_filter_sort())
        self._filter_value.setStyleSheet(f"""
            QComboBox {{
                background-color: #ffffff;
                color: {TEXT_PRIMARY};
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
            }}
            QComboBox:hover {{
                border: 1px solid {ACCENT};
            }}
        """)
        row4.addWidget(self._filter_value, 2)

        row4.addStretch()
        search_layout.addLayout(row4)

        row5 = QHBoxLayout()
        row5.setSpacing(8)

        order_label = QLabel("Ordre :")
        order_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        order_label.setFont(QFont("Helvetica Neue", 11))
        row5.addWidget(order_label)

        self._sort_order = QComboBox()
        self._sort_order.addItems(["A → Z", "Z → A"])
        self._sort_order.currentTextChanged.connect(lambda _: self._schedule_filter_sort())
        self._sort_order.setStyleSheet(f"""
            QComboBox {{
                background-color: #ffffff;
                color: {TEXT_PRIMARY};
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
            }}
            QComboBox:hover {{
                border: 1px solid {ACCENT};
            }}
        """)
        row5.addWidget(self._sort_order, 1)

        row5.addStretch()

        self._btn_export_csv = QPushButton("Exporter CSV")
        self._btn_export_csv.setMinimumHeight(34)
        self._btn_export_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_export_csv.setStyleSheet(f"""
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
        self._btn_export_csv.clicked.connect(self._export_csv)
        row5.addWidget(self._btn_export_csv)

        self._btn_plot_distribution = QPushButton("Distribution")
        self._btn_plot_distribution.setMinimumHeight(34)
        self._btn_plot_distribution.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_plot_distribution.setStyleSheet(f"""
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
        self._btn_plot_distribution.clicked.connect(self._plot_distribution)
        row5.addWidget(self._btn_plot_distribution)

        search_layout.addLayout(row5)
        self._pattern_panel.hide()
        
        layout.addWidget(search_group)
        
        # Résultats
        results_group = self.make_group("Concordances")
        results_layout = QVBoxLayout(results_group)
        
        self._stats_label = QLabel("Aucune recherche lancée.")
        self._stats_label.setFont(QFont("Helvetica Neue", 11))
        self._stats_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        results_layout.addWidget(self._stats_label)
        
        self._results_table = QTableWidget()
        self._results_table.setMinimumHeight(500)
        self._results_table.setColumnCount(4)
        self._results_table.setHorizontalHeaderLabels(["Contexte gauche", "Terme", "Contexte droit", "Source"])
        
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

    def _on_search_mode_changed(self, mode_label: str):
        is_pattern_mode = mode_label == "Motifs enregistrés"
        is_cqp_mode = mode_label == "CQP"
        self._query_input.setVisible(not is_pattern_mode)
        self._radio_word.setVisible(not is_pattern_mode and not is_cqp_mode)
        self._radio_lemma.setVisible(not is_pattern_mode and not is_cqp_mode)
        self._radio_pos.setVisible(not is_pattern_mode and not is_cqp_mode)
        self._pattern_panel.setVisible(is_pattern_mode)
        self._search_btn.setVisible(not is_pattern_mode)
        if is_cqp_mode:
            self._query_input.setPlaceholderText('Entrez une requête CQP, ex. [lemma="faire"] []{0,3} [pos="NOUN"]')
        else:
            self._query_input.setPlaceholderText("Entrez un terme à rechercher...")
        if is_pattern_mode and not self._closed_pattern_entries:
            self._load_closed_patterns()

    def _load_closed_patterns(self):
        self._closed_pattern_entries = load_closed_patterns_from_last_analysis(self._project_root)
        self._populate_closed_patterns(self._closed_pattern_entries)
        if self._closed_pattern_entries:
            source_file = self._closed_pattern_entries[0].get("source_file", "")
            self._pattern_info_label.setText(
                f"{len(self._closed_pattern_entries)} motif(s) chargé(s) depuis {source_file}."
            )
        else:
            self._pattern_info_label.setText(
                "Aucun motif exploitable n'a été trouvé pour la dernière analyse."
            )

    def _populate_closed_patterns(self, entries):
        self._pattern_list.clear()
        for entry in entries:
            label = entry.get("display", "")
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self._pattern_list.addItem(item)
        if self._pattern_list.count() > 0:
            self._pattern_list.setCurrentRow(0)

    def _filter_closed_patterns(self, text: str):
        needle = text.strip().lower()
        if not needle:
            self._populate_closed_patterns(self._closed_pattern_entries)
            return
        filtered = [
            entry for entry in self._closed_pattern_entries
            if needle in entry.get("display", "").lower()
        ]
        self._populate_closed_patterns(filtered)

    def _guess_metadata_path(self) -> str:
        """Localise le metadata.tsv de la dernière analyse.

        Stratégie (pour tous les utilisateurs, chemins relatifs ou absolus) :
        1. Lire last_analysis.json → analysis_info.json → config.path_metadata
           et résoudre le chemin par rapport à la racine du projet.
        2. Si introuvable, utiliser config.metadata_corpus_dir (même résolution)
           et chercher metadata.tsv dedans.
        3. Retourne "" si rien n'est trouvé.
        """
        last_analysis = self._project_root / "logs" / "last_analysis.json"
        if not last_analysis.exists():
            return ""
        try:
            with open(last_analysis, "r", encoding="utf-8") as f:
                data = json.load(f)
            analysis_group_name = data.get("analysis_group_name", data.get("corpus_name", ""))
            config_id = data.get("config_id", "")
            if not (analysis_group_name and config_id):
                return ""
            info_path = (
                self._project_root / "Data" / "analyses"
                / analysis_group_name / config_id / "analysis_info.json"
            )
            if not info_path.exists():
                return ""
            with open(info_path, "r", encoding="utf-8") as f:
                info = json.load(f)
            config = info.get("config", {})

            def _resolve(p: str) -> Path:
                """Résout un chemin relatif par rapport à la racine du projet."""
                path = Path(p)
                return path if path.is_absolute() else self._project_root / path

            # 1. Chemin direct stocké dans path_metadata
            stored_path = config.get("path_metadata", "").strip()
            if stored_path:
                resolved = _resolve(stored_path)
                if resolved.exists():
                    return str(resolved)

            # 2. Fallback : dériver depuis metadata_corpus_dir
            corpus_dir = config.get("metadata_corpus_dir", "").strip()
            if corpus_dir:
                resolved_dir = _resolve(corpus_dir)
                candidate = resolved_dir / "metadata.tsv"
                if candidate.exists():
                    return str(candidate)

        except Exception:
            pass
        return ""

    def _guess_registry_path(self) -> str:
        """Localise le registre CWB de la dernière analyse.
        
        Stratégie :
        1. Lire last_analysis.json pour recuperer analysis_group_name et config_id
        2. Construire le chemin : Data/analyses/{analysis_group_name}/{config_id}/cwb-corpus/registry
        3. Si le dossier existe, l'utiliser
        4. Sinon, retourner une chaine vide
        """
        last_analysis = self._project_root / "logs" / "last_analysis.json"
        if not last_analysis.exists():
            return ""
        
        try:
            with open(last_analysis, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            analysis_group_name = data.get("analysis_group_name", data.get("corpus_name", ""))
            config_id = data.get("config_id", "")
            
            if not (analysis_group_name and config_id):
                return ""
            
            # Construire le chemin vers le registre CWB de cette analyse
            registry_path = (
                self._project_root / "Data" / "analyses"
                / analysis_group_name / config_id / "cwb-corpus" / "registry"
            )
            
            # Vérifier si le registre existe
            if registry_path.exists():
                return str(registry_path)
            return ""
        
        except Exception:
            return ""

    def _refresh_registry_status(self):
        """Met à jour le libellé d'information sur le registry CWB utilisé."""
        registry_dir = Path(self._registry_path)
        registry_file = registry_dir / "merged"
        is_ready = registry_dir.exists() and registry_file.exists()
        state_text = "Disponible" if is_ready else "Introuvable"
        state_color = "#166534" if is_ready else "#b91c1c"
        self._registry_status_label.setText(
            f"Registry CWB utilisé : <b style='color:{state_color};'>{state_text}</b><br>"
            f"<span style='color:#6b7280;'>{registry_dir}</span>"
        )

    def refresh_from_latest_analysis(self, _results: dict | None = None):
        """Recharge les chemins, motifs et métadonnées de la dernière analyse."""
        self._registry_path = self._guess_registry_path()
        self._metadata_path_value = self._guess_metadata_path()
        self._refresh_registry_status()
        self._load_metadata(show_message=False)

        self._closed_pattern_entries = []
        self._pattern_list.clear()
        self._pattern_info_label.setText("Rafraîchissement des motifs de la dernière analyse...")

        if self._search_mode.currentText() == "Motifs enregistrés":
            self._load_closed_patterns()
        else:
            self._pattern_info_label.setText(
                "Nouvelle analyse détectée. Les motifs seront rechargés en mode 'Motifs enregistrés'."
            )

        self._raw_results = []
        self._displayed_results = []
        self._results_table.setRowCount(0)
        self._refresh_filter_values()
        self._stats_label.setText(
            "Concordancier mis à jour avec les données de la dernière analyse."
        )

    def _load_metadata(self, show_message: bool):
        metadata_path = self._metadata_path_value.strip()
        self._metadata_headers = []
        self._metadata_map = {}

        if not metadata_path:
            self._filter_column.clear()
            self._filter_column.addItem("(Aucun filtre)")
            self._filter_value.clear()
            self._filter_value.addItem("(Toutes les valeurs)")
            return

        path = Path(metadata_path)

        if not path.exists():
            self._filter_column.clear()
            self._filter_column.addItem("(Aucun filtre)")
            self._filter_value.clear()
            self._filter_value.addItem("(Toutes les valeurs)")
            if show_message:
                QMessageBox.warning(self, "Metadata introuvable", f"Fichier introuvable:\n{path}")
            return

        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                self._metadata_headers = list(reader.fieldnames or [])
                for row in reader:
                    row_id = (row.get("id") or "").strip()
                    if not row_id:
                        continue
                    self._metadata_map[row_id] = row
                    self._metadata_map[Path(row_id).stem] = row

            available_filter_cols = [h for h in self._metadata_headers if h != "id"]
            self._filter_column.blockSignals(True)
            current = self._filter_column.currentText() if self._filter_column.count() else "(Aucun filtre)"
            self._filter_column.clear()
            self._filter_column.addItem("(Aucun filtre)")
            self._filter_column.addItems(available_filter_cols)
            if current and self._filter_column.findText(current) >= 0:
                self._filter_column.setCurrentText(current)
            self._filter_column.blockSignals(False)
            self._refresh_filter_values()

            if show_message:
                QMessageBox.information(
                    self,
                    "Metadata chargé",
                    f"{len(self._metadata_map)} clés metadata chargées depuis:\n{path}"
                )
        except Exception as exc:
            QMessageBox.critical(self, "Erreur metadata", f"Impossible de charger metadata.tsv:\n{exc}")

    def _get_metadata_row(self, source: str) -> dict:
        if source in self._metadata_map:
            return self._metadata_map[source]
        source_stem = Path(source).stem
        return self._metadata_map.get(source_stem, {})

    def _refresh_filter_values(self):
        selected_column = self._filter_column.currentText().strip()
        self._filter_value.blockSignals(True)
        self._filter_value.clear()
        self._filter_value.addItem("(Toutes les valeurs)")

        if selected_column and selected_column != "(Aucun filtre)":
            values = sorted({
                str(row.get("metadata", {}).get(selected_column, "")).strip()
                for row in self._raw_results
                if str(row.get("metadata", {}).get(selected_column, "")).strip()
            })
            self._filter_value.addItems(values)

        self._filter_value.blockSignals(False)

    def _on_filter_column_changed(self, _value: str):
        self._refresh_filter_values()
        self._schedule_filter_sort()  # Utiliser le debouncing
    
    def _schedule_filter_sort(self):
        """Redémarre le timer de debouncing pour éviter trop d'appels consécutifs."""
        self._filter_timer.start()  # Redémarre le timer à chaque appel
    
    def _apply_filters_sort(self):
        """Applique immédiatement le filtre et tri (pour compatibilité)."""
        self._filter_timer.stop()  # Annule le timer en attente
        self._apply_filters_sort_now()

    def _apply_filters_sort_now(self):
        """Applique le filtre et tri alphabétique intelligent.
        
        Tri par :
        - La colonne de filtre sélectionnée si elle existe
        - Sinon par la source (ID du texte)
        
        Ordre alphabétique (A→Z) ou inverse (Z→A).
        """
        filtered = list(self._raw_results)
        selected_column = self._filter_column.currentText().strip()
        selected_value = self._filter_value.currentText().strip()

        # Filtrage
        if selected_column and selected_column != "(Aucun filtre)" and selected_value and selected_value != "(Toutes les valeurs)":
            filtered = [
                row for row in filtered
                if str(row.get("metadata", {}).get(selected_column, "")).strip() == selected_value
            ]

        # Tri alphabétique intelligent
        reverse = self._sort_order.currentText().strip() == "Z → A"
        
        if selected_column and selected_column != "(Aucun filtre)":
            # Tri par la colonne de métadonnées sélectionnée
            filtered.sort(
                key=lambda row: str(row.get("metadata", {}).get(selected_column, "")).strip().lower(),
                reverse=reverse,
            )
        else:
            # Tri par défaut : source (ID du texte)
            filtered.sort(
                key=lambda row: row.get("source", "").lower(),
                reverse=reverse,
            )

        self._displayed_results = filtered
        self._render_results_table(filtered)

    def _render_results_table(self, rows):
        """Affiche les résultats dans le tableau avec optimisations pour grandes listes."""
        # Limite de résultats affichés pour éviter les freezes
        MAX_DISPLAY = 10000
        total_rows = len(rows)
        truncated = total_rows > MAX_DISPLAY
        
        if truncated:
            display_rows = rows[:MAX_DISPLAY]
        else:
            display_rows = rows
        
        metadata_cols = [h for h in self._metadata_headers if h != "id"]
        headers = ["Contexte gauche", "Terme", "Contexte droit", "Source"] + metadata_cols
        
        # Optimisations pour éviter les freezes avec beaucoup de données
        self._results_table.setSortingEnabled(False)  # Désactiver le tri automatique
        self._results_table.setUpdatesEnabled(False)  # Désactiver les repaints pendant le remplissage
        
        try:
            self._results_table.setColumnCount(len(headers))
            self._results_table.setHorizontalHeaderLabels(headers)
            self._results_table.setRowCount(len(display_rows))

            for row_index, row in enumerate(display_rows):
                item_left = QTableWidgetItem(row.get("left", ""))
                item_left.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._results_table.setItem(row_index, 0, item_left)

                item_keyword = QTableWidgetItem(row.get("keyword", ""))
                item_keyword.setFont(QFont("Helvetica Neue", 11, QFont.Weight.Bold))
                item_keyword.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._results_table.setItem(row_index, 1, item_keyword)

                item_right = QTableWidgetItem(row.get("right", ""))
                item_right.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self._results_table.setItem(row_index, 2, item_right)

                item_source = QTableWidgetItem(row.get("source", ""))
                item_source.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._results_table.setItem(row_index, 3, item_source)

                for offset, col in enumerate(metadata_cols, start=4):
                    item_meta = QTableWidgetItem(str(row.get("metadata", {}).get(col, "")))
                    item_meta.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._results_table.setItem(row_index, offset, item_meta)
        finally:
            # Réactiver les updates et le tri
            self._results_table.setUpdatesEnabled(True)
            self._results_table.setSortingEnabled(False)  # Garder désactivé car on gère le tri manuellement

        # Message avec avertissement si tronqué
        if truncated:
            self._stats_label.setText(
                f"⚠️ {len(display_rows)} résultats affichés sur {total_rows} filtrés "
                f"({len(self._raw_results)} occurrences totales). "
                f"Affinez vos filtres pour voir plus de résultats."
            )
        else:
            self._stats_label.setText(
                f"{len(display_rows)} résultat(s) affiché(s) / {len(self._raw_results)} occurrence(s) trouvée(s)."
            )
        
    def _run_search(self):
        self._registry_path = self._guess_registry_path()
        self._refresh_registry_status()

        registry_dir = Path(self._registry_path) if self._registry_path else None
        registry_file = registry_dir / "merged" if registry_dir else None
        if not registry_dir or not registry_file or not registry_file.exists():
            self._stats_label.setText(
                "Aucun registry CWB valide n'est disponible. Lancez d'abord une analyse terminée."
            )
            self._results_table.setRowCount(0)
            return

        latest_metadata = self._guess_metadata_path()
        if latest_metadata != self._metadata_path_value:
            self._metadata_path_value = latest_metadata
            self._load_metadata(show_message=False)

        current_mode = self._search_mode.currentText()
        is_pattern_mode = current_mode == "Motifs enregistrés"
        is_cqp_mode = current_mode == "CQP"
        query = self._query_input.text().strip()
        search_type = "word"
        selected_pattern = None

        if is_pattern_mode:
            current_item = self._pattern_list.currentItem()
            if current_item is None:
                self._stats_label.setText("Veuillez d'abord sélectionner un motif.")
                self._results_table.setRowCount(0)
                return
            selected_pattern = current_item.data(Qt.ItemDataRole.UserRole) or {}
            display_label = selected_pattern.get("display", "motif")
            self._stats_label.setText(f"Recherche en cours du motif '{display_label}'...")
        else:
            if not query:
                self._stats_label.setText("Veuillez entrer une recherche.")
                self._results_table.setRowCount(0)
                return

            if is_cqp_mode:
                self._stats_label.setText("Recherche CQP en cours...")
            else:
                # Déterminer le type de recherche
                if self._radio_word.isChecked():
                    search_type = "word"
                elif self._radio_lemma.isChecked():
                    search_type = "lemma"
                else:
                    search_type = "pos"

                # Afficher un message de chargement
                self._stats_label.setText(f"Recherche en cours de '{query}' ({search_type})...")

        self._results_table.setRowCount(0)
        self._search_btn.setEnabled(False)
        
        try:
            if is_pattern_mode:
                concordances = search_concordances_cqp_pattern(
                    cqp_pattern=selected_pattern.get("cqp_pattern", ""),
                    context_words=10,
                    registry_path=self._registry_path
                )
            elif is_cqp_mode:
                concordances = search_concordances_cqp_pattern(
                    cqp_pattern=query,
                    context_words=10,
                    registry_path=self._registry_path
                )
            else:
                # Lancer la recherche CQP
                concordances = search_concordances(
                    query=query,
                    search_type=search_type,
                    context_words=10,
                    registry_path=self._registry_path
                )
            
            if not concordances:
                if is_pattern_mode:
                    self._stats_label.setText("Aucune occurrence du motif sélectionné n'a été trouvée dans le corpus.")
                elif is_cqp_mode:
                    self._stats_label.setText("Aucune occurrence trouvée pour cette requête CQP.")
                else:
                    self._stats_label.setText(
                        f"Aucune occurrence de '{query}' trouvée dans le corpus."
                    )
                return
            
            # Formater et afficher les résultats
            formatted = format_concordances_for_display(concordances)
            self._raw_results = []
            show_mode = self._closed_pattern_display_mode()
            for left, keyword, right, source in formatted:
                if is_pattern_mode and show_mode == "motif":
                    keyword_value = selected_pattern.get("display", keyword)
                else:
                    keyword_value = keyword
                self._raw_results.append(
                    {
                        "left": left,
                        "keyword": keyword_value,
                        "right": right,
                        "source": source,
                        "metadata": self._get_metadata_row(source),
                    }
                )

            self._refresh_filter_values()
            self._apply_filters_sort()
            
        except Exception as e:
            if is_cqp_mode:
                self._stats_label.setText(f"Erreur dans la requête CQP: {str(e)}")
            else:
                self._stats_label.setText(f"Erreur lors de la recherche: {str(e)}")
        
        finally:
            self._search_btn.setEnabled(True)

    def _export_csv(self):
        if not self._displayed_results:
            QMessageBox.information(self, "Export CSV", "Aucun résultat à exporter.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_path = self._project_root / "logs" / f"concordances_{timestamp}.csv"
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter les concordances",
            str(default_path),
            "CSV (*.csv)",
        )
        if not selected:
            return

        metadata_cols = [h for h in self._metadata_headers if h != "id"]
        headers = ["left_context", "keyword", "right_context", "source"] + metadata_cols
        with open(selected, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            for row in self._displayed_results:
                out = {
                    "left_context": row.get("left", ""),
                    "keyword": row.get("keyword", ""),
                    "right_context": row.get("right", ""),
                    "source": row.get("source", ""),
                }
                for col in metadata_cols:
                    out[col] = row.get("metadata", {}).get(col, "")
                writer.writerow(out)

        QMessageBox.information(self, "Export CSV", f"Export terminé:\n{selected}")

    def _plot_distribution(self):
        """Ouvre une fenêtre avec le graphique de distribution."""
        if not self._displayed_results:
            QMessageBox.information(self, "Distribution", "Aucun résultat à visualiser.")
            return

        selected_column = self._filter_column.currentText().strip()
        if not selected_column or selected_column == "(Aucun filtre)":
            QMessageBox.information(
                self,
                "Distribution",
                "Sélectionnez d'abord une colonne metadata dans le filtre pour générer la distribution."
            )
            return

        if not MATPLOTLIB_AVAILABLE:
            QMessageBox.warning(self, "Distribution", "matplotlib est indisponible dans l'environnement courant.")
            return

        # Calculer les occurrences
        counts = {}
        for row in self._displayed_results:
            value = str(row.get("metadata", {}).get(selected_column, "")).strip() or "(vide)"
            counts[value] = counts.get(value, 0) + 1

        # Vérifier qu'il y a au moins 2 valeurs uniques
        if len(counts) < 2:
            QMessageBox.information(
                self,
                "Distribution",
                "Le graphique nécessite au moins 2 valeurs différentes.\n"
                "Actuellement, tous les résultats affichés ont la même valeur pour cette colonne."
            )
            return

        # Ouvrir le dialogue
        dialog = DistributionDialog(selected_column, counts, self._project_root, self)
        dialog.exec()
