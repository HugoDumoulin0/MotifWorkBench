"""
Génération automatique de noms d'analyse avec timestamp et description intelligente.
Format: YYYYMMDD_HHMMSS_<description>
Description: seulement les paramètres différents des valeurs par défaut.

@jcharlesDS (2026)
"""

from datetime import datetime
from typing import Dict
import re
from gui.config.settings import DEFAULT_CONFIG


def _slugify(text: str) -> str:
    """Convertit un texte en slug compatible filesystem (ASCII safe)."""
    # Remplacer les caractères non-alphanumériques par underscore
    text = re.sub(r'[^\w\s-]', '', text.lower())
    # Remplacer espaces et tirets multiples par underscore unique
    text = re.sub(r'[-\s]+', '_', text)
    return text.strip('_')


def generate_analysis_description(config: Dict) -> str:
    """
    Génère une description courte basée sur les différences avec DEFAULT_CONFIG.
    
    Args:
        config: Configuration de l'analyse
        
    Returns:
        Description courte (max 50 caractères) ou "default" si aucune différence
    """
    parts = []
    
    # 1. Paramètres motifs (priorité haute)
    if config.get("list_itemset_min", [3])[0] != 3:
        parts.append(f"min{config['list_itemset_min'][0]}")
    
    gap_min = config.get("list_gap_min", [0])[0]
    gap_max = config.get("list_gap_max", [0])[0]
    if gap_min != 0 or gap_max != 0:
        parts.append(f"gap{gap_min}-{gap_max}")
    
    if config.get("list_minsup_percent", [25])[0] != 25:
        parts.append(f"sup{config['list_minsup_percent'][0]}pct")
    
    # 2. Analyses principales (priorité haute)
    if config.get("specifs", False):
        parts.append("specifs")
    
    if config.get("earlySelection", False):
        seuil = config.get("seuil_early_selection", 200)
        parts.append(f"early{seuil}")
    
    if not config.get("internal_clustering", True):
        parts.append("noclust")
    
    # 3. Attributs linguistiques (priorité moyenne)
    if config.get("Form", False):
        parts.append("form")
    
    if not config.get("Lemma", True):
        parts.append("nolemma")
    
    if not config.get("Pos", True):
        parts.append("nopos")
    
    if not config.get("Dep", True):
        parts.append("nodep")
    
    if config.get("Feats", False):
        parts.append("feats")
    
    # 3b. Annotateur (si différent de spacy par défaut)
    annotator = config.get("annotator", "spacy")
    if annotator != "spacy":
        # Raccourcir les noms pour la description
        annotator_short = {
            "stanza": "stz",
        }.get(annotator, annotator[:3])
        parts.append(annotator_short)
    
    # 4. Paramètres avancés early selection (priorité basse)
    if config.get("earlySelection", False):
        if config.get("filter_specifs", False):
            parts.append("earlySpecifs")
        
        partition = config.get("partition_cible", "test")
        if partition != "test":
            parts.append(f"part_{_slugify(partition)}")
        
        banal = config.get("seuil_banalité", 2)
        if banal != 2:
            parts.append(f"banal{banal}")
        
        early_pos = config.get("early_pos4lemma", "ADJ|NOUN|VERB")
        if early_pos != "ADJ|NOUN|VERB":
            parts.append("earlyPosCustom")
        
        if config.get("user_input_list", False):
            parts.append("earlyList")
    
    # 5. Seuils comparaison (priorité basse)
    if config.get("specifs", False):
        seuils_lemma = config.get("liste_seuils_lemma", [100, 200])
        if seuils_lemma != [100, 200]:
            parts.append(f"thLem{'-'.join(map(str, seuils_lemma))}")
        
        dh_pos = config.get("downhill_pos4lemma", "ADJ|ADV|NOUN|VERB")
        if dh_pos != "ADJ|ADV|NOUN|VERB":
            parts.append("dhPosCustom")
        
        seuils_big = config.get("liste_seuils_bigrams", [100])
        if seuils_big != [100]:
            parts.append(f"thBig{'-'.join(map(str, seuils_big))}")
    
    # 6. Metadata (priorité basse)
    list_meta = config.get("list_metadata", ["id"])
    if list_meta != ["id"] and len(list_meta) > 1:
        # Garder seulement colonnes non-id
        meta_cols = [col for col in list_meta if col != "id"]
        if meta_cols and len(meta_cols) <= 3:
            parts.append(f"meta_{'_'.join(_slugify(col) for col in meta_cols[:3])}")
        elif meta_cols:
            parts.append("meta")
    
    # 7. Langue (très rare)
    lang = config.get("language", "fr")
    if lang != "fr":
        parts.append(f"lang_{lang}")
    
    # 8. GPU (rare)
    if config.get("use_gpu", False):
        parts.append("gpu")
    
    # Si aucune différence, retourner "default"
    if not parts:
        return "default"
    
    # Joindre les parties et limiter à 50 caractères
    description = "_".join(parts)
    
    if len(description) > 50:
        # Tronquer et ajouter "+" pour indiquer troncature
        description = description[:49] + "+"
    
    return description


def generate_analysis_id(config: Dict) -> str:
    """
    Génère un ID d'analyse au format: YYYYMMDD_HHMMSS_description
    
    Args:
        config: Configuration de l'analyse
        
    Returns:
        ID unique avec timestamp et description
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    description = generate_analysis_description(config)
    return f"{timestamp}_{description}"


def parse_analysis_id(analysis_id: str) -> dict:
    """
    Parse un ID d'analyse pour extraire timestamp et description.
    
    Args:
        analysis_id: ID au format YYYYMMDD_HHMMSS_description
        
    Returns:
        Dict avec 'timestamp' (datetime ou None) et 'description' (str)
    """
    parts = analysis_id.split("_", 2)
    
    result = {
        "timestamp": None,
        "description": analysis_id  # Par défaut, tout est la description
    }
    
    # Essayer de parser le timestamp
    if len(parts) >= 2:
        try:
            timestamp_str = f"{parts[0]}_{parts[1]}"
            result["timestamp"] = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            result["description"] = parts[2] if len(parts) > 2 else "default"
        except ValueError:
            # Pas un timestamp valide, garder comme description
            pass
    
    return result
