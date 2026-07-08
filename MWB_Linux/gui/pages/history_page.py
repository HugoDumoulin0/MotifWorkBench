"""
Page Historique: Suivi des analyses précédentes et de leurs résultats.
@jcharlesDS (2026)
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtGui import QFont, QBrush, QColor
from PyQt6.QtCore import Qt

from gui.widgets.base_page import BasePage, TEXT_PRIMARY, ACCENT
from gui.core.run_history import load_run_history, clear_run_history

class HistoryPage(BasePage):
    """
    Affiche un historique simple basé sur les fichiers générés (logs/résultats),
    triés par date de modification.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._refresh_history()
    
    def _format_duration(self, seconds: float) -> str:
        """Formate la durée en format lisible (heures/minutes/secondes)."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}min {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}min"
        
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
            "Historique des analyses",
            "Consultez les analyses précédentes et leurs résultats."
        ))
        
        # Actions
        actions_group = self.make_group("Actions")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.setSpacing(10)
        
        self._refresh_btn = QPushButton("Actualiser")
        self._refresh_btn.setMinimumHeight(38)
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._refresh_history)
        self._refresh_btn.setStyleSheet(f"""
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
        actions_layout.addWidget(self._refresh_btn)

        self._clear_btn = QPushButton("Supprimer l'historique")
        self._clear_btn.setMinimumHeight(38)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear_history)
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
            QPushButton:pressed {
                background-color: #ac2925;
            }
        """)
        actions_layout.addWidget(self._clear_btn)
        actions_layout.addStretch()
        
        layout.addWidget(actions_group)
        
        # Résumé
        summary_group = self.make_group("Résumé")
        summary_layout = QVBoxLayout(summary_group)
        
        self._summary_label = QLabel("Chargement...")
        self._summary_label.setFont(QFont("Segoe UI", 10))
        self._summary_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; background-color: transparent;"
        )
        summary_layout.addWidget(self._summary_label)
        
        layout.addWidget(summary_group)
        
        # Historique détaillé
        history_group = self.make_group("Dernières activités")
        history_layout = QVBoxLayout(history_group)
        
        self._history_list = QListWidget()
        self._history_list.setMinimumHeight(400)
        self._history_list.setStyleSheet(f"""
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
        history_layout.addWidget(self._history_list)
        
        layout.addWidget(history_group)
        layout.addStretch()
        
        scroll.setWidget(content)
        outer.addWidget(scroll)
    
    def _status_colors(self, status: str) -> tuple[str, str]:
        status = (status or "").lower()
        if status == "success":
            return "#166534", "#dcfce7"
        if status == "error":
            return "#991b1b", "#fee2e2"
        if status == "stopped":
            return "#92400e", "#fef3c7"
        return "#1f2937", "#e5e7eb"
        
        
    def _refresh_history(self):
        self._history_list.clear()

        history = load_run_history()

        self._summary_label.setText(
            f"<b>Exécutions enregistrées:</b> {len(history)}"
        )

        if not history:
            self._history_list.addItem(QListWidgetItem("Aucune exécution enregistrée pour le moment."))
            return

        for run in history[:120]:
            ts = run.get("timestamp", "?")
            status = run.get("status", "?")
            duration = run.get("duration_seconds", 0.0)
            lang = run.get("language", "")
            gpu = "GPU" if run.get("use_gpu", False) else "CPU"
            threads = run.get("threads", "")
            minsup = run.get("minsup", [])

            line = (
                f"{ts} | {status.upper()} | {self._format_duration(duration)} | "
                f"{lang} | {gpu} | threads={threads} | minsup={minsup}"
            )

            item = QListWidgetItem(line)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)

            fg, bg = self._status_colors(status)
            item.setForeground(QBrush(QColor(fg)))
            item.setBackground(QBrush(QColor(bg)))

            self._history_list.addItem(item)

            details = run.get("details", "")
            if details:
                sub = QListWidgetItem(f"    Détails: {details}")
                sub.setFlags(Qt.ItemFlag.ItemIsEnabled)
                sub.setForeground(QBrush(QColor("#6b7280")))
                font = QFont("Segoe UI", 9)
                sub.setFont(font)
                self._history_list.addItem(sub)

    def _clear_history(self):
        """Supprime l'historique après confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Voulez-vous vraiment supprimer tout l'historique des analyses ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            clear_run_history()
            self._refresh_history()
            QMessageBox.information(self, "Succès", "L'historique a été supprimé.")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de supprimer l'historique : {e}")
