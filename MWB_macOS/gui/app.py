"""
Point d'entrée de l'application GUI.
Lance l'application PyQt6.
@jcharlesDS (2026)
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QPalette, QColor
from gui.main_window import MainWindow


def _build_light_palette() -> QPalette:
    """Palette claire explicite pour éviter l'héritage du mode sombre macOS."""
    palette = QPalette()

    window = QColor("#f7f8fc")
    base = QColor("#ffffff")
    alt_base = QColor("#eef2f7")
    text = QColor("#111827")
    button = QColor("#ffffff")
    button_text = QColor("#111827")
    highlight = QColor("#2f5d8a")
    highlighted_text = QColor("#ffffff")
    border = QColor("#d1d5db")
    placeholder = QColor("#6b7280")

    palette.setColor(QPalette.ColorRole.Window, window)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, base)
    palette.setColor(QPalette.ColorRole.AlternateBase, alt_base)
    palette.setColor(QPalette.ColorRole.ToolTipBase, base)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, button)
    palette.setColor(QPalette.ColorRole.ButtonText, button_text)
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#b91c1c"))
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, highlighted_text)
    palette.setColor(QPalette.ColorRole.Link, QColor("#1d4ed8"))
    palette.setColor(QPalette.ColorRole.LinkVisited, QColor("#6d28d9"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, placeholder)
    palette.setColor(QPalette.ColorRole.Mid, border)
    palette.setColor(QPalette.ColorRole.Midlight, QColor("#e5e7eb"))
    palette.setColor(QPalette.ColorRole.Dark, QColor("#9ca3af"))
    palette.setColor(QPalette.ColorRole.Shadow, QColor("#9ca3af"))

    disabled_text = QColor("#9ca3af")
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor("#e5e7eb"))

    return palette


def main():
    # macOS Retina support
    if sys.platform == "darwin":
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("MotifWorkBench")
    app.setOrganizationName("MotifWorkBench")
    app.setFont(QFont("Helvetica Neue", 11))
    if sys.platform == "darwin":
        # Force un rendu clair, quelle que soit l'apparence système de macOS.
        app.setStyle("Fusion")
        app.setPalette(_build_light_palette())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()
