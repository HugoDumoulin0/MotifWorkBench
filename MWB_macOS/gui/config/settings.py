"""
Gestion de la sauvegarde et du chargement
des profils de configuration de l'analyse.
Les profils sont stockés en JSON dans le dossier profiles/

@jcharlesDS (2026)
"""

import json
from pathlib import Path

PROFILES_DIR = Path(__file__).parent.parent.parent / "profiles"

# Valeurs par défaut
DEFAULT_CONFIG = {
    # Annotation
    "use_gpu": False,
    "language": "fr",
    "annotator": "spacy",  # "stanza" | "spacy"
    
    # Early Selection
    "earlySelection": False,
    "seuil_early_selection": 200,
    "filter_specifs": False,
    "partition_cible": "test",
    "seuil_banalité": 2,
    "early_pos4lemma": "ADJ|NOUN|VERB",
    "user_input_list": False,
    "liste_earlyselection_lemma": [],
    
    # Clustering
    "internal_clustering": True,
    
    # Paramètres des motifs
    "list_itemset_min": [3],
    "list_gap_min": [0],
    "list_gap_max": [0],
    "list_minsup_percent": [25],
    "threads": 4,
    
    # Attributs linguistiques
    "Form": False,
    "Lemma": True,
    "Pos": True,
    "Dep": True,
    "Feats": False,
    
    # Metadata
    "selected_corpus": "",
    "input_type": "raw_txt",
    "input_source_path": "",
    "path_metadata": "",
    "metadata_corpus_dir": "",
    "list_metadata": ["id"],
    "specifs": False,
    
    # Comparaison
    "liste_seuils_lemma": [100, 200],
    "downhill_pos4lemma": "ADJ|ADV|NOUN|VERB",
    "liste_seuils_bigrams": [100],
    
    # Mode
    "mode": "",
}

def ensure_profiles_dir():
    """Crée le dossier profiles/ s'il n'existe pas."""
    PROFILES_DIR.mkdir(exist_ok=True)

def list_profiles() -> list[str]:
    """Retourne la liste des noms de profils sauvegardés."""
    ensure_profiles_dir()
    return [f.stem for f in PROFILES_DIR.glob("*.json")]

def save_profile(name: str, config: dict):
    """Sauvegarde un profil de configuration sous le nom donné."""
    ensure_profiles_dir()
    path = PROFILES_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def _migrate_old_paths(config: dict) -> dict:
    """Migre les anciens chemins vers la nouvelle structure Data/Corpus/."""
    # Migration des chemins pour Textes_raw (plusieurs variantes possibles)
    old_paths = ["./Data/Textes_raw", "Data/Textes_raw", "./Data/Textes_raw/"]
    if config.get("metadata_corpus_dir") in old_paths:
        config["metadata_corpus_dir"] = "./Data/Corpus/Textes_raw"
    
    # Migration des chemins pour metadata.tsv (plusieurs variantes possibles)
    old_metadata_paths = ["./Data/metadata.tsv", "Data/metadata.tsv"]
    if config.get("path_metadata") in old_metadata_paths:
        config["path_metadata"] = "./Data/Corpus/metadata.tsv"

    # Migration pour déduire un corpus sélectionné depuis les chemins existants.
    selected_corpus = config.get("selected_corpus", "")
    if not selected_corpus:
        corpus_dir = str(config.get("metadata_corpus_dir", "")).replace("\\", "/").rstrip("/")
        if "/Data/Corpus/" in corpus_dir:
            maybe_name = corpus_dir.split("/Data/Corpus/")[-1].split("/")[0]
            if maybe_name and maybe_name != "Textes_raw":
                config["selected_corpus"] = maybe_name

    # Replier tout annotateur non supporté vers SpaCy.
    if config.get("annotator") not in {"spacy", "stanza"}:
        config["annotator"] = "spacy"
    
    return config

def load_profile(name: str) -> dict:
    """Charge un profil de configuration. 
    Retourne DEFAULT_CONFIG si le profil n'existe pas."""
    path = PROFILES_DIR / f"{name}.json"
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Fusionne avec les valeurs par défaut pour garantir toutes les clés
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    
    # Migrer les anciens chemins
    merged = _migrate_old_paths(merged)
    
    return merged

def delete_profile(name: str):
    """Supprime un profil de configuration."""
    path = PROFILES_DIR / f"{name}.json"
    if path.exists():
        path.unlink()
