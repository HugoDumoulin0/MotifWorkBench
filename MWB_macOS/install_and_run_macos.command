#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/src/requirements.txt"
GUI_ENTRYPOINT="$SCRIPT_DIR/run_gui.py"

print_header() {
  echo
  echo "============================================================"
  echo "$1"
  echo "============================================================"
}

require_brew() {
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew n'est pas installe."
    echo "Installez-le d'abord ici : https://brew.sh"
    exit 1
  fi
}

install_if_missing() {
  local label="$1"
  local command_name="$2"
  local brew_package="$3"

  echo "Verification de $label..."
  if command -v "$command_name" >/dev/null 2>&1; then
    echo "$label est deja installe."
  else
    echo "$label non trouve. Installation via Homebrew..."
    brew install "$brew_package"
  fi
}

print_header "Verification des prerequis systeme"
require_brew

install_if_missing "Python 3" "python3" "python"
install_if_missing "Perl" "perl" "perl"
install_if_missing "Rscript" "Rscript" "r"

echo "Python : $(command -v python3)"
echo "Rscript : $(command -v Rscript)"
echo "Perl : $(command -v perl)"

print_header "Preparation de l'environnement virtuel"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creation de l'environnement virtuel dans $VENV_DIR"
  python3 -m venv "$VENV_DIR"
else
  echo "Environnement virtuel existant detecte : $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

print_header "Mise a jour de pip"
python -m pip install --upgrade pip

print_header "Installation des dependances Python"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
  echo "Erreur : fichier requirements introuvable : $REQUIREMENTS_FILE"
  exit 1
fi
python -m pip install -r "$REQUIREMENTS_FILE"

print_header "Lancement de l'application"
if [ ! -f "$GUI_ENTRYPOINT" ]; then
  echo "Erreur : point d'entree GUI introuvable : $GUI_ENTRYPOINT"
  exit 1
fi

echo "Demarrage de MotifWorkBench..."
exec python "$GUI_ENTRYPOINT"
