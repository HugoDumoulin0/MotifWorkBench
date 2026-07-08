"""
Gestion des chemins pour organiser les analyses par groupe et configuration.
Structure : Data/analyses/{analysis_group_name}/{config_id}/[tous les dossiers generes]
@jcharlesDS (2026)
"""

from pathlib import Path
from datetime import datetime
import json
import hashlib

# Import de la génération intelligente des noms d'analyse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from gui.config.analysis_naming import generate_analysis_id


def get_project_root() -> Path:
    """Retourne la racine du projet."""
    return Path(__file__).resolve().parents[2]


def get_analyses_root() -> Path:
    """Retourne le dossier racine de toutes les analyses."""
    return get_project_root() / "Data" / "analyses"


def get_annotations_cache_root() -> Path:
    """Retourne le dossier racine du cache partagé des annotations."""
    return get_project_root() / "Data" / "annotations_cache"


def _sanitize_for_path(value: str) -> str:
    """Nettoie une valeur pour l'utiliser dans un nom de dossier."""
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value.strip())
    return cleaned or "inconnu"


def build_annotation_cache_paths(
    selected_corpus: str,
    annotator_name: str,
    actual_model_name: str,
    use_gpu: bool,
) -> dict:
    """Construit les chemins du cache partagé d'annotation."""
    corpus_key = _sanitize_for_path(selected_corpus)
    annotator_key = _sanitize_for_path(annotator_name.lower())
    model_key = _sanitize_for_path(actual_model_name)
    compute_key = "gpu" if use_gpu else "cpu"
    root = get_annotations_cache_root() / corpus_key / annotator_key / f"{model_key}_{compute_key}"
    return {
        "root": root,
        "tagged": root / "Textes_tagged",
        "underscore_fix": root / "underscore_fix",
        "cache_info": root / "cache_info.json",
    }


def compute_config_hash(config: dict) -> str:
    """
    Calcule un hash court (6 caractères) d'une configuration.
    Utilisé pour identifier des configurations identiques.
    """
    # Exclure les clés qui ne sont pas pertinentes pour l'unicité
    config_copy = {
        k: v for k, v in config.items()
        if k not in ["mode", "analysis_group_name"]
    }
    config_str = json.dumps(config_copy, sort_keys=True)
    return hashlib.md5(config_str.encode()).hexdigest()[:6]


def find_existing_analysis(analysis_group_name: str, config: dict) -> str | None:
    """
    Cherche si une analyse avec la meme configuration existe deja pour ce groupe.
    Retourne le config_id si trouvé, None sinon.
    """
    analysis_group_path = get_analyses_root() / analysis_group_name
    if not analysis_group_path.exists():
        return None
    
    target_hash = compute_config_hash(config)
    
    # Parcourir toutes les analyses existantes pour ce corpus
    for config_dir in sorted(analysis_group_path.iterdir(), reverse=True):
        if not config_dir.is_dir() or config_dir.name.startswith('.'):
            continue
        
        info_file = config_dir / "analysis_info.json"
        if info_file.exists():
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    existing_config = info.get("config", {})
                    existing_hash = compute_config_hash(existing_config)
                    
                    if existing_hash == target_hash:
                        # Configuration identique trouvée !
                        return config_dir.name
            except (json.JSONDecodeError, KeyError):
                continue
    
    return None


def generate_config_id(config: dict) -> str:
    """
    Génère un ID unique pour une configuration basé sur timestamp + description intelligente.
    Format: YYYYMMDD_HHMMSS_<description>
    Description: seulement les paramètres différents des valeurs par défaut.
    """
    return generate_analysis_id(config)


def get_analysis_root(analysis_group_name: str, config_id: str) -> Path:
    """
    Retourne le dossier racine pour une analyse spécifique.
    Args:
        analysis_group_name: Nom du groupe d'analyses (ex: "analyse_test")
        config_id: ID de la configuration (ex: "20260519_143022_a1b2c3")
    """
    return get_analyses_root() / analysis_group_name / config_id


def create_analysis_structure(analysis_group_name: str, config_id: str, config: dict) -> dict:
    """
    Crée la structure complète de dossiers pour une nouvelle analyse.
    Retourne un dictionnaire avec tous les chemins.
    """
    root = get_analysis_root(analysis_group_name, config_id)
    
    paths = {
        "root": root,
        "metadata": root / "metadata.tsv",
        "tagged": root / "Textes_tagged",
        "tagged_for_dmt4": root / "Textes_tagged_for_dmt4",
        "textes_vrt": root / "textesVRT",
        "cwb_corpus": root / "cwb-corpus",
        "dmt4_files": root / "DMT4_files",
        "lexiques": root / "Lexiques",
        "clustering_results": root / "Clustering_results",
        "patterns_results": root / "Patterns_results",
        "logs": get_project_root() / "logs",
        "underscore_fix": root / "underscore_fix",
    }
    
    # Ajouter earlySelection si utilisé dans la config
    if config.get("earlySelection", False):
        paths["early_selection"] = root / "earlySelection"
    
    # Créer tous les dossiers
    for key, path in paths.items():
        if key != "metadata":  # metadata est un fichier, pas un dossier
            path.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder la configuration et un résumé
    summary = {
        "analysis_group_name": analysis_group_name,
        "config_id": config_id,
        "created_at": datetime.now().isoformat(),
        "config": config
    }
    
    summary_path = root / "analysis_info.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return paths


def list_analysis_group_names() -> list[str]:
    """Liste tous les groupes d'analyses disponibles."""
    analyses_root = get_analyses_root()
    if not analyses_root.exists():
        return []
    
    return sorted([
        d.name for d in analyses_root.iterdir() 
        if d.is_dir() and not d.name.startswith('.')
    ])


def list_configs_for_analysis_group(analysis_group_name: str) -> list[dict]:
    """
    Liste toutes les configurations disponibles pour un groupe d'analyses.
    Retourne une liste de dicts avec config_id, created_at, et config.
    """
    analysis_group_path = get_analyses_root() / analysis_group_name
    if not analysis_group_path.exists():
        return []
    
    configs = []
    for config_dir in sorted(analysis_group_path.iterdir(), reverse=True):
        if not config_dir.is_dir() or config_dir.name.startswith('.'):
            continue
        
        info_file = config_dir / "analysis_info.json"
        if info_file.exists():
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    configs.append({
                        "config_id": config_dir.name,
                        "created_at": info.get("created_at", "Unknown"),
                        "config": info.get("config", {})
                    })
            except Exception:
                # Si le fichier JSON est corrompu, on l'ignore
                continue
    
    return configs


def get_textes_raw_path() -> Path:
    """Retourne le chemin vers le dossier Textes_raw (source, ne change pas)."""
    return get_project_root() / "Data" / "Corpus" / "Textes_raw"


def get_metadata_source_path() -> Path:
    """Retourne le chemin vers le fichier metadata.tsv source."""
    return get_project_root() / "Data" / "Corpus" / "metadata.tsv"
