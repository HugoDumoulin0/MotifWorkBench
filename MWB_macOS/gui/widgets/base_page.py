"""
Widget de base pour toutes les pages de l'application
Il fournit les styles et utilitaires communs à toutes les pages.
@jcharlesDS (2026)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox
from PyQt6.QtGui import QFont

PAGE_BG = "#f7f8fc"
CARD_BG = "#ffffff"
TEXT_PRIMARY = "#1f2937"
TEXT_SECONDARY = "#6b7280"
BORDER_COLOR = "#e5e7eb"
ACCENT = "#3a3a5a"

def page_stylesheet() -> str:
    return f"""
        QWidget {{
            background-color: {PAGE_BG};
            color: {TEXT_PRIMARY};
        }}
        QToolTip {{
            background-color: #fffbe6;
            color: #1f2937;
            border: 1px solid #f0c040;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 13px;
        }}
    """

def group_stylesheet() -> str:
    return (
        "QGroupBox {"
        f"  background-color: {CARD_BG};"
        f"  border: 1px solid {BORDER_COLOR};"
        "  border-radius: 8px;"
        "  margin-top: 12px;"
        "  padding: 12px 8px 8px 8px;"
        "  font-weight: bold;"
        "}"
        "QGroupBox::title {"
        f"  color: {TEXT_PRIMARY};"
        "  subcontrol-origin: margin;"
        "  subcontrol-position: top left;"
        "  padding: 0 6px;"
        "  left: 12px;"
        "  top: 2px;"
        "}"
        f"QGroupBox QLabel {{ color: {TEXT_PRIMARY}; background-color: transparent; }}"
        f"QGroupBox QCheckBox {{ color: {TEXT_PRIMARY}; background-color: transparent; }}"
        f"QGroupBox QComboBox {{ color: {TEXT_PRIMARY}; }}"
        f"QGroupBox QSpinBox {{ color: {TEXT_PRIMARY}; }}"
        f"QGroupBox QLineEdit {{ color: {TEXT_PRIMARY}; }}"
    )

class BasePage(QWidget):
    """
    Classe de base pour les pages de l'application.
    Applique les styles communs et fournit des utilitaires pour la mise en page.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(page_stylesheet())
    
    # Utilitaires
    def make_title(self, text: str, subtitle: str = "") -> QWidget:
        """Retourne un bloc titre + sous-titre optionnel."""
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(2)
        
        lbl = QLabel(text)
        lbl.setFont(QFont("Helvetica Neue", 20, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background-color: transparent;")
        layout.addWidget(lbl)
        
        if subtitle:
            sub = QLabel(subtitle)
            sub.setFont(QFont("Helvetica Neue", 11))
            sub.setStyleSheet(f"color: {TEXT_SECONDARY}; background-color: transparent;")
            layout.addWidget(sub)
        
        return container
    
    def make_group(self, title: str) -> QGroupBox:
        """Retourne un QGroupBox stylisé avec le style carte."""
        box = QGroupBox(title)
        box.setStyleSheet(group_stylesheet())
        return box
