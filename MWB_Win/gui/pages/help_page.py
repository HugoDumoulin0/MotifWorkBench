"""
Page d'Aide : guide rapide d'utilisation de l'application.
@jcharlesDS (2026)
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QLabel, QScrollArea, QWidget, QTextEdit
)
from PyQt6.QtGui import QFont

from gui.widgets.base_page import BasePage, TEXT_PRIMARY

class HelpPage(BasePage):
    """Page d'aide statique avec étapes, FAQ et bonnes pratiques."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
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
            "Aide",
            "Guide rapide pour configurer, lancer et interpréter les analyses."
        ))
        
        quickstart_group = self.make_group("Démarrage rapide")
        quickstart_layout = QVBoxLayout(quickstart_group)
        quickstart = QLabel(
            "1. Configurez votre profil dans la section Configuration.\n"
            "2. Vérifiez les paramètres et lancez l'analyse depuis la section Analyse.\n"
            "3. Consultez les résultats dans la section Résultats et Concordancier.\n"
            "4. Suivez l'historique de vos analyses dans la section Historique."
        )
        quickstart.setWordWrap(True)
        quickstart.setFont(QFont("Segoe UI", 10))
        quickstart.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        quickstart_layout.addWidget(quickstart)
        layout.addWidget(quickstart_group)
        
        faq_group = self.make_group("FAQ")
        faq_layout = QVBoxLayout(faq_group)
        
        faq_text = QTextEdit()
        faq_text.setReadOnly(True)
        faq_text.setMinimumHeight(250)
        faq_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #ffffff;
                color: {TEXT_PRIMARY};
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px;
                font-size: 10pt;
            }}
        """)
        faq_text.setPlainText(
            "Q: Je n'ai aucun résultat, que vérifier ?\n"
            "R: Vérifiez le minimum support, les gaps, les attributs activés et les données d'entrée.\n\n"
            "Q: Le GPU n'est pas détecté.\n"
            "R: Vérifiez les drivers CUDA et l'installation de torch compatible.\n\n"
            "Q: Où sont les sorties ?\n"
            "R: Patterns_results, Clustering_results, logs.\n\n"
            "Q: Comment relancer rapidement ?\n"
            "R: Sauvegardez un profil en Configuration puis rechargez-le avant analyse."
        )
        faq_layout.addWidget(faq_text)
        layout.addWidget(faq_group)
        
        tips_group = self.make_group("Bonnes pratiques")
        tips_layout = QVBoxLayout(tips_group)
        tips = QLabel(
            "- Commencer avec des paramètres modestes pour valider le pipeline.\n"
            "- Sauvegarder plusieurs profils pour comparer les réglages.\n"
            "- Utiliser Concordancier pour interpréter les motifs en contexte.\n"
            "- Vérifier Historique après chaque run pour suivre les sorties."
        )
        tips.setWordWrap(True)
        tips.setFont(QFont("Segoe UI", 10))
        tips.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        tips_layout.addWidget(tips)
        layout.addWidget(tips_group)
        
        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)