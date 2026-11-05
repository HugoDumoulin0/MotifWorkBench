#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
REQUIREMENTS_FILE="${SCRIPT_DIR}/src/requirements.txt"
SUDO_CMD=""
PYTHON_BIN=""

print_line() {
  printf '%s\n' "------------------------------------------------------------------"
}

info() {
  printf '%s\n' "[INFO] $1"
}

warn() {
  printf '%s\n' "[ATTENTION] $1"
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

has_command() {
  command -v "$1" >/dev/null 2>&1
}

ensure_linux() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    error "Ce script est prévu pour Linux uniquement."
    return 1
  fi
}

ensure_sudo_mode() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    SUDO_CMD=""
    return 0
  fi

  if has_command sudo; then
    SUDO_CMD="sudo"
    return 0
  fi

  error "Il faut être root ou disposer de sudo pour installer les dépendances système."
  return 1
}

detect_package_manager() {
  if has_command apt-get; then
    printf '%s\n' "apt"
    return 0
  fi
  if has_command dnf; then
    printf '%s\n' "dnf"
    return 0
  fi
  if has_command yum; then
    printf '%s\n' "yum"
    return 0
  fi
  if has_command pacman; then
    printf '%s\n' "pacman"
    return 0
  fi
  if has_command zypper; then
    printf '%s\n' "zypper"
    return 0
  fi

  return 1
}

select_python() {
  if has_command python3; then
    PYTHON_BIN="$(command -v python3)"
    return 0
  fi

  error "Python 3 est requis pour lancer MotifWorkBench."
  return 1
}

check_prereqs() {
  local ok=0

  if has_command python3; then
    info "Python 3 détecté : $(command -v python3)"
  else
    warn "Python 3 manquant."
    ok=1
  fi

  if has_command perl; then
    info "Perl détecté : $(command -v perl)"
  else
    warn "Perl manquant."
    ok=1
  fi

  if has_command R; then
    info "R détecté : $(command -v R)"
  elif has_command Rscript; then
    info "Rscript détecté : $(command -v Rscript)"
  else
    warn "R manquant."
    ok=1
  fi

  return "$ok"
}

install_with_apt() {
  info "Installation via apt..."
  $SUDO_CMD apt-get update
  $SUDO_CMD apt-get install -y python3 python3-venv python3-pip perl r-base
}

install_with_dnf() {
  info "Installation via dnf..."
  $SUDO_CMD dnf install -y python3 python3-pip perl R
}

install_with_yum() {
  info "Installation via yum..."
  $SUDO_CMD yum install -y python3 python3-pip perl R
}

install_with_pacman() {
  info "Installation via pacman..."
  $SUDO_CMD pacman -Sy --noconfirm python python-pip perl r
}

install_with_zypper() {
  info "Installation via zypper..."
  $SUDO_CMD zypper --non-interactive install python3 python3-pip python3-virtualenv perl R-base
}

install_missing_prereqs() {
  local package_manager

  if ! package_manager="$(detect_package_manager)"; then
    error "Gestionnaire de paquets non pris en charge automatiquement."
    error "Installe manuellement Python 3, Perl et R, puis relance ce script."
    return 1
  fi

  info "Gestionnaire de paquets détecté : ${package_manager}"

  case "$package_manager" in
    apt)
      install_with_apt
      ;;
    dnf)
      install_with_dnf
      ;;
    yum)
      install_with_yum
      ;;
    pacman)
      install_with_pacman
      ;;
    zypper)
      install_with_zypper
      ;;
    *)
      error "Gestionnaire de paquets non géré : ${package_manager}"
      return 1
      ;;
  esac
}

create_virtualenv() {
  if [[ ! -d "$VENV_DIR" ]]; then
    info "Création de l'environnement virtuel dans .venv..."
    if ! "$PYTHON_BIN" -m venv "$VENV_DIR"; then
      error "Impossible de créer l'environnement virtuel."
      return 1
    fi
  else
    info "Environnement virtuel déjà présent : $VENV_DIR"
  fi
}

install_requirements() {
  local venv_python="${VENV_DIR}/bin/python"

  if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
    error "Fichier requirements introuvable : $REQUIREMENTS_FILE"
    return 1
  fi

  info "Mise à jour de pip..."
  if ! "$venv_python" -m pip install --upgrade pip; then
    error "Échec de la mise à jour de pip."
    return 1
  fi

  info "Installation des dépendances Python..."
  if ! "$venv_python" -m pip install -r "$REQUIREMENTS_FILE"; then
    error "Échec de l'installation des dépendances."
    return 1
  fi
}

launch_app() {
  local venv_python="${VENV_DIR}/bin/python"

  info "Lancement de l'application..."
  cd "$SCRIPT_DIR" || return 1
  "$venv_python" run_gui.py
}

main() {
  print_line
  info "Installation et lancement de MotifWorkBench"
  print_line

  if ! ensure_linux; then
    pause_if_needed
    exit 1
  fi

  if check_prereqs; then
    info "Les dépendances système nécessaires sont déjà présentes."
  else
    warn "Certaines dépendances système sont absentes."
    if ! ensure_sudo_mode; then
      pause_if_needed
      exit 1
    fi
    if ! install_missing_prereqs; then
      error "L'installation automatique a échoué."
      pause_if_needed
      exit 1
    fi
  fi

  print_line
  info "Vérification finale des prérequis..."
  print_line

  if ! check_prereqs; then
    error "Les prérequis ne sont pas correctement installés après tentative d'installation."
    pause_if_needed
    exit 1
  fi

  if ! select_python; then
    pause_if_needed
    exit 1
  fi

  if ! create_virtualenv; then
    pause_if_needed
    exit 1
  fi

  if ! install_requirements; then
    pause_if_needed
    exit 1
  fi

  print_line
  info "Tous les prérequis sont OK."
  print_line

  if ! launch_app; then
    error "Le lancement de l'application a échoué."
    pause_if_needed
    exit 1
  fi
}

main "$@"
