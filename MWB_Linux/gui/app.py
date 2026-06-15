"""
Point d'entrée de l'application GUI.
Lance l'application PyQt6.
@jcharlesDS (2026)
"""

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MotifWorkBench")
    app.setOrganizationName("MotifWorkBench")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()