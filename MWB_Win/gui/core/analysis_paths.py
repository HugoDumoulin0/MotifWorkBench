"""
Gestion des chemins pour organiser les analyses par groupe et configuration.
Structure : analyses_root/{analysis_group_name}/{config_id}/[tous les dossiers générés]
@jcharlesDS (2026)
"""

from pathlib import Path
from datetime import datetime
import json
import hashlib
import shutil


def get_project_root() -> Path:
    """Retourne la racine du projet."""
    return Path(__file__).resolve().parents[2]


def get_default_analyses_root() -> Path:
    """Retourne le dossier d'analyses par défaut du projet."""
    return get_project_root() / "Data" / "analyses"


def get_analyses_root() -> Path:
    """Retourne le dossier racine de toutes les analyses."""
    settings_path = get_project_root() / "app_settings.json"
    default_root = get_default_analyses_root()

    if settings_path.exists():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            configured_root = settings.get("analyses_root_path", "")
            if configured_root:
                return Path(configured_root).expanduser()
        except Exception:
            pass

    return default_root


def compute_config_hash(config: dict) -> str:
    """
    Calcule un hash court (6 caractères) d'une configuration.
    Utilisé pour identifier des configurations identiques.
    """
    # Exclure les clés qui ne sont pas pertinentes pour l'unicité
    config_copy = {
        k: v
        for k, v in config.items()
        if k not in ["mode", "corpus_name", "analysis_group_name", "_display_profile_name"]
    }
    config_str = json.dumps(config_copy, sort_keys=True)
    return hashlib.md5(config_str.encode()).hexdigest()[:6]


def find_existing_analysis(analysis_group_name: str, config: dict) -> str | None:
    """
    Cherche si une analyse avec la même configuration existe déjà pour ce groupe.
    Retourne le config_id si trouvé, None sinon.
    """
    analysis_group_path = get_analyses_root() / analysis_group_name
    if not analysis_group_path.exists():
        return None
    
    target_hash = compute_config_hash(config)
    
    # Parcourir toutes les analyses existantes pour ce groupe
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
    Génère un ID descriptif pour une configuration.
    Format: YYYYMMDD_HHMMSS_description
    Description basée sur les paramètres qui diffèrent du défaut (Option A).
    Limite: 40-50 caractères total.
    """
    from gui.config.settings import DEFAULT_CONFIG
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # 15 car
    
    # Construire la description (24-34 car max)
    parts = []
    
    # 1. Features optionnelles (priorité haute)
    if config.get("earlySelection", False):
        parts.append("earlysel")
    if config.get("specifs", False):
        parts.append("specifs")
    if config.get("filter_specifs", False):
        parts.append("filtspec")
    if not config.get("internal_clustering", True):
        parts.append("noclust")
    
    # 2. Paramètres des motifs (critique)
    minsup = config.get("list_minsup_percent", [25])[0]
    if minsup != 25:
        parts.append(f"minsup{minsup}")
    
    itemset = config.get("list_itemset_min", [3])[0]
    if itemset != 3:
        parts.append(f"itemset{itemset}")
    
    gap_min = config.get("list_gap_min", [0])[0]
    gap_max = config.get("list_gap_max", [0])[0]
    if gap_min != 0 or gap_max != 0:
        parts.append(f"gap{gap_min}-{gap_max}")
    
    # 3. Attributs linguistiques (toujours affiché si ≠ défaut LPD)
    attrs = []
    if config.get("Lemma", True):
        attrs.append("L")
    if config.get("Pos", True):
        attrs.append("P")
    if config.get("Dep", True):
        attrs.append("D")
    if config.get("Form", False):
        attrs.append("F")
    if config.get("Feats", False):
        attrs.append("Ft")
    
    attrs_str = "".join(attrs)
    # Afficher seulement si différent du défaut (LPD)
    if attrs_str != "LPD":
        parts.append(attrs_str)
    
    # 4. Seuils avancés (si modifiés)
    if config.get("earlySelection", False):
        seuil_early = config.get("seuil_early_selection", 200)
        if seuil_early != 200:
            parts.append(f"seuilE{seuil_early}")
    
    seuil_ban = config.get("seuil_banalité", 2)
    if seuil_ban != 2:
        parts.append(f"seuilB{seuil_ban}")
    
    # 5. Langue (si ≠ fr)
    lang = config.get("language", "fr")
    if lang != "fr":
        parts.append(lang)
    
    # 6. Annotateur (si ≠ spacy)
    annotator_tool = config.get("annotator_tool", "spacy")
    annotator_map = {
        "spacy": "spy",
        "stanza": "stz"
    }
    if annotator_tool != "spacy":
        parts.append(annotator_map.get(annotator_tool, annotator_tool))
    
    # Construire la description
    if not parts:
        description = "default"
    else:
        description = "_".join(parts)
    
    # Vérifier la limite de 50 caractères (15 timestamp + 1 underscore + description)
    full_id = f"{timestamp}_{description}"
    
    if len(full_id) > 50:
        # Troncature : garder les éléments les plus importants
        # Ordre de suppression : seuils avancés > filtspec > noclust > specifs > earlysel
        priority_parts = []
        
        # Params critiques (toujours gardés)
        for part in parts:
            if (part.startswith("minsup") or part.startswith("itemset") or part.startswith("gap") or 
                part in ["spy", "stz", "en", "fr"] or 
                (len(part) <= 4 and not part.startswith("seuil"))):
                priority_parts.append(part)
        
        # Features importantes (gardées si place)
        for part in ["earlysel", "specifs"]:
            if part in parts and len("_".join(priority_parts + [part])) + 16 <= 50:
                priority_parts.append(part)
        
        description = "_".join(priority_parts) if priority_parts else "default"
        full_id = f"{timestamp}_{description}"
        
        # Si encore trop long, ajouter un hash court
        if len(full_id) > 50:
            config_hash = compute_config_hash(config)
            description = f"{description[:30]}_{config_hash}"
            full_id = f"{timestamp}_{description}"
    
    return full_id


def get_analysis_root(analysis_group_name: str, config_id: str) -> Path:
    """
    Retourne le dossier racine pour une analyse spécifique.
    Args:
        analysis_group_name: Nom du groupe d'analyses (ex: "analyse_presse")
        config_id: ID de la configuration (ex: "20260519_143022_a1b2c3")
    """
    return get_analyses_root() / analysis_group_name / config_id


def create_analysis_structure(analysis_group_name: str, config_id: str, config: dict) -> dict:
    """
    Crée la structure complète de dossiers pour une nouvelle analyse.
    Retourne un dictionnaire avec tous les chemins.
    """
    root = get_analysis_root(analysis_group_name, config_id)
    
    # Calculer path_metadata depuis config["path_corpus"]
    path_corpus = config.get("path_corpus", "")
    if not path_corpus:
        raise ValueError("path_corpus manquant dans la configuration. Veuillez sélectionner un corpus dans la page Configuration.")
    path_metadata = Path(path_corpus) / "metadata.tsv"
    
    paths = {
        "root": root,
        "path_metadata": path_metadata,
        "tagged_stanza": root / "Textes_tagged",
        "tagged_for_dmt4": root / "Textes_tagged_for_dmt4",
        "textes_vrt": root / "textesVRT",
        "cwb_corpus": root / "cwb-corpus",
        "dmt4_files": root / "DMT4_files",
        "lexiques": root / "Lexiques",
        "clustering_results": root / "Clustering_results",
        "patterns_results": root / "Patterns_results",
        # Note: les logs sont écrits dans ./logs/ à la racine du projet, pas dans l'analyse
        "underscore_fix": root / "underscore_fix",
    }
    
    # Ajouter earlySelection si utilisé dans la config
    if config.get("earlySelection", False):
        paths["early_selection"] = root / "earlySelection"
    
    # Créer tous les dossiers
    for key, path in paths.items():
        if key != "path_metadata":  # metadata est un fichier, pas un dossier
            path.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder la configuration et un résumé
    summary = {
        "analysis_group_name": analysis_group_name,
        "corpus_name": analysis_group_name,
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


def list_corpus_names() -> list[str]:
    """Alias rétrocompatible vers les groupes d'analyses."""
    return list_analysis_group_names()


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


def list_configs_for_corpus(corpus_name: str) -> list[dict]:
    """Alias rétrocompatible vers les groupes d'analyses."""
    return list_configs_for_analysis_group(corpus_name)


def delete_analysis_configs(analysis_group_name: str, config_ids: list[str]) -> int:
    """Supprime une ou plusieurs configurations dans un groupe d'analyses."""
    deleted_count = 0
    analysis_group_path = get_analyses_root() / analysis_group_name
    if not analysis_group_path.exists():
        return deleted_count

    for config_id in config_ids:
        config_path = analysis_group_path / config_id
        if config_path.exists() and config_path.is_dir():
            shutil.rmtree(config_path)
            deleted_count += 1

    if analysis_group_path.exists() and not any(analysis_group_path.iterdir()):
        analysis_group_path.rmdir()

    return deleted_count


def get_textes_raw_path() -> Path:
    """Retourne le chemin vers le dossier Textes_raw (source, ne change pas)."""
    return get_project_root() / "Data" / "Corpus" / "Textes_raw"


def get_metadata_source_path() -> Path:
    """Retourne le chemin vers le fichier metadata.tsv source."""
    return get_project_root() / "Data" / "Corpus" / "metadata.tsv"
