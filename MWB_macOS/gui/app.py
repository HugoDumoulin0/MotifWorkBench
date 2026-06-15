"""
Point d'entrée de l'application GUI.
Lance l'application PyQt6.
@jcharlesDS (2026)
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from gui.main_window import MainWindow

def main():
    # macOS Retina support
    if sys.platform == "darwin":
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("MotifWorkBench")
    app.setOrganizationName("MotifWorkBench")
    app.setFont(QFont("Helvetica Neue", 11))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()
