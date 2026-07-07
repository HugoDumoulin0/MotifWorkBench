"""
Page d'accueil de l'application
Résumé du projet et accès rapide aux fonctionnalités principales.
@jcharlesDS (2026)
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal

from gui.widgets.base_page import BasePage, TEXT_PRIMARY, ACCENT
from gui.core.gpu_detect import detect_gpu
from gui.config.settings import list_profiles

class HomePage(BasePage):
    """
    Page d'accueil de l'application.
    Statut du projet, GPU, accès rapides...
    """
    
    # Signaux pour demander une navigation vers une autre page
    navigate_to = pyqtSignal(str)  # Nom de la page cible
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._refresh_status()
        
    # Construction
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
            "Bienvenue sur MotifWorkBench",
            "Extraction et analyse de motifs séquentiels."
        ))

        # Statut du projet + Accès rapide
        row = QHBoxLayout()
        row.setSpacing(16)
        
        self._status_group = self.make_group("Statut du projet")
        self._status_layout = QVBoxLayout()
        self._status_layout.setSpacing(8)
        self._status_group.setLayout(self._status_layout)
        row.addWidget(self._status_group, stretch=3)
        
        quick = self.make_group("Accès rapide")
        quick_layout = QVBoxLayout(quick)
        quick_layout.setSpacing(8)
        for label, target in [
            ("Configuration", "Réglages"),
            ("Lancer l'analyse", "Analyse"),
            ("Historique", "Historique"),
            ("Concordancier", "Concordancier"),
        ]:
            btn = self._action_btn(label)
            btn.clicked.connect(lambda _, t=target: self.navigate_to.emit(t))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        row.addWidget(quick, stretch=2)
        
        layout.addLayout(row)
        
        # Description
        desc_group = self.make_group("À propos")
        desc_layout = QVBoxLayout(desc_group)
        desc_lbl = QLabel(
            "MotifWorkBench est un outil d'analyse de corpus qui permet d'extraire "
            "des motifs séquentiels fréquents, de mettre en évidence leur spécificité, "
            "les comparer selon différents critères et de visualiser les résultats "
            "via une interface Shiny interactive.\n\n"
            "Commencez par vérifier votre configuration, puis lancez l'analyse depuis "
            "la page dédiée."
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        desc_lbl.setFont(QFont("Segoe UI", 10))
        desc_layout.addWidget(desc_lbl)
        layout.addWidget(desc_group)
        
        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)
    
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
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: #4a4a6a;
            }}
            QPushButton:pressed {{
                background-color: #2a2a4a;
            }}
        """)
        return btn
    
    # Statut du projet
    
    def _refresh_status(self):
        """Met à jour les indicateurs de statut."""
        # Vider
        while self._status_layout.count():
            item = self._status_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Profils
        profiles = list_profiles()
        self._status_layout.addWidget(self._status_row(
            "Profils enregistrés",
            f"{len(profiles)} profil(s)" if profiles else "Aucun profil",
            bool(profiles)
        ))
        
        # GPU
        gpu_ok, gpu_msg = detect_gpu()
        self._status_layout.addWidget(self._status_row(
            "Accélération GPU",
            gpu_msg,
            gpu_ok
        ))
        
        self._status_layout.addStretch()
        
    def _status_row(self, label: str, value: str, ok: bool) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background-color: transparent;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        
        dot = QLabel("●")
        dot.setFont(QFont("Segoe UI", 12))
        dot.setStyleSheet(f"color: {'#2e7d32' if ok else '#b91c1c'}; background-color: transparent;")
        dot.setFixedWidth(16)
        
        lbl = QLabel(f"<b>{label}:</b>")
        lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        lbl.setFont(QFont("Segoe UI", 10))
        
        val = QLabel(value)
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val.setFont(QFont("Segoe UI", 10))
        val.setStyleSheet(f"color: {'#2e7d32' if ok else '#b91c1c'}; background-color: transparent;")
        val.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        h.addWidget(dot)
        h.addWidget(lbl)
        h.addWidget(val)
        return row
