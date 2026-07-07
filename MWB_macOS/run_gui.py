"""
Lance l'interface graphique de MotifWorkBench.
Usage : python run_gui.py
@jcharlesDS (2026)
"""

import os
import sys

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(APP_ROOT)

# Assure que la racine est dans le path
sys.path.insert(0, APP_ROOT)

from gui.app import main

if __name__ == "__main__":
    main()
