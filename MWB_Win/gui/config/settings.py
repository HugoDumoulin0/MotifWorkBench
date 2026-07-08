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
    "annotator_tool": "spacy",  # spacy ou stanza
    "use_gpu": False,
    "language": "fr",
    
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
    
    # Corpus et metadata (sera chargé depuis last_analysis.json)
    "input_mode": "raw",  # raw, annotated_conllu ou prepared_conllu_zip
    "path_corpus": "",  # Pas de valeur par défaut pour éviter référence à un corpus inexistant
    "path_annotated_corpus": "",
    "path_prepared_archive": "",
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
    from pathlib import Path
    
    # Migration metadata_corpus_dir -> path_corpus
    if "metadata_corpus_dir" in config:
        old_path = config["metadata_corpus_dir"]
        
        # Tenter de migrer les anciens chemins vers la nouvelle structure
        if old_path and not Path(old_path).exists():
            # Ancien chemin invalide : essayer de trouver le corpus dans Data/Corpus/
            # Ex: "./Data/Textes_raw" → "./Data/Corpus/Textes_raw"
            folder_name = Path(old_path).name  # "Textes_raw"
            new_path = f"./Data/Corpus/{folder_name}"
            
            if Path(new_path).exists():
                config["path_corpus"] = new_path
            else:
                # Impossible de migrer : laisser vide pour forcer l'utilisateur à choisir
                config["path_corpus"] = ""
        else:
            # Chemin valide : le conserver
            config["path_corpus"] = old_path
        
        del config["metadata_corpus_dir"]
    
    # Retirer path_metadata (sera calculé automatiquement depuis path_corpus)
    if "path_metadata" in config:
        del config["path_metadata"]

    # Migrer les anciens annotateurs retirés vers spaCy.
    if config.get("annotator_tool") in {"udpipe", "trankit"}:
        config["annotator_tool"] = "spacy"
    
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
