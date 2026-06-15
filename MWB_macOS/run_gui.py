"""
Lance l'interface graphique de MotifWorkBench.
Usage : python run_gui.py
@jcharlesDS (2026)
"""

import os
import sys

# Assure que la racine est dans le path
sys.path.insert(0, os.path.dirname(__file__))

from gui.app import main

if __name__ == "__main__":
    main()