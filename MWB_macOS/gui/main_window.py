"""
Fenêtre principale de l'application.
Contient la sidebar de navigation et le contenu central.
@jcharlesDS (2026)
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QStackedWidget,
    QLabel, QToolButton
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui.pages.config_page import ConfigPage
from gui.pages.home_page import HomePage
from gui.pages.analysis_page import AnalysisPage
from gui.pages.settings_page import SettingsPage
from gui.pages.shiny_page import ShinyPage
from gui.pages.concordancer_page import ConcordancerPage
from gui.pages.history_page import HistoryPage
from gui.pages.help_page import HelpPage


class SidebarButton(QPushButton):
    """
    Bouton de navigation dans la sidebar.
    """
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._full_text = text
        self.setCheckable(True)
        self.setMinimumHeight(45)
        self.setFont(QFont("Helvetica Neue", 11))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                background-color: transparent;
                color: #cccccc;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                color: #ffffff;
            }
            QPushButton:checked {
                background-color: #3a3a5a;
                color: #ffffff;
                font-weight: bold;
            }
        """)

class MainWindow(QMainWindow):
    """
    Fenêtre principale avec sidebar et zone de contenu.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MotifWorkBench")
        self.setMinimumSize(1280, 720)
        
        self._sidebar_expanded_width = 220
        self._sidebar_collapsed_width = 64
        self._sidebar_expanded = True
        
        self._setup_ui()
        self._nav_buttons[0].setChecked(True)  # Sélectionne la première page par défaut
        
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sidebar
        self._sidebar = QWidget()
        self._sidebar.setFixedWidth(self._sidebar_expanded_width)
        self._sidebar.setStyleSheet("background-color: #1e1e2e;")
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(10, 16, 10, 16)
        sidebar_layout.setSpacing(4)
        
        # Bouton de bascule
        self._toggle_btn = QToolButton()
        self._toggle_btn.setText("◀")
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle_sidebar)
        self._toggle_btn.setStyleSheet("""
            QToolButton {
                color: #ffffff;
                background-color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 6px;
            }
            QToolButton:hover {
                background-color: #2a2a3a;
            }
        """)
        sidebar_layout.addWidget(self._toggle_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Titre
        self._sidebar_title = QLabel("MotifWorkBench")
        self._sidebar_title.setFont(QFont("Helvetica Neue", 13, QFont.Weight.Bold))
        self._sidebar_title.setStyleSheet("color: #ffffff; padding: 8px 8px 16px 8px;")
        self._sidebar_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self._sidebar_title)
        
        # Pages
        self._pages_def = [
            ("Accueil", self._make_home_page()),
            ("Réglages", ConfigPage()),
            ("Analyse", AnalysisPage()),
            ("Résultats", self._make_shiny_page()),
            ("Concordancier", ConcordancerPage()),
            ("Historique", HistoryPage()),
            ("Paramètres", self._make_settings_page()),
            ("Aide", HelpPage()),
        ]
        
        # Récupérer les pages pour les connecter
        config_page = self._pages_def[1][1]  # ConfigPage
        analysis_page = self._pages_def[2][1]  # AnalysisPage
        self._shiny_page = self._pages_def[3][1]  # ShinyPage
        
        # Connecter le signal de configuration à la page d'analyse
        config_page.config_applied.connect(analysis_page.update_config)
        
        # Permettre à AnalysisPage d'accéder à ConfigPage pour obtenir la config actuelle
        analysis_page.set_config_page(config_page)
        
        self._stack = QStackedWidget()
        self._nav_buttons = []
        
        for label, page_widget in self._pages_def:
            btn = SidebarButton(label)
            btn.clicked.connect(lambda checked, w=page_widget, b=btn: self._navigate(w, b))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)
            self._stack.addWidget(page_widget)
            
        sidebar_layout.addStretch()
        
        layout.addWidget(self._sidebar)
        layout.addWidget(self._stack)
    
    def _navigate(self, page_widget, clicked_btn):
        """
        Change la page affichée et met à jour les boutons.
        """
        self._stack.setCurrentWidget(page_widget)
        for btn in self._nav_buttons:
            btn.setChecked(btn is clicked_btn)
    
    def _toggle_sidebar(self):
        """
        Affiche ou rétracte la sidebar.
        """
        self._sidebar_expanded = not self._sidebar_expanded
        
        if self._sidebar_expanded:
            self._sidebar.setFixedWidth(self._sidebar_expanded_width)
            self._toggle_btn.setText("◀")
            self._sidebar_title.show()
            for btn, (label, _) in zip(self._nav_buttons, self._pages_def):
                btn.setText(label)
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding: 8px 16px;
                        border: none;
                        border-radius: 6px;
                        background-color: transparent;
                        color: #cccccc;
                    }
                    QPushButton:hover {
                        background-color: #2a2a2a;
                        color: #ffffff;
                    }
                    QPushButton:checked {
                        background-color: #3a3a5a;
                        color: #ffffff;
                        font-weight: bold;
                    }
                """)
        else:
            self._sidebar.setFixedWidth(self._sidebar_collapsed_width)
            self._toggle_btn.setText("▶")
            self._sidebar_title.hide()
            for btn, (label, _) in zip(self._nav_buttons, self._pages_def):
                # Affiche un repère court (lettre/logo texte) quand la sidebar est rétractée.
                btn.setText(self._collapsed_nav_label(label))
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: center;
                        padding: 8px;
                        border: none;
                        border-radius: 6px;
                        background-color: transparent;
                        color: #cccccc;
                    }
                    QPushButton:hover {
                        background-color: #2a2a2a;
                        color: #ffffff;
                    }
                    QPushButton:checked {
                        background-color: #3a3a5a;
                        color: #ffffff;
                        font-weight: bold;
                    }
                """)

    def _collapsed_nav_label(self, label: str) -> str:
        """
        Génère un libellé compact affiché lorsque la sidebar est rétractée.
        """
        words = label.split()
        if len(words) >= 2:
            return "".join(word[0] for word in words[:2]).upper()
        if len(label) <= 2:
            return label.upper()
        return label[:2].upper()

    def _make_home_page(self):
        page = HomePage()
        page.navigate_to.connect(self._navigate_by_name)
        return page
    
    def _make_settings_page(self):
        page = SettingsPage()
        return page
    
    def _make_shiny_page(self):
        return ShinyPage()
    
    def _navigate_by_name(self, name: str):
        for i, (label, widget) in enumerate(self._pages_def):
            if label == name:
                self._navigate(widget, self._nav_buttons[i])
                # Si on navigue vers la page de visualisation, charger automatiquement l'URL
                if name == "Résultats":
                    self._shiny_page.load_shiny_url()
                break
    
    def _make_placeholder(self, name):
        """
        Crée une page temporaire en attendant l'implémentation réelle.
        """
        widget = QWidget()
        widget.setStyleSheet("background-color: #13131f;")
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel(f"Page : {name}\n(à implémenter)")
        label.setFont(QFont("Helvetica Neue", 15))
        label.setStyleSheet("color: #888888;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        return widget
