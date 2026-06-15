"""
Last updated on XXX

@author: Dumoulin, H & Premat, T.
Based on scripts by Jade Mekki 2022
Modified by JcharlesDS (2026)
"""


import os
import sys
import formate_patterns
import conll_dmt4
import compute_emergent_sequential_patterns
import compute_CQP
import time
import shutil

import subprocess
import tools
import conllu2vrt
import cwb
import datetime
import early_selection
import pandas as pd
import execute_internal_clustering
import json
from pathlib import Path
import hashlib
import re
import zipfile

from replace_underscore import replace_underscore_in_conllu 

# Import de l'architecture d'annotation modulaire
from annotators import get_annotator

# Niveaux de log
LOG_ERROR = 0    # Erreurs critiques seulement
LOG_WARNING = 1  # Erreurs + avertissements
LOG_INFO = 2     # Erreurs + avertissements + étapes principales
LOG_DEBUG = 3    # Tout (détails de progression inclus)
LOG_TRACE = 4    # Traces très verbeuses / diagnostics techniques

# Mapping des niveaux UI vers niveaux internes
LOG_LEVEL_MAP = {
    "Minimal": LOG_ERROR,
    "Normal": LOG_INFO,
    "Détaillé": LOG_DEBUG,
    "Debug": LOG_TRACE
} 


class AnalysisCancelled(Exception):
    """Interruption propre demandée par l'utilisateur."""
    pass


class StdoutLogger:
    """Redirige stdout vers le callback de log."""
    def __init__(self, log_callback):
        self.log_callback = log_callback
        self.buffer = ""
        self.original_stdout = sys.stdout
        
    def write(self, text):
        if text and text.strip():
            if self.log_callback:
                self.log_callback(text.rstrip())
            else:
                self.original_stdout.write(text)
                
    def flush(self):
        pass
    
    def __enter__(self):
        sys.stdout = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        return False


def _slugify_cache_component(value: str) -> str:
    """Normalise une chaîne pour en faire un nom de dossier de cache."""
    text = (value or "").strip().lower()
    text = re.sub(r"[^a-z0-9._-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "default"


def _build_annotation_cache_key(path_corpus: str, annotator_tool: str, language: str, resolved_model_name: str) -> str:
    """Construit une clé stable pour mutualiser annotation et underscore_fix."""
    corpus_fingerprint = hashlib.md5(str(Path(path_corpus).resolve()).encode("utf-8")).hexdigest()[:10]
    model_part = _slugify_cache_component(resolved_model_name or f"{annotator_tool}_{language}")
    return f"{_slugify_cache_component(annotator_tool)}__{_slugify_cache_component(language)}__{model_part}__{corpus_fingerprint}"


def _copy_cached_conllu_files(cache_dir: str, destination_dir: str, textes: list[str], log_fn) -> int:
    """Copie les fichiers .conllu manquants depuis un cache partagé."""
    cache_path = Path(cache_dir)
    destination_path = Path(destination_dir)
    if not cache_path.exists():
        return 0

    copied = 0
    destination_path.mkdir(parents=True, exist_ok=True)
    for texte in textes:
        source = cache_path / f"{texte}.conllu"
        destination = destination_path / f"{texte}.conllu"
        if source.exists() and not destination.exists():
            shutil.copy2(source, destination)
            copied += 1
            log_fn(f"\t Cache partagé: réutilisation de {source.name}", LOG_DEBUG)
    return copied


def _update_shared_conllu_cache(source_dir: str, cache_dir: str, textes: list[str], log_fn) -> int:
    """Alimente le cache partagé avec les fichiers .conllu produits pour l'analyse."""
    source_path = Path(source_dir)
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    updated = 0
    for texte in textes:
        source = source_path / f"{texte}.conllu"
        destination = cache_path / f"{texte}.conllu"
        if source.exists() and not destination.exists():
            shutil.copy2(source, destination)
            updated += 1
            log_fn(f"\t Cache partagé mis à jour: {destination.name}", LOG_TRACE)
    return updated


def _copy_named_conllu_files(source_dir: str, destination_dir: str, textes: list[str], log_fn, origin_label: str) -> int:
    """Copie les .conllu manquants correspondant aux ids du corpus."""
    source_path = Path(source_dir)
    destination_path = Path(destination_dir)
    if not source_path.exists():
        return 0

    destination_path.mkdir(parents=True, exist_ok=True)
    copied = 0
    for texte in textes:
        source = source_path / f"{texte}.conllu"
        destination = destination_path / f"{texte}.conllu"
        if source.exists() and not destination.exists():
            shutil.copy2(source, destination)
            copied += 1
            log_fn(f"\t {origin_label}: réutilisation de {source.name}", LOG_DEBUG)
    return copied


def _prepare_extraction_dir(extract_dir: str):
    """Recrée proprement le dossier d'extraction d'une archive importée."""
    if not extract_dir:
        raise ValueError("Dossier d'extraction de l'archive préparée manquant.")
    extract_path = Path(extract_dir)
    if extract_path.exists():
        shutil.rmtree(extract_path)
    extract_path.mkdir(parents=True, exist_ok=True)


def _find_prepared_conllu_directories(root_dir: str) -> tuple[Path | None, Path | None]:
    """Détecte les dossiers .conllu annotés et underscore_fix dans une archive extraite."""
    root_path = Path(root_dir)
    if not root_path.exists():
        return None, None

    candidates: list[tuple[Path, int, bool]] = []
    for current_root, _dirs, files in os.walk(root_path):
        conllu_count = sum(1 for file_name in files if file_name.endswith(".conllu"))
        if conllu_count <= 0:
            continue
        current_path = Path(current_root)
        path_parts = {part.lower() for part in current_path.parts}
        is_underscore = any("underscore_fix" in part for part in path_parts)
        candidates.append((current_path, conllu_count, is_underscore))

    if not candidates:
        return None, None

    underscore_candidates = [item for item in candidates if item[2]]
    regular_candidates = [item for item in candidates if not item[2]]

    underscore_dir = max(underscore_candidates, key=lambda item: item[1])[0] if underscore_candidates else None
    annotated_dir = max(regular_candidates, key=lambda item: item[1])[0] if regular_candidates else None

    if annotated_dir is None and underscore_dir is not None:
        annotated_dir = underscore_dir

    return annotated_dir, underscore_dir


def _import_prepared_inputs(
    config: dict,
    textes: list[str],
    dir_tagged_stanza: str,
    dir_underscore_fix: str,
    prepared_import_dir: str,
    log_fn,
) -> tuple[int, int]:
    """Importe des données préparées fournies par l'utilisateur."""
    prepared_conllu_dir = (config.get("prepared_conllu_dir", "") or "").strip()
    prepared_archive_zip = (config.get("prepared_archive_zip", "") or "").strip()

    imported_tagged = 0
    imported_underscore = 0

    if prepared_conllu_dir:
        prepared_dir_path = Path(prepared_conllu_dir).expanduser()
        if prepared_dir_path.exists() and prepared_dir_path.is_dir():
            count = _copy_named_conllu_files(
                str(prepared_dir_path),
                dir_tagged_stanza,
                textes,
                log_fn,
                "Import .conllu",
            )
            if count:
                imported_tagged += count
                log_fn(f"Réutilisation de {count} fichier(s) depuis le dossier .conllu importé.", LOG_INFO)
        else:
            log_fn(f"⚠ Dossier .conllu importé introuvable: {prepared_dir_path}", LOG_WARNING)

    if prepared_archive_zip:
        archive_path = Path(prepared_archive_zip).expanduser()
        if archive_path.exists() and archive_path.is_file():
            try:
                _prepare_extraction_dir(prepared_import_dir)
                with zipfile.ZipFile(archive_path, "r") as archive:
                    archive.extractall(prepared_import_dir)
                log_fn(f"Archive préparée extraite: {archive_path.name}", LOG_INFO)

                annotated_dir, underscore_dir = _find_prepared_conllu_directories(prepared_import_dir)

                if annotated_dir is not None:
                    count = _copy_named_conllu_files(
                        str(annotated_dir),
                        dir_tagged_stanza,
                        textes,
                        log_fn,
                        "Archive préparée",
                    )
                    if count:
                        imported_tagged += count
                        log_fn(f"Réutilisation de {count} fichier(s) annoté(s) depuis l'archive.", LOG_INFO)

                if underscore_dir is not None:
                    count = _copy_named_conllu_files(
                        str(underscore_dir),
                        dir_underscore_fix,
                        textes,
                        log_fn,
                        "Archive underscore_fix",
                    )
                    if count:
                        imported_underscore += count
                        log_fn(f"Réutilisation de {count} fichier(s) underscore_fix depuis l'archive.", LOG_INFO)

                    backfill_count = _copy_named_conllu_files(
                        str(underscore_dir),
                        dir_tagged_stanza,
                        textes,
                        log_fn,
                        "Archive underscore_fix",
                    )
                    imported_tagged += backfill_count

                if annotated_dir is None and underscore_dir is None:
                    log_fn(
                        "⚠ L'archive préparée ne contient pas de dossier .conllu exploitable.",
                        LOG_WARNING,
                    )
            except zipfile.BadZipFile:
                log_fn(f"⚠ Archive ZIP invalide: {archive_path}", LOG_WARNING)
            except Exception as exc:
                log_fn(f"⚠ Erreur lors de l'import de l'archive préparée: {exc}", LOG_WARNING)
        else:
            log_fn(f"⚠ Archive préparée introuvable: {archive_path}", LOG_WARNING)

    return imported_tagged, imported_underscore


def format_time(seconds):
    """Formate un temps en secondes vers heures:minutes ou minutes."""
    if seconds < 60:
        return f"{seconds:.2f} secondes"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.2f} minutes"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours}h{mins:02d}min"


def is_valid_timestamp_filename(filename):
    """
    Vérifie si le nom de fichier contient un timestamp au bon format (YYYYMMDD_HHMMSS).
    Ignore les fichiers avec des timestamps contenant espaces, tirets ou points (ancien format).
    """
    import re
    # Rejeter les fichiers avec timestamp au mauvais format (espaces, tirets, points multiples)
    if re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:', filename):
        return False
    # Accepter les fichiers avec timestamp au bon format (YYYYMMDD_HHMMSS)
    if re.search(r'\d{8}_\d{6}', filename):
        return True
    return True  # Accepter les autres fichiers par défaut


def run_analysis(config, progress_callback=None, log_callback=None, paths=None, cancel_callback=None):
    """
    Lance l'analyse complète.

    Args:
        config (dict): Contient toutes les variables de configuration nécessaires à l'exécution de l'analyse.
        progress_callback (callable, optional): Fonction de rappel pour suivre la progression. Defaults to None.
        log_callback (callable, optional): Fonction de rappel pour enregistrer les logs. Defaults to None.
        paths (dict, optional): Dictionnaire contenant les chemins pour l'organisation par corpus/config. Defaults to None.
    """
    # Démarrer le chronomètre pour le temps total
    start_time_total = time.time()
    
    # Ajouter ./bin au PATH pour que les scripts Perl trouvent les wrappers CWB Docker
    bin_path = os.path.abspath("./bin")
    os.environ["PATH"] = f"{bin_path}:{os.environ.get('PATH', '')}"
    
    # Définir les chemins (système organisé par analyse)
    # Les paths doivent toujours être fournis maintenant
    if not paths:
        raise ValueError("Le système d'analyse nécessite la structure paths. Utilisez l'interface GUI ou fournissez les chemins.")
    
    # Organisation par corpus/config
    dir_tagged_stanza = str(paths["tagged_stanza"])
    dir_tagged_for_dmt4 = str(paths["tagged_for_dmt4"])
    dir_textes_vrt = str(paths["textes_vrt"])
    # Chaque analyse a son propre corpus CWB pour garantir la cohérence
    dir_cwb_corpus = str(paths["cwb_corpus"])
    dir_dmt4_files = str(paths["dmt4_files"])
    dir_lexiques = str(paths["lexiques"])
    dir_clustering_results = str(paths["clustering_results"])
    dir_patterns_results = str(paths["patterns_results"])
    # Les logs sont toujours écrits dans ./logs/ à la racine du projet
    dir_logs = "./logs"
    dir_underscore_fix = str(paths["underscore_fix"])
    prepared_import_dir = str(paths.get("prepared_import", "")) if paths.get("prepared_import") else ""
    shared_cache_root = str(paths.get("shared_cache_root", "")) if paths.get("shared_cache_root") else ""
    dir_early_selection = str(paths.get("early_selection", "")) if paths.get("early_selection") else ""
    # Chemins source (ne changent pas)
    dir_textes_raw = config.get("path_corpus", "./Data/Corpus/Textes_raw")
    path_metadata = str(paths.get("path_metadata", f"{dir_textes_raw}/metadata.tsv"))
    
    # Définir le chemin du registry CWB pour cette analyse
    registry_path = f"{dir_cwb_corpus}/registry"
    
    # Définir la variable d'environnement pour que les scripts Perl trouvent le corpus
    os.environ["CORPUS_REGISTRY_PATH"] = registry_path
    
    # Charger le niveau de verbosité depuis app_settings.json
    current_log_level = LOG_INFO  # Défaut: Normal
    try:
        settings_file = Path("app_settings.json")
        if settings_file.exists():
            with open(settings_file, "r", encoding="utf-8") as f:
                app_settings = json.load(f)
                log_level_ui = app_settings.get("log_level", "Normal")
                current_log_level = LOG_LEVEL_MAP.get(log_level_ui, LOG_INFO)
    except Exception:
        pass  # En cas d'erreur, utiliser le niveau par défaut
    
    def _log(msg, level=LOG_INFO):
        """
        Enregistre un message de log si son niveau est <= au niveau configuré.
        
        Args:
            msg: Message à enregistrer
            level: Niveau du message (LOG_ERROR, LOG_WARNING, LOG_INFO, LOG_DEBUG)
        """
        if level <= current_log_level:
            if log_callback:
                log_callback(msg)
            else:
                print(msg)

    def _infer_log_level(message: str) -> int:
        """Déduit un niveau de verbosité approximatif pour les messages externes."""
        text = (message or "").strip()
        lower = text.lower()

        if not text:
            return LOG_DEBUG

        if (
            "erreur" in lower
            or "[erreur]" in lower
            or "traceback" in lower
            or "exception" in lower
            or ("failed" in lower and "fallback" not in lower and "bascule" not in lower)
        ):
            return LOG_ERROR

        if (
            "warning" in lower
            or "⚠" in text
            or "avertissement" in lower
            or "echec" in lower
            or "échec" in lower
            or "bascule sur docker" in lower
            or "fallback" in lower
        ):
            return LOG_WARNING

        if (
            "[debug]" in lower
            or lower.startswith("[cwb] backend")
            or lower.startswith("[cwb] registry")
            or lower.startswith("[cwb] arguments:")
            or lower.startswith("[cwb] stderr local:")
            or lower.startswith("[cwb] stdout local:")
            or "binaire cwb-" in lower
            or "verification dossier" in lower
            or "cwd local" in lower
            or "is_dir" in lower
            or lower.startswith("indexing ")
            or lower == "index done"
            or lower.startswith("computing ")
            or lower.startswith("transforming conllu")
            or lower.startswith("vrt file already exists")
            or lower.startswith("re-using ")
            or lower.startswith("results : saved")
            or lower.startswith("file_out_")
            or lower.startswith("[fusion]")
        ):
            return LOG_TRACE

        return LOG_INFO

    def _route_external_log(message: str):
        """Fait passer les messages externes dans le même filtre de verbosité."""
        _log(message, _infer_log_level(message))
    
    def _progress(etape, pct):
        if progress_callback:
            progress_callback(etape, pct)

    def _check_cancelled():
        if callable(cancel_callback) and cancel_callback():
            raise AnalysisCancelled("Analyse arrêtée par l'utilisateur.")
    
    # Configuration
    annotator_tool = config.get("annotator_tool", "spacy")
    use_gpu = config.get("use_gpu", True)
    language = config.get("language", "fr")
    earlySelection = config.get("earlySelection", False)
    seuil_early_selection = config.get("seuil_early_selection", 200)
    filter_specifs = config.get("filter_specifs", False)
    partition_cible = config.get("partition_cible", "test")
    seuil_banalité = config.get("seuil_banalité", 2)
    early_pos4lemma = (config.get("early_pos4lemma", "ADJ|NOUN|VERB") or "").strip() or ".*"
    user_input_list = config.get("user_input_list", False)
    liste_earlyselection_lemma = config.get("liste_earlyselection_lemma", [])
    internal_clustering = config.get("internal_clustering", True)
    list_itemset_min = config.get("list_itemset_min", [3])
    list_gap_min = config.get("list_gap_min", [0])
    list_gap_max = config.get("list_gap_max", [0])
    list_minsup_percent = config.get("list_minsup_percent", [25])
    threads = config.get("threads", 30)
    Form = config.get("Form", False)
    Lemma = config.get("Lemma", True)
    Pos = config.get("Pos", True)
    Dep = config.get("Dep", True)
    Feats = config.get("Feats", False)
    list_metadata = config.get("list_metadata", ["id"])
    specifs = config.get("specifs", False)
    liste_seuils_lemma = config.get("liste_seuils_lemma", [100, 200])
    downhill_pos4lemma = config.get("downhill_pos4lemma", "ADJ|ADV|NOUN|VERB")
    liste_seuils_bigrams = config.get("liste_seuils_bigrams", [100])
    mode = config.get("mode", "")

    python = "python3.7"
    
    # ==================================
    # 1 - Annotation des données
    # ==================================
    
    _log("-"*75, LOG_INFO)
    _log("1. Annotation des données", LOG_INFO)
    _progress(f"Annotation ({annotator_tool.upper()})", 0)
    _log(f"1.1. Annotation des données avec {annotator_tool.upper()}: POS, lemma, UD", LOG_INFO)
    _check_cancelled()
    
    textes = os.listdir(dir_textes_raw)
    # Exclure les fichiers système et metadata.tsv
    if ".DS_Store" in textes:
        textes.remove(".DS_Store")
    if "metadata.tsv" in textes:
        textes.remove("metadata.tsv")
    textes = [item[:-4] for item in textes]
    
    start_time = time.time()
    
    # Initialiser l'annotateur sélectionné
    try:
        annotator = get_annotator(annotator_tool)
        annotator.set_log_callback(_route_external_log)
    except ValueError as e:
        _log(f"ERREUR: {e}", LOG_ERROR)
        raise
    
    # Vérifier que l'outil est installé
    if not annotator.check_installation():
        error_msg = annotator.get_installation_instructions()
        _log(f"ERREUR: {error_msg}", LOG_ERROR)
        raise RuntimeError(error_msg)
    
    # Vérifier/télécharger les modèles
    _log(f"Vérification des modèles {annotator.get_name()}...", LOG_INFO)
    # Pour spaCy, passer use_gpu pour sélectionner le bon modèle (trf si GPU, lg si CPU).
    if annotator_tool == "spacy":
        check_result = annotator.check_models(language, use_gpu=use_gpu)
    else:
        check_result = annotator.check_models(language)
    
    if not check_result:
        _log(f"ERREUR: Impossible de charger les modèles pour '{language}'", LOG_ERROR)
        raise RuntimeError(f"Modèles {annotator.get_name()} manquants pour '{language}'")

    resolved_model_name = annotator.get_resolved_model_name(language, use_gpu=use_gpu)
    if resolved_model_name:
        config["_resolved_annotator_model"] = resolved_model_name
        _log(f"Modèle NLP retenu : {resolved_model_name}", LOG_INFO)
    elif annotator_tool == "stanza":
        config["_resolved_annotator_model"] = (
            f"Pipeline Stanza ({language}, {'GPU' if use_gpu else 'CPU'})"
        )
    
    _log(f"✓ Modèles {annotator.get_name()} pour '{language}' prêts.", LOG_INFO)

    annotation_cache_dir = ""
    underscore_cache_dir = ""
    if shared_cache_root:
        cache_key = _build_annotation_cache_key(
            config.get("path_corpus", dir_textes_raw),
            annotator_tool,
            language,
            config.get("_resolved_annotator_model", ""),
        )
        annotation_cache_dir = str(Path(shared_cache_root) / "annotation" / cache_key)
        underscore_cache_dir = str(Path(shared_cache_root) / "underscore_fix" / cache_key)
        _log(f"Cache d'annotation partagé : {cache_key}", LOG_DEBUG)
    
    if not os.path.exists(dir_tagged_stanza):
        os.makedirs(dir_tagged_stanza, exist_ok=True)
    if not os.path.exists(dir_underscore_fix):
        os.makedirs(dir_underscore_fix, exist_ok=True)

    imported_tagged_count, imported_underscore_count = _import_prepared_inputs(
        config,
        textes,
        dir_tagged_stanza,
        dir_underscore_fix,
        prepared_import_dir,
        _log,
    )
    if imported_tagged_count or imported_underscore_count:
        _log(
            "Données préparées importées : "
            f"{imported_tagged_count} annoté(s), {imported_underscore_count} underscore_fix.",
            LOG_INFO,
        )

    if annotation_cache_dir:
        reused_count = _copy_cached_conllu_files(annotation_cache_dir, dir_tagged_stanza, textes, _log)
        if reused_count:
            _log(f"Réutilisation de {reused_count} fichier(s) annoté(s) depuis le cache partagé.", LOG_INFO)
    
    # Identifier les fichiers à annoter
    tagging_list = {}
    tag = False
    for texte in textes:
        _check_cancelled()
        output_file = f"{dir_tagged_stanza}/{texte}.conllu"
        if os.path.exists(output_file):
            _log(f"\t {annotator.get_name()}: {output_file} existe déjà.", LOG_DEBUG)
        else:
            _log(f"\t {annotator.get_name()}: {output_file} n'existe pas. Annotation en cours...", LOG_INFO)
            file_path = f"{dir_textes_raw}/{texte}.txt"
            tagging_list[texte] = (file_path, output_file)
            tag = True
    
    # Annoter les fichiers manquants
    if tag:
        total = len(tagging_list)
        for i, (texte, (file_path, output_file)) in enumerate(tagging_list.items()):
            _check_cancelled()
            try:
                annotator.annotate_file(file_path, output_file, language, use_gpu)
                _log(f"\t [{i+1}/{total}] {texte} annoté et sauvegardé: {output_file}", LOG_DEBUG)
            except Exception as e:
                _log(f"Erreur lors de l'annotation de {texte}: {e}", LOG_ERROR)
                raise
            _progress(f"Annotation ({annotator_tool.upper()})", int((i+1) / total * 15))
        if annotation_cache_dir:
            updated_count = _update_shared_conllu_cache(dir_tagged_stanza, annotation_cache_dir, list(tagging_list.keys()), _log)
            if updated_count:
                _log(f"Cache partagé d'annotation enrichi avec {updated_count} fichier(s).", LOG_DEBUG)
    elif annotation_cache_dir:
        _log("Tous les fichiers annotés requis étaient déjà disponibles localement ou via le cache partagé.", LOG_INFO)
    
    end_time = time.time()
    time_tag = end_time - start_time
    
    # Correction des underscores
    if underscore_cache_dir:
        reused_underscore_count = _copy_cached_conllu_files(underscore_cache_dir, dir_underscore_fix, textes, _log)
        if reused_underscore_count:
            _log(f"Réutilisation de {reused_underscore_count} fichier(s) underscore_fix depuis le cache partagé.", LOG_INFO)
    
    total_textes = len(textes)
    for idx, texte in enumerate(textes, start=1):
        _check_cancelled()
        output_file = f"{dir_underscore_fix}/{texte}.conllu"
        if os.path.exists(output_file):
            _log(f"\t [{idx}/{total_textes}] La correction des underscores a déjà été effectuée pour {texte}.", LOG_DEBUG)
        else:
            _log(f"\t [{idx}/{total_textes}] Underscore_fix : {texte}", LOG_DEBUG)
            destination = dir_underscore_fix
            source = f"{dir_tagged_stanza}/{texte}.conllu"
            shutil.copy(source, destination)
            replace_underscore_in_conllu(output_file)

    if underscore_cache_dir:
        updated_underscore_count = _update_shared_conllu_cache(dir_underscore_fix, underscore_cache_dir, textes, _log)
        if updated_underscore_count:
            _log(f"Cache partagé underscore_fix enrichi avec {updated_underscore_count} fichier(s).", LOG_DEBUG)
    

    # ==================================
    # 2 - Fichiers DMT4
    # ==================================
    
    _log("-" * 75, LOG_INFO)
    _log("2. Création des fichiers DMT4", LOG_INFO)
    _progress("Création fichiers DMT4", 15)
    _check_cancelled()
    
    # Créer ou nettoyer le dossier DMT4
    dmt4_prep_dir = dir_tagged_for_dmt4
    if os.path.exists(dmt4_prep_dir):
        _log("\t DMT4: Nettoyage du dossier existant...", LOG_DEBUG)
        # Supprimer les fichiers temporaires (merged, etc.)
        for f in os.listdir(dmt4_prep_dir):
            _check_cancelled()
            if not f.endswith('.conllu'):
                os.remove(os.path.join(dmt4_prep_dir, f))
    else:
        os.makedirs(dmt4_prep_dir, exist_ok=True)
    
    # Copier les fichiers CoNLL-U
    _log("\t DMT4: Copie des fichiers CoNLL-U...", LOG_DEBUG)
    for texte in textes:
        _check_cancelled()
        destination = dmt4_prep_dir
        source = f"{dir_underscore_fix}/{texte}.conllu"
        dest_file = os.path.join(destination, f"{texte}.conllu")
        if not os.path.exists(dest_file):
            shutil.copy(source, destination)
            _log(f"\t\t Copie: {texte}.conllu", LOG_DEBUG)
    
    liste_textes = ["merged"]
    dmt4_merged_sorted = f"{dir_dmt4_files}/DMT4_merged_files_sorted.txt"
    
    if os.path.exists(dmt4_merged_sorted):
        _log("\t Le fichier DMT4 trié existe déjà.", LOG_DEBUG)
    else:
        if not os.path.exists(dir_dmt4_files):
            os.makedirs(dir_dmt4_files, exist_ok=True)
        _log("\t DMT4: Création du fichier DMT4.", LOG_INFO)
        # S'assurer que le chemin se termine par / pour les fonctions de concaténation
        dmt4_prep_dir_slash = dmt4_prep_dir.rstrip("/") + "/"
        with StdoutLogger(_route_external_log):
            conll_dmt4.instancier_dict(dmt4_prep_dir_slash, dir_lexiques)
        # Ne sélectionner que les fichiers .conllu
        path = dmt4_prep_dir_slash
        file_list = [f for f in os.listdir(dmt4_prep_dir) if f.endswith('.conllu')]
        _log(f"\t DMT4: Concaténation de {len(file_list)} fichiers...", LOG_DEBUG)
        with StdoutLogger(_route_external_log):
            tools.concat_multiple_conll(path, file_list, "merged")
        for texte in liste_textes:
            _check_cancelled()
            with StdoutLogger(_route_external_log):
                conll_dmt4.transform_data(dmt4_prep_dir_slash, texte, Form, Lemma, Pos, Dep, Feats, dir_dmt4_files, dir_lexiques)
        # S'assurer que le chemin se termine par / pour sort_dmtfiles
        dir_dmt4_files_slash = dir_dmt4_files.rstrip("/") + "/"
        with StdoutLogger(_route_external_log):
            conll_dmt4.sort_dmtfiles(dir_dmt4_files_slash)
        for texte in liste_textes:
            _check_cancelled()
            with StdoutLogger(_route_external_log):
                conll_dmt4.make_DMT4_file(texte, dir_dmt4_files)
    
    _check_cancelled()
    path_stanza = dir_tagged_stanza.rstrip("/") + "/"
    path_vrt = dir_textes_vrt.rstrip("/") + "/"
    with StdoutLogger(_route_external_log):
        conllu2vrt.transform(path_stanza, path_vrt)
    
    # Vérifier si le corpus CWB existe, sinon l'encoder
    cwb_registry = f"{dir_cwb_corpus}/registry/merged"
    if not os.path.exists(cwb_registry):
        _log("Encodage du corpus CWB pour cette analyse...", LOG_INFO)
        os.makedirs(dir_cwb_corpus, exist_ok=True)
        with StdoutLogger(_route_external_log):
            cwb.main(dir_textes_vrt=dir_textes_vrt, dir_cwb_corpus=dir_cwb_corpus)
        
    if user_input_list and earlySelection:
        _log("2.1 Early Selection ignorée : la liste manuelle de lemmes est activée.", LOG_INFO)
    elif earlySelection:
        _check_cancelled()
        _log("-" * 75, LOG_INFO)
        _log("2.1 Early Selection du lemme pour la recherche", LOG_INFO)
        # Passer les chemins à early_selection pour éviter qu'il écrive dans Data/
        with StdoutLogger(_route_external_log):
            liste_earlyselection_lemma = early_selection.main(
                seuil_early_selection, list_minsup_percent[0] if list_minsup_percent else 25, path_metadata, partition_cible, 
                seuil_banalité, early_pos4lemma, filter_specifs,
                dir_early_selection=dir_early_selection,
                dir_lexiques=dir_lexiques,
                registry_path=registry_path
            )
        
    if user_input_list:
        path_lexique = f"{dir_lexiques}/dico_str_to_int_all_items.pk"
        lexique = tools.load_pickles(path_lexique)
        nom = f"user_input_{time.time()}"
        if dir_early_selection:
            os.makedirs(dir_early_selection, exist_ok=True)
            with open(f"{dir_early_selection}/{nom}.txt", "w") as f:
                f.write(str(liste_earlyselection_lemma))
        liste_lemma = []
        lignes = liste_earlyselection_lemma
        _log(str(lignes), LOG_DEBUG)
        for l in lignes:
            _check_cancelled()
            lemma_preformat = f'lemma_"{l}"'
            liste_lemma.append(lexique[lemma_preformat])
        
    # ==================================
    # 3 - Extraction des motifs
    # ==================================
    
    _log("-" * 75, LOG_INFO)
    _log("3. Extraction des motifs fréquents et clos", LOG_INFO)
    _progress("Fouille de motifs (BideSpanTree)", 30)
    start_time = time.time()
    _check_cancelled()
    
    path_results = dir_patterns_results
    if not os.path.exists(path_results):
        os.makedirs(path_results, exist_ok=True)
    path_file_closed = f"{dir_patterns_results}/Closed"
    if not os.path.exists(path_file_closed):
        os.makedirs(path_file_closed, exist_ok=True)
    
    for nb_itemset_min in list_itemset_min:
        _check_cancelled()
        for gap_min in list_gap_min:
            _check_cancelled()
            for gap_max in list_gap_max:
                _check_cancelled()
                for minsup_percent in list_minsup_percent:
                    _check_cancelled()
                    args = f"{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}"
                    if user_input_list:
                        args = f"user_input_list_{nom}_{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}"
                    if earlySelection:
                        args = f"{seuil_early_selection}early{early_pos4lemma}_specifs{filter_specifs}{partition_cible}_{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}"
                    args = args.replace("|", "-")
                    
                    if os.path.exists(f"{dir_patterns_results}/Closed/{args}_DMT4_merged_files_sorted_closed.txt"):
                        _log(f"\t Le fichier de motifs clos existe déjà pour {args}.", LOG_DEBUG)
                    else:
                        dmt4_files = f"{dir_dmt4_files}/DMT4_merged_files_sorted.txt"
                        
                        # Vérifier que le fichier DMT4 trié existe
                        if not os.path.exists(dmt4_files):
                            raise FileNotFoundError(
                                f"Le fichier DMT4 trié est manquant: {dmt4_files}\n"
                                f"Les fichiers DMT4 doivent être générés avant l'extraction de motifs.\n"
                                f"Vérifiez que l'étape de préparation DMT4 s'est correctement déroulée."
                            )
                        
                        minsup = tools.get_minsup(float(minsup_percent), dmt4_files)
                        _log(f"\t Nombre d'itemsets minimum {nb_itemset_min} ", LOG_DEBUG)
                        _log(f"\t Gap minimum {gap_min} ", LOG_DEBUG)
                        _log(f"\t Gap maximum {gap_max} ", LOG_DEBUG)
                        _log(f"\t Minimum Support {minsup_percent}% ", LOG_INFO)
                        
                        # Vérifier la taille du fichier DMT4
                        dmt4_size = os.path.getsize(dmt4_files)
                        _log(f"\t Fichier DMT4: {dmt4_files} ({dmt4_size} bytes)", LOG_DEBUG)
                        
                        file_out = f"{args}_DMT4_merged_files_sorted_closed.txt"
                        
                        _log("\t\t Extraction des motifs clos", LOG_INFO)
                
                        # Utiliser un chemin absolu pour le corpus dans Load.ini
                        dmt4_files_abs = os.path.abspath(dmt4_files)
                        
                        with open("BideSpanTree/bin/Load.ini", "w", encoding="utf8") as set_up:
                            set_up.write(f"MINSUP={minsup}\n")
                            set_up.write(f"CORPUS={dmt4_files_abs}\n")
                            set_up.write(f"THREAD={threads}\n")
                            set_up.write(f"GAPMIN={gap_min}\n")
                            set_up.write(f"GAPMAX={gap_max}\n")
                            set_up.write(f"NB_ITEMSET_MIN={nb_itemset_min}\n")
                            if user_input_list:
                                set_up.write(f"OR={str(liste_lemma)[1:-1]}\n")
                            if earlySelection:
                                set_up.write(f"OR={str(liste_earlyselection_lemma)[1:-1]}\n")
                        
                        # Fichier Load.ini fermé, maintenant on peut exécuter le binaire
                        try:
                            # Essayer d'abord le binaire directement (Linux/Mac)
                            output_path = f"{dir_patterns_results}/Closed/{file_out}"
                            # Convertir en chemin absolu
                            output_path_abs = os.path.abspath(output_path)
                            
                            _log("\t\t Tentative d'exécution directe du binaire...", LOG_DEBUG)
                            # Obtenir le répertoire racine du projet (parent de src/)
                            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                            # Exécuter depuis BideSpanTree/bin/ où Load.ini est présent
                            bidespantree_bin_dir = os.path.join(project_root, "BideSpanTree", "bin")
                            # Créer le répertoire de sortie
                            os.makedirs(os.path.dirname(output_path_abs), exist_ok=True)
                            # Exécuter le binaire et rediriger stdout vers le fichier de résultats
                            with open(output_path_abs, "w", encoding="utf-8") as output_file:
                                result = subprocess.run(
                                    ["./bidespantree"],
                                    check=True,
                                    stdout=output_file,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    cwd=bidespantree_bin_dir,
                                )
                            _log("\t\t ✓ Exécution directe réussie", LOG_INFO)
                            # Vérifier la taille du fichier de résultats
                            result_size = os.path.getsize(output_path_abs)
                            _log(f"\t\t Fichier de résultats: {output_path} ({result_size} bytes)", LOG_DEBUG)
                            if result_size == 0:
                                _log(f"\t\t ⚠ ATTENTION: Le fichier de résultats est vide!", LOG_WARNING)
                                if result.stderr:
                                    _log(f"\t\t Stderr: {result.stderr}", LOG_DEBUG)
                        except (FileNotFoundError, subprocess.CalledProcessError, PermissionError, OSError) as e:
                            # Si direct échoue, essayer Docker
                            _log(f"\t\t Exécution directe impossible ({type(e).__name__}), tentative avec Docker...", LOG_DEBUG)
                            try:
                                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                subprocess.run(
                                    ["docker", "run", "--rm", "--platform", "linux/amd64",
                                     "-v", f"{base_dir}:/data",
                                     "ubuntu:22.04",
                                     "bash", "-c",
                                     f"cd /data/BideSpanTree/bin && chmod +x bidespantree && ./bidespantree > /data/Patterns_results/Closed/{file_out}"],
                                    check=True,
                                    capture_output=True,
                                    text=True,
                                )
                                _log("\t\t ✓ Exécution avec Docker réussie", LOG_INFO)
                            except (FileNotFoundError, subprocess.CalledProcessError, OSError, PermissionError) as docker_err:
                                error_msg = docker_err.stderr if hasattr(docker_err, 'stderr') and docker_err.stderr else str(docker_err)
                                _log(f"\t\t ✗ Docker échoue aussi: {error_msg}", LOG_ERROR)
                                
                                # Vérifier si c'est un problème de permissions Docker
                                if "permission denied" in error_msg.lower() or "docker" in error_msg.lower():
                                    raise RuntimeError(
                                        "Impossible d'exécuter BideSpanTree:\n"
                                        "  1. Le binaire direct n'a pas fonctionné\n"
                                        "  2. Docker n'est pas accessible (problème de permissions)\n"
                                        "  \n"
                                        "Pour corriger sur Linux:\n"
                                        "  sudo usermod -aG docker $USER\n"
                                        "  # Puis se déconnecter et se reconnecter\n"
                                        "  newgrp docker\n"
                                        "  \n"
                                        "Ou sur Mac/Windows:\n"
                                        "  Installez Docker Desktop et démarrez-le"
                                    )
                                else:
                                    raise RuntimeError(
                                        "Impossible d'exécuter BideSpanTree:\n"
                                        "  1. Le binaire direct n'a pas fonctionné\n"
                                        "  2. Docker n'est pas disponible\n"
                                        "  \n"
                                        f"Erreur Docker: {error_msg}"
                                    )
                        except Exception as e:
                            _log(f"Erreur lors de l'extraction des motifs: {str(e)}", LOG_ERROR)

        end_time = time.time()
        time_DMT4 = end_time - start_time
    
    # ========================================
    # 4 - Calcul des motifs caractéristiques
    # ========================================
    
    _log("-" * 75, LOG_INFO)
    _log("4. Extraction des motifs caractéristiques", LOG_INFO)
    _progress("Calcul des motifs caractéristiques", 55)
    _check_cancelled()
    
    rep_clos = f"{dir_patterns_results}/Closed/"
    for f_clos in os.listdir(rep_clos):
        _check_cancelled()
        if "txt" not in f_clos:
            continue
        with StdoutLogger(_route_external_log):
            compute_emergent_sequential_patterns.from_txt_to_dict(os.path.join(rep_clos, f_clos))
    
    
    # ================================
    # 4.bis - Clustering interne
    # ================================
    
    if internal_clustering:
        _progress("Clustering interne", 60)
        start_time = time.time()
        _check_cancelled()
        for d in [dir_clustering_results, f"{dir_clustering_results}/Clusters", f"{dir_clustering_results}/Medoids"]:
            if not os.path.exists(d):
                os.makedirs(d, exist_ok=True)
        nbr_pool = 10
        for nb_itemset_min in list_itemset_min:
            _check_cancelled()
            for gap_min in list_gap_min:
                _check_cancelled()
                for gap_max in list_gap_max:
                    _check_cancelled()
                    for minsup_percent in list_minsup_percent:
                        _check_cancelled()
                        # Vérifier que le fichier des motifs clos existe et n'est pas vide
                        closed_pattern_file = f"{dir_patterns_results}/Closed/{args}_DMT4_merged_files_sorted_closed.pk"
                        if not os.path.exists(closed_pattern_file):
                            _log(f"⚠ Fichier de motifs clos manquant: {closed_pattern_file}", LOG_WARNING)
                            _log("Le clustering ne peut pas être effectué sans motifs clos.", LOG_WARNING)
                            continue
                        
                        file_size = os.path.getsize(closed_pattern_file)
                        _log(f"Fichier de motifs clos: {closed_pattern_file} ({file_size} bytes)", LOG_DEBUG)
                        
                        if not os.path.exists(f"{dir_clustering_results}/Clusters/{args}_clustering_3.pk"):
                            _log("Exécution du clustering interne...", LOG_INFO)
                            # Rediriger stdout pour capturer les outputs du clustering
                            import io
                            import sys
                            old_stdout = sys.stdout
                            sys.stdout = io.StringIO()
                            try:
                                execute_internal_clustering.main(nbr_pool, args, dir_clustering_results, dir_patterns_results)
                                clustering_output = sys.stdout.getvalue()
                                # Rediriger chaque ligne vers le log
                                for line in clustering_output.split('\n'):
                                    if line.strip():
                                        _log(line, LOG_DEBUG)
                            finally:
                                sys.stdout = old_stdout
                        else:
                            _log("-" * 75, LOG_DEBUG)
                            _log("4.bis Clustering interne : fichier de clusters déjà existant.", LOG_DEBUG)
                            
        end_time = time.time()
        time_clustering = end_time - start_time
    
    # ==================================
    # 5 - Calcul statistiques (CQP + R)
    # ==================================
    
    _progress("Calcul statistiques (CQP + R)", 75)
    start_time = time.time()
    _check_cancelled()
    for d in [f"{dir_patterns_results}/Specifs/", f"{dir_patterns_results}/R"]:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
    _log("-" * 75, LOG_INFO)
    _log("5. Calcul statistique des motifs caractéristiques", LOG_INFO)
    
    # Rediriger stdout vers le log pour capturer les messages des scripts
    with StdoutLogger(_route_external_log):
        df_metadata = pd.read_csv(path_metadata, sep="\t", index_col=0)
        results = {}
        
        modif = ""
        if user_input_list:
            modif = f"user_input_list_{nom}_"
        if earlySelection:
            modif = f"{seuil_early_selection}early{early_pos4lemma}_specifs{filter_specifs}{partition_cible}_"
        if internal_clustering:
            modif = modif + "internal_clustering_"
        
        for metadata in list_metadata:
            _check_cancelled()
            for nb_itemset_min in list_itemset_min:
                _check_cancelled()
                for gap_min in list_gap_min:
                    _check_cancelled()
                    for gap_max in list_gap_max:
                        _check_cancelled()
                        path_R = f"{dir_patterns_results}/R/{metadata}/{modif}motifs/itemset_min{nb_itemset_min}/gap_min{gap_min}_gap_max{gap_max}/"
                        if not os.path.exists(path_R):
                            for sub in [f"{dir_patterns_results}/R/",
                                        f"{dir_patterns_results}/R/{metadata}/",
                                        f"{dir_patterns_results}/R/{metadata}/{modif}motifs/",
                                        f"{dir_patterns_results}/R/{metadata}/{modif}motifs/itemset_min{nb_itemset_min}/",
                                        f"{dir_patterns_results}/R/{metadata}/{modif}motifs/itemset_min{nb_itemset_min}/gap_min{gap_min}/",
                                        f"{dir_patterns_results}/R/{metadata}/{modif}motifs/itemset_min{nb_itemset_min}/gap_min{gap_min}_gap_max{gap_max}/"]:
                                if not os.path.exists(sub):
                                    os.makedirs(sub, exist_ok=True)
                        for minsup_percent in list_minsup_percent:
                            _check_cancelled()
                            _log(f"Minsup: {minsup_percent}%", LOG_DEBUG)
                            path_out = f"{path_R}minsup{str(minsup_percent)}/"
                            force_recalcul = False  # Flag pour forcer le recalcul si fichier corrompu
                            if os.path.exists(path_out) and not force_recalcul:
                                for dir in os.listdir(path_out):
                                    _check_cancelled()
                                    _log(f"Déjà calculé {dir}", LOG_DEBUG)
                                    fichiers = sorted(os.listdir(path_out + dir), key=lambda f: os.path.getmtime(os.path.join(path_out + dir, f)), reverse=True)
                                    # Filtrer pour ne garder que les fichiers avec timestamps valides
                                    fichiers = [f for f in fichiers if is_valid_timestamp_filename(f)]
                                    for f in fichiers:
                                        _check_cancelled()
                                        if "motifsTexte_" in f:
                                            file_path = path_out + dir + "/" + f
                                            # Vérifier que le fichier n'est pas vide/corrompu
                                            try:
                                                # Lire le fichier pour vérifier qu'il est valide
                                                df_test = pd.read_csv(file_path, sep="\t", index_col=0, nrows=1)
                                                if df_test.empty or len(df_test.columns) == 0:
                                                    _log(f"Fichier corrompu détecté (vide ou sans colonnes) : {file_path}", LOG_WARNING)
                                                    _log(f"   Recalcul nécessaire...", LOG_WARNING)
                                                    force_recalcul = True
                                                    break  # Sortir de la boucle pour forcer le recalcul
                                            except Exception as e:
                                                _log(f"Erreur lecture fichier existant : {file_path}", LOG_WARNING)
                                                _log(f"   {str(e)}", LOG_DEBUG)
                                                _log(f"   Recalcul nécessaire...", LOG_WARNING)
                                                force_recalcul = True
                                                break  # Sortir de la boucle pour forcer le recalcul
                                            
                                            if internal_clustering:
                                                if "_FUS" in f:
                                                    fus_path = file_path
                                                else:
                                                    df_k = pd.read_csv(file_path, sep="\t", index_col=0)
                                                    _log(f"   Fusion des clusters internes pour {f}...", LOG_DEBUG)
                                                    lexic_int_str = formate_patterns.make_dict_int_to_str(
                                                        f"{dir_lexiques}/dico_str_to_int_all_items.pk"
                                                    )
                                                    df_k = compute_CQP.fusion_internal_clusters(df_k, lexic_int_str, args, dir_clustering_results)
                                                    
                                                    # Vérifier que la fusion a produit un résultat valide
                                                    if df_k.empty or len(df_k.columns) == 0:
                                                        _log(f"La fusion des clusters a échoué (DataFrame vide)", LOG_WARNING)
                                                        _log(f"   Utilisation du fichier non-FUS à la place", LOG_WARNING)
                                                        results[f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"] = file_path
                                                        break
                                                    
                                                    f_fus = f[:-4] + "_FUS.tsv"
                                                    fus_path = path_out + dir + "/" + f_fus
                                                    df_k.to_csv(fus_path, sep="\t")
                                                    _log(f"   Fichier FUS généré: {f_fus}", LOG_DEBUG)
                                                
                                                # Valider le fichier FUS généré/existant
                                                try:
                                                    df_fus_test = pd.read_csv(fus_path, sep="\t", index_col=0, nrows=1)
                                                    if df_fus_test.empty or len(df_fus_test.columns) == 0:
                                                        _log(f"Fichier FUS corrompu détecté (vide ou sans colonnes) : {fus_path}", LOG_WARNING)
                                                        _log(f"   Suppression et recalcul nécessaire...", LOG_WARNING)
                                                        os.remove(fus_path)
                                                        force_recalcul = True
                                                        break  # Forcer le recalcul complet
                                                except Exception as e:
                                                    _log(f"Erreur lecture fichier FUS : {fus_path}", LOG_WARNING)
                                                    _log(f"   {str(e)}", LOG_DEBUG)
                                                    _log(f"   Suppression et recalcul nécessaire...", LOG_WARNING)
                                                    if os.path.exists(fus_path):
                                                        os.remove(fus_path)
                                                    force_recalcul = True
                                                    break  # Forcer le recalcul complet
                                                
                                                results[f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"] = fus_path
                                            else:
                                                results[f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"] = file_path
                                            break
                                    # Si un fichier corrompu a été détecté, sortir aussi de la boucle externe
                                    if force_recalcul:
                                        break
                            
                            if not os.path.exists(path_out) or force_recalcul:
                                _log("Calcul en cours...", LOG_INFO)
                                results, path_out = compute_CQP.main(
                                    textes,
                                    minsup_percent,
                                    gap_min,
                                    gap_max,
                                    nb_itemset_min,
                                    specifs,
                                    df_metadata,
                                    modif,
                                    metadata,
                                    internal_clustering,
                                    results,
                                    path_out,
                                    mode,
                                    args,
                                    dir_clustering_results,
                                    dir_patterns_results,
                                    registry_path,
                                    dir_lexiques,
                                )
        
        for metadata in list_metadata:
            _check_cancelled()
            _log(metadata, LOG_DEBUG)
            if not os.path.exists(f"{dir_patterns_results}/R/{metadata}"):
                os.makedirs(f"{dir_patterns_results}/R/{metadata}", exist_ok=True)
            
            # POS
            _log("pos", LOG_DEBUG)
            path_pos = f"{dir_patterns_results}/R/{metadata}/"
            execution_time = datetime.datetime.now()
            if not os.path.exists(f"{dir_patterns_results}/R/{metadata}/pos/"):
                os.makedirs(f"{dir_patterns_results}/R/{metadata}/pos/", exist_ok=True)
                if metadata != "id":
                    path_id = f"{dir_patterns_results}/R/id/pos/"
                    modif = ""
                    if os.path.exists(path_id):
                        try:
                            file_out_pos, file_total, path_out, df_pos = compute_CQP.get_already_computed_df_id("pos", minsup_percent, gap_min, gap_max, nb_itemset_min, path_id, path_pos, modif)
                        except (FileNotFoundError, Exception) as e:
                            _log(f"Aucun fichier POS valide trouvé, recalcul nécessaire...", LOG_WARNING)
                            file_out_pos, path_out, df_pos, file_total = compute_CQP.compute_freq_TextesPos_AFC(execution_time, path_pos, registry_path)
                    else:
                        file_out_pos, path_out, df_pos, file_total = compute_CQP.compute_freq_TextesPos_AFC(execution_time, path_pos, registry_path)
                    df_pos = compute_CQP.textes2metadata(df_pos, df_metadata, metadata).T
                else:
                    file_out_pos, path_out, df_pos, file_total = compute_CQP.compute_freq_TextesPos_AFC(execution_time, path_pos, registry_path)
                df_pos.to_csv(file_out_pos, sep="\t")
                _log(f"file_out_pos : {file_out_pos}", LOG_DEBUG)
                if mode == "auto":
                    subprocess.call(["Rscript", "./src/AFC.R", file_out_pos, path_out])
                df_pos = compute_CQP.add_total(df_pos)
                df_pos.to_csv(file_total, sep="\t")
                results[f"{metadata}_pos"] = file_out_pos
            else:
                _log(f"Le fichier de résultats pour POS existe déjà", LOG_DEBUG)
                doss = f"{dir_patterns_results}/R/{metadata}/pos/"
                liste = [doss + f for f in os.listdir(doss) if "posTexte_" in f and is_valid_timestamp_filename(f)]
                tri = sorted(liste, key=os.path.getmtime, reverse=True)
                if tri:
                    results[f"{metadata}_pos"] = tri[0]
                else:
                    _log(f"⚠ Aucun fichier POS trouvé dans {doss}", LOG_WARNING)
        
        # Lemma
        for seuil in liste_seuils_lemma:
            _check_cancelled()
            _log(f"{seuil}lemma{downhill_pos4lemma}", LOG_DEBUG)
            path_lemma = f"{dir_patterns_results}/R/{metadata}/"
            execution_time = datetime.datetime.now()
            if not os.path.exists(f"{dir_patterns_results}/R/{metadata}/{seuil}lemma{downhill_pos4lemma}"):
                os.makedirs(f"{dir_patterns_results}/R/{metadata}/{seuil}lemma{downhill_pos4lemma}", exist_ok=True)
                if metadata != "id":
                    path_id = f"{dir_patterns_results}/R/id/{seuil}lemma{downhill_pos4lemma}/"
                    modif = ""
                    if os.path.exists(path_id):
                        try:
                            file_out_lemma, file_total, path_out, df_lemma = compute_CQP.get_already_computed_df_id(
                                f"{seuil}lemma{downhill_pos4lemma}", minsup_percent, gap_min, gap_max, nb_itemset_min, path_id, path_lemma, modif
                            )
                        except (FileNotFoundError, Exception) as e:
                            _log(f"Aucun fichier Lemma valide trouvé, recalcul nécessaire...", LOG_WARNING)
                            file_out_lemma, path_out, df_lemma, file_total = compute_CQP.compute_freq_TextesLemma_AFC(seuil, execution_time, path_lemma, downhill_pos4lemma, registry_path)
                    else:
                        file_out_lemma, path_out, df_lemma, file_total = compute_CQP.compute_freq_TextesLemma_AFC(seuil, execution_time, path_lemma, downhill_pos4lemma, registry_path)
                    df_lemma = compute_CQP.textes2metadata(df_lemma, df_metadata, metadata).T
                else:
                    file_out_lemma, path_out, df_lemma, file_total = compute_CQP.compute_freq_TextesLemma_AFC(seuil, execution_time, path_lemma, downhill_pos4lemma, registry_path)
                df_lemma.to_csv(file_out_lemma, sep="\t")
                if mode == "auto":
                    subprocess.call(["Rscript", "./src/AFC.R", file_out_lemma, path_out])
                df_lemma = compute_CQP.add_total(df_lemma)
                df_lemma.to_csv(file_total, sep="\t")
                results[f"{metadata}_{seuil}lemma{downhill_pos4lemma}"] = file_out_lemma
            else:
                _log(f"already computed {seuil}lemma{downhill_pos4lemma}", LOG_DEBUG)
                doss = f"{dir_patterns_results}/R/{metadata}/{seuil}lemma{downhill_pos4lemma}/"
                liste = [doss + f for f in os.listdir(doss) if f"{seuil}lemma{downhill_pos4lemma}Texte_" in f and is_valid_timestamp_filename(f)]
                tri = sorted(liste, key=os.path.getmtime, reverse=True)
                if tri:
                    results[f"{metadata}_{seuil}lemma{downhill_pos4lemma}"] = tri[0]
                else:
                    _log(f"⚠ Aucun fichier Lemma trouvé dans {doss}", LOG_WARNING)
        
        # Bigrams
        for seuil in liste_seuils_bigrams:
            _check_cancelled()
            _log(f"{seuil}bigrams", LOG_DEBUG)
            path_big = f"{dir_patterns_results}/R/{metadata}/"
            execution_time = datetime.datetime.now()
            if not os.path.exists(f"{dir_patterns_results}/R/{metadata}/{seuil}bigramslemma"):
                os.makedirs(f"{dir_patterns_results}/R/{metadata}/{seuil}bigramslemma", exist_ok=True)
                if metadata != "id":
                    path_id = f"{dir_patterns_results}/R/id/{seuil}bigramslemma/"
                    modif = ""
                    if os.path.exists(path_id):
                        try:
                            file_out_bigrams, file_total, path_out, df_big = compute_CQP.get_already_computed_df_id(
                                f"{seuil}bigramslemma", minsup_percent, gap_min, gap_max, nb_itemset_min, path_id, path_big, modif
                            )
                        except (FileNotFoundError, Exception) as e:
                            _log(f"Aucun fichier Bigrams valide trouvé, recalcul nécessaire...", LOG_WARNING)
                            file_out_bigrams, path_out, df_big = compute_CQP.compute_freq_Textes_BigramsLemma_noAFC(execution_time, path_big, seuil, registry_path)
                    else:
                        file_out_bigrams, path_out, df_big = compute_CQP.compute_freq_Textes_BigramsLemma_noAFC(execution_time, path_big, seuil, registry_path)
                    df_big = compute_CQP.textes2metadata(df_big, df_metadata, metadata).T
                else:
                    file_out_bigrams, path_out, df_big = compute_CQP.compute_freq_Textes_BigramsLemma_noAFC(execution_time, path_big, seuil, registry_path)
                df_big.to_csv(file_out_bigrams, sep="\t")
                if mode == "auto":
                    subprocess.call(["Rscript", "./src/AFC.R", file_out_bigrams, path_out])
                results[f"{metadata}_{seuil}bigramslemma"] = file_out_bigrams
            else:
                _log(f"already computed {seuil}bigrams", LOG_DEBUG)
                doss = f"{dir_patterns_results}/R/{metadata}/{seuil}bigramslemma/"
                liste = [doss + f for f in os.listdir(doss) if "bigramslemmaTexte_" in f and is_valid_timestamp_filename(f)]
                tri = sorted(liste, key=os.path.getmtime, reverse=True)
                if tri:
                    results[f"{metadata}_{seuil}bigramslemma"] = tri[0]
                else:
                    _log(f"⚠ Aucun fichier Bigrams trouvé dans {doss}", LOG_WARNING)

        _log(str(results), LOG_DEBUG)
        
        # Réinitialiser les paramètres aux premières valeurs pour la section POS/Lemma/Bigrams
        nb_itemset_min = list_itemset_min[0] if list_itemset_min else 3
        gap_min = list_gap_min[0] if list_gap_min else 0
        gap_max = list_gap_max[0] if list_gap_max else 0
        minsup_percent = list_minsup_percent[0] if list_minsup_percent else 25
        
        end_time = time.time()
        time_stats = end_time - start_time
    
    _check_cancelled()
    _progress("Analyse terminée", 100)
    
    # Calculer le temps total de l'analyse
    end_time_total = time.time()
    time_total = end_time_total - start_time_total
    
    # Afficher les temps dans les logs (mode auto et gui)
    if mode in ["auto", "gui"]:
        _log(f"Temps total d'annotation ({annotator.get_name()}) : {format_time(time_tag)}", LOG_INFO)
        _log(f"Temps d'extraction des motifs : {format_time(time_DMT4)}", LOG_INFO)
        _log(f"Temps de calcul statistique : {format_time(time_stats)}", LOG_INFO)
        if internal_clustering:
            _log(f"Temps de clustering interne : {format_time(time_clustering)}", LOG_INFO)
        _log(f"="*75, LOG_INFO)
        _log(f"⏱️  TEMPS TOTAL DE L'ANALYSE : {format_time(time_total)}", LOG_INFO)
        _log(f"="*75, LOG_INFO)
    
    if mode == "auto":
        
        execution_time = datetime.datetime.now()
        log_file_path = f"{dir_logs}/log_{execution_time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_file_path, "w") as file:
            file.write(f"earlySelection={earlySelection}\n")
            file.write(f"internal_clustering={internal_clustering}\n")
            file.write(f"list_itemset_min={list_itemset_min}\n")
            file.write(f"list_gap_min={list_gap_min}\n")
            file.write(f"list_gap_max={list_gap_max}\n")
            file.write(f"list_minsup_percent={list_minsup_percent}\n")
            file.write(f"Patterns_param_form={Form}\n")
            file.write(f"Patterns_param_lemma={Lemma}\n")
            file.write(f"Patterns_param_pos={Pos}\n")
            file.write(f"Patterns_param_dep={Dep}\n")
            file.write(f"Patterns_param_feats={Feats}\n")
            file.write(f"List_metadata={list_metadata}\n")
            file.write(f"List_seuils_lemma={liste_seuils_lemma}\n")
            file.write(f"List_seuils_bigrams={liste_seuils_bigrams}\n")
            file.write("-" * 75 + "\n")
            file.write(f"Temps d'annotation : {format_time(time_tag)}\n")
            file.write(f"Temps d'extraction des motifs : {format_time(time_DMT4)}\n")
            if internal_clustering:
                file.write(f"Temps de clustering interne : {format_time(time_clustering)}\n")
            file.write(f"Temps de calcul statistique : {format_time(time_stats)}\n")
            file.write("-" * 75 + "\n")
            file.write(f"TEMPS TOTAL : {format_time(time_total)}\n")
            file.write("-" * 75 + "\n")
    elif mode != "gui":
        # Ne lance Shiny automatiquement que si on n'est pas en mode GUI
        # (la GUI gère elle-même le lancement via le bouton "Lancer Shiny")
        json_results = json.dumps(results)
        # Sauvegarder le fichier JSON dans le dossier de l'analyse si paths est fourni
        if paths:
            json_file = f"{dir_logs}/temp_input.json"
        else:
            json_file = "./temp_input.json"
        with open(json_file, "w") as file:
            file.write(json_results)
        
        shiny_app = "./src/Shiny_CA.R"
        p = subprocess.Popen(
            ["Rscript", shiny_app, json_file],
            stdout=None,
            stderr=None,
            stdin=None,
        )
    return results

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    from config import (
        download, use_gpu, language,
        earlySelection, seuil_early_selection, filter_specifs,
        partition_cible, seuil_banalité, early_pos4lemma,
        user_input_list, liste_earlyselection_lemma,
        internal_clustering,
        list_itemset_min, list_gap_min, list_gap_max, list_minsup_percent, threads,
        Form, Lemma, Pos, Dep, Feats,
        path_metadata, list_metadata, specifs,
        liste_seuils_lemma, downhill_pos4lemma, liste_seuils_bigrams,
    )
    
    config = dict(
        download=download, use_gpu=use_gpu, language=language,
        earlySelection=earlySelection, seuil_early_selection=seuil_early_selection,
        filter_specifs=filter_specifs, partition_cible=partition_cible,
        seuil_banalité=seuil_banalité, early_pos4lemma=early_pos4lemma,
        user_input_list=user_input_list, liste_earlyselection_lemma=liste_earlyselection_lemma,
        internal_clustering=internal_clustering,
        list_itemset_min=list_itemset_min, list_gap_min=list_gap_min,
        list_gap_max=list_gap_max, list_minsup_percent=list_minsup_percent,
        threads=threads, Form=Form, Lemma=Lemma, Pos=Pos, Dep=Dep, Feats=Feats,
        path_metadata=path_metadata, list_metadata=list_metadata, specifs=specifs,
        liste_seuils_lemma=liste_seuils_lemma, downhill_pos4lemma=downhill_pos4lemma,
        liste_seuils_bigrams=liste_seuils_bigrams, mode=mode,
    )
    
    run_analysis(config)
