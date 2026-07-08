"""
Page Résultats : Aperçu des sorties générés par l'analyse.
@jcharlesDS (2026)
"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import Qt, QUrl

from gui.widgets.base_page import BasePage, TEXT_PRIMARY, ACCENT


class ResultsPage(BasePage):
    """Page d'affichage des résultats de l'analyse."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = Path(__file__).resolve().parents[2]
        
        # Charger les chemins de la dernière analyse ou utiliser les anciens par défaut
        self._load_last_analysis_paths()
        
        self._build_ui()
        self._refresh_results()
    
    def _load_last_analysis_paths(self):
        """Charge les chemins de la dernière analyse depuis last_analysis.json."""
        last_analysis_file = self._project_root / "logs" / "last_analysis.json"
        
        if last_analysis_file.exists():
            try:
                with open(last_analysis_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    self._results_dirs = [
                        Path(info["patterns_results"]),
                        Path(info["clustering_results"]),
                        Path(info["logs"]),
                    ]
                    self._last_analysis_info = info
                    return
            except Exception:
                pass
        
        # Fallback : anciens chemins par défaut (legacy)
        self._results_dirs = [
            self._project_root / "Patterns_results",
            self._project_root / "Clustering_results",
            self._project_root / "logs",
        ]
        self._last_analysis_info = None
    
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
            "Résultats de l'analyse",
            "Explorez les sorties générées par le processus d'analyse."
        ))
        
        # Actions rapides
        actions_group = self.make_group("Actions rapides")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.setSpacing(10)
        
        self._btn_refresh = self._action_btn("Actualiser")
        self._btn_refresh.clicked.connect(self._refresh_results)
        actions_layout.addWidget(self._btn_refresh)
        
        self._btn_open_patterns = self._action_btn("Ouvrir Patterns_results")
        self._btn_open_patterns.clicked.connect(self._open_patterns)
        actions_layout.addWidget(self._btn_open_patterns)
        
        self._btn_open_clustering = self._action_btn("Ouvrir Clustering_results")
        self._btn_open_clustering.clicked.connect(self._open_clustering)
        actions_layout.addWidget(self._btn_open_clustering)
        
        self._btn_open_logs = self._action_btn("Ouvrir logs")
        self._btn_open_logs.clicked.connect(self._open_logs)
        actions_layout.addWidget(self._btn_open_logs)
        
        layout.addWidget(actions_group)
        
        # Résumé des résultats
        summary_group = self.make_group("Résumé")
        summary_layout = QVBoxLayout(summary_group)
        
        self._summary_label = QLabel("Chargement...")
        self._summary_label.setFont(QFont("Segoe UI", 10))
        self._summary_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        self._summary_label.setWordWrap(True)
        summary_layout.addWidget(self._summary_label)
        
        layout.addWidget(summary_group)
        
        # Liste des fichiers détectés
        files_group = self.make_group("Fichiers générés")
        files_layout = QVBoxLayout(files_group)
        
        self._files_list = QListWidget()
        self._files_list.setMinimumHeight(400)
        self._files_list.setStyleSheet(f"""
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
        files_layout.addWidget(self._files_list)
        self._files_list.itemDoubleClicked.connect(self._open_selected_file)
        
        layout.addWidget(files_group)
        
        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        
    
    # --- Actions --- 
    
    def _action_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumHeight(38)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 10))
        btn.setStyleSheet(f"""
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
        return btn
    
    def _open_dir(self, path: Path):
        if path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
    
    def _open_selected_file(self, item: QListWidgetItem):
        """Ouvre le fichier sélectionné (double-clic) si c'est une vraie entrée."""
        text = item.text().strip()

        # Ignore les lignes d'entête et d'information
        if text.startswith("[") or text.startswith("...") or text.startswith("Aucun fichier"):
            return

        file_path = self._project_root / text
        if file_path.exists() and file_path.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))
    
    def _open_patterns(self):
        """Ouvre le dossier Patterns_results de la dernière analyse."""
        if len(self._results_dirs) > 0:
            self._open_dir(self._results_dirs[0])
    
    def _open_clustering(self):
        """Ouvre le dossier Clustering_results de la dernière analyse."""
        if len(self._results_dirs) > 1:
            self._open_dir(self._results_dirs[1])
    
    def _open_logs(self):
        """Ouvre le dossier logs de la dernière analyse."""
        if len(self._results_dirs) > 2:
            self._open_dir(self._results_dirs[2])
    
    def _refresh_results(self):
        """Actualise la liste des fichiers de la dernière analyse."""
        # Recharger les chemins au cas où une nouvelle analyse serait terminée
        self._load_last_analysis_paths()
        
        self._files_list.clear()
        
        existing_dirs = [p for p in self._results_dirs if p.exists()]
        total_files = 0
        
        for d in existing_dirs:
            files = [f for f in d.rglob("*") if f.is_file()]
            total_files += len(files)
            
            if not files:
                continue
            
            header = QListWidgetItem(f"[{d.name}]")
            header.setFlags(Qt.ItemFlag.ItemIsEnabled)
            header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self._files_list.addItem(header)
            
            for f in files[:50]:
                rel = f.relative_to(self._project_root)
                self._files_list.addItem(str(rel))
                
            if len(files) > 50:
                self._files_list.addItem(f"... ({len(files) - 50} fichiers supplémentaires)")
                
        self._summary_label.setText(
            f"<b>Dossiers détectés :</b> {len(existing_dirs)} / {len(self._results_dirs)}<br>"
            f"<b>Fichiers trouvés :</b> {total_files}"
        )
        
        if self._files_list.count() == 0:
            self._files_list.addItem("Aucun fichier trouvé.")
