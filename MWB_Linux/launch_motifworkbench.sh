#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="${SCRIPT_DIR}/.venv/bin/python"
APP_ENTRY="${SCRIPT_DIR}/run_gui.py"

info() {
  printf '%s\n' "[INFO] $1"
}

error() {
  printf '%s\n' "[ERREUR] $1" >&2
}

pause_if_needed() {
  if [[ -t 0 ]]; then
    printf '\n'
    read -r -p "Appuyez sur Entrée pour fermer..."
  fi
}

ensure_linux() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    error "Ce lanceur est prévu pour Linux uniquement."
    return 1
  fi
}

check_runtime() {
  if [[ ! -f "$APP_ENTRY" ]]; then
    error "Fichier d'entrée introuvable : $APP_ENTRY"
    return 1
  fi

  if [[ ! -x "$VENV_PYTHON" ]]; then
    error "Environnement virtuel introuvable ou incomplet : $VENV_PYTHON"
    error "Lance d'abord ./install_and_run_linux.sh pour préparer l'installation."
    return 1
  fi

  if ! command -v perl >/dev/null 2>&1; then
    error "Perl n'est pas disponible sur cette machine."
    return 1
  fi

  if ! command -v Rscript >/dev/null 2>&1; then
    error "Rscript n'est pas disponible sur cette machine."
    return 1
  fi
}

launch_app() {
  info "Lancement de MotifWorkBench..."
  cd "$SCRIPT_DIR" || return 1
  "$VENV_PYTHON" "$APP_ENTRY"
}

main() {
  if ! ensure_linux; then
    pause_if_needed
    exit 1
  fi

  if ! check_runtime; then
    pause_if_needed
    exit 1
  fi

  if ! launch_app; then
    error "Le lancement de MotifWorkBench a échoué."
    pause_if_needed
    exit 1
  fi
}

main "$@"
