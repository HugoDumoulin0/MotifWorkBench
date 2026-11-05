#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
GUI_ENTRYPOINT="$SCRIPT_DIR/run_gui.py"
INSTALL_SCRIPT="$SCRIPT_DIR/install_and_run_macos.command"

print_header() {
  echo
  echo "============================================================"
  echo "$1"
  echo "============================================================"
}

pause_before_exit() {
  echo
  read -r "?Appuyez sur Entree pour fermer cette fenetre..."
}

fail() {
  echo
  echo "Erreur : $1"
  pause_before_exit
  exit 1
}

print_header "Lancement de MotifWorkBench"

if ! command -v python3 >/dev/null 2>&1; then
  fail "Python 3 n'est pas disponible sur cette machine.
Lancez d'abord $INSTALL_SCRIPT pour installer l'application."
fi

if [ ! -d "$VENV_DIR" ]; then
  fail "Environnement virtuel introuvable : $VENV_DIR
Lancez d'abord $INSTALL_SCRIPT pour effectuer la premiere installation."
fi

if [ ! -f "$VENV_DIR/bin/python" ]; then
  fail "Python du venv introuvable dans : $VENV_DIR/bin/python
Relancez $INSTALL_SCRIPT pour recreer l'environnement."
fi

if [ ! -f "$GUI_ENTRYPOINT" ]; then
  fail "Point d'entree introuvable : $GUI_ENTRYPOINT"
fi

source "$VENV_DIR/bin/activate"

echo "Demarrage de MotifWorkBench..."
if ! python "$GUI_ENTRYPOINT"; then
  fail "Le lancement de l'application a echoue."
fi
