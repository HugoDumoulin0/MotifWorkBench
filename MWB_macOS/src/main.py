"""
Last updated on XXX

@author: Dumoulin, H & Premat, T.
Based on scripts by Jade Mekki 2022
Modified by JcharlesDS (2026)
"""


import os
import sys
from pprint import pprint
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
import zipfile

from replace_underscore import replace_underscore_in_conllu 

# Import du système d'annotation modulaire
from annotators import get_annotator 


def format_log_message(level: int, message: str) -> str:
    """Encapsule un message avec son niveau pour la GUI."""
    return f"[[LEVEL:{level}]] {message}"


class StdoutLogger:
    """Redirige stdout et stderr vers le callback de log."""
    def __init__(self, log_callback, level=1):
        self.log_callback = log_callback
        self.level = level
        self.buffer = ""
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def write(self, text):
        if text and text.strip():
            if self.log_callback:
                self.log_callback(format_log_message(self.level, text.rstrip()))
            else:
                self.original_stdout.write(text)
                
    def flush(self):
        pass
    
    def __enter__(self):
        sys.stdout = self
        sys.stderr = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        return False


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


class AnalysisCancelled(Exception):
    """Exception levée lorsqu'un arrêt utilisateur est demandé."""


ANNOTATION_CACHE_VERSION = 1


def _file_signature(path: Path) -> dict:
    """Construit une signature légère pour valider un fichier source."""
    stat = path.stat()
    return {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _build_source_manifest(corpus_dir: Path, textes: list[str]) -> dict:
    """Construit le manifeste des fichiers source du corpus."""
    return {
        f"{texte}.txt": _file_signature(corpus_dir / f"{texte}.txt")
        for texte in textes
    }


def _load_cache_info(cache_info_path: Path) -> dict | None:
    if not cache_info_path.exists():
        return None
    try:
        with open(cache_info_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _annotation_cache_is_valid(cache_paths: dict, expected_info: dict, source_manifest: dict) -> bool:
    """Vérifie si le cache partagé est complet et correspond au corpus source."""
    cache_info = _load_cache_info(cache_paths["cache_info"])
    if not cache_info:
        return False

    for key in ("pipeline_version", "selected_corpus", "annotator", "language", "actual_model_name", "use_gpu"):
        if cache_info.get(key) != expected_info.get(key):
            return False

    if cache_info.get("source_manifest", {}) != source_manifest:
        return False

    tagged_dir = cache_paths["tagged"]
    underscore_dir = cache_paths["underscore_fix"]
    if not tagged_dir.exists() or not underscore_dir.exists():
        return False

    for filename in source_manifest:
        conllu_name = f"{Path(filename).stem}.conllu"
        if not (tagged_dir / conllu_name).exists():
            return False
        if not (underscore_dir / conllu_name).exists():
            return False

    return True


def _write_annotation_cache_info(cache_paths: dict, cache_info: dict) -> None:
    cache_paths["root"].mkdir(parents=True, exist_ok=True)
    with open(cache_paths["cache_info"], "w", encoding="utf-8") as f:
        json.dump(cache_info, f, indent=2, ensure_ascii=False)


def _prepare_annotation_cache_dirs(cache_paths: dict) -> None:
    cache_paths["tagged"].mkdir(parents=True, exist_ok=True)
    cache_paths["underscore_fix"].mkdir(parents=True, exist_ok=True)


def _reset_annotation_cache(cache_paths: dict) -> None:
    """Supprime puis recrée le cache d'annotation partagé."""
    if cache_paths["root"].exists():
        shutil.rmtree(cache_paths["root"])
    _prepare_annotation_cache_dirs(cache_paths)


def _resolve_optional_path(project_root: Path, path_value: str) -> Path:
    """Résout un chemin utilisateur éventuellement relatif."""
    path = Path(str(path_value).strip()).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path


def _copy_conllu_files(source_dir: Path, destination_dir: Path, recursive: bool = False) -> list[str]:
    """Copie les fichiers .conllu d'un dossier vers un autre et retourne leurs stems."""
    destination_dir.mkdir(parents=True, exist_ok=True)
    pattern = source_dir.rglob("*.conllu") if recursive else source_dir.glob("*.conllu")
    conllu_files = sorted(path for path in pattern if path.is_file())
    if not conllu_files:
        raise FileNotFoundError(f"Aucun fichier .conllu trouvé dans {source_dir}")

    for existing in destination_dir.glob("*.conllu"):
        existing.unlink()

    stems = []
    for path in conllu_files:
        target = destination_dir / path.name
        shutil.copy2(path, target)
        stems.append(path.stem)
    return sorted(stems)


def _generate_underscore_fix(source_dir: Path, destination_dir: Path, textes: list[str], log_fn, cancel_fn) -> None:
    """Génère les fichiers underscore_fix à partir de fichiers .conllu annotés."""
    destination_dir.mkdir(parents=True, exist_ok=True)
    for existing in destination_dir.glob("*.conllu"):
        existing.unlink()

    total_textes = len(textes)
    for idx, texte in enumerate(textes, start=1):
        cancel_fn()
        output_file = destination_dir / f"{texte}.conllu"
        log_fn(f"\t [{idx}/{total_textes}] Underscore_fix : {texte}", 2)
        shutil.copy2(source_dir / f"{texte}.conllu", output_file)
        replace_underscore_in_conllu(str(output_file))


def _find_first_matching_directory(base_dir: Path, dir_names: tuple[str, ...]) -> Path | None:
    """Cherche récursivement un dossier correspondant à l'un des noms fournis."""
    lowered = {name.lower() for name in dir_names}
    for candidate in sorted(base_dir.rglob("*")):
        if candidate.is_dir() and candidate.name.lower() in lowered:
            return candidate
    return None


def run_analysis(config, progress_callback=None, log_callback=None, paths=None, should_stop_callback=None):
    """
    Lance l'analyse complète.

    Args:
        config (dict): Contient toutes les variables de configuration nécessaires à l'exécution de l'analyse.
        progress_callback (callable, optional): Fonction de rappel pour suivre la progression. Defaults to None.
        log_callback (callable, optional): Fonction de rappel pour enregistrer les logs. Defaults to None.
        paths (dict, optional): Dictionnaire contenant les chemins pour l'organisation par corpus/config. Defaults to None.
        should_stop_callback (callable, optional): Retourne True si l'analyse doit être interrompue.
    """
    # Démarrer le chronomètre pour le temps total
    start_time_total = time.time()
    project_root = Path(__file__).resolve().parents[1]
    
    # Charger le niveau de verbosité depuis app_settings.json
    settings_file = project_root / "logs" / "app_settings.json"
    log_verbosity = "normal"  # Valeur par défaut
    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                log_verbosity = settings.get("log_level", "normal")
        except Exception:
            pass
    
    # Mapping des niveaux de verbosité
    # minimal: 0, normal: 1, détaillé: 2, debug: 3
    verbosity_levels = {
        "minimal": 0,
        "normal": 1,
        "détaillé": 2,
        "debug": 3
    }
    current_level = verbosity_levels.get(log_verbosity, 1)

    def _resolve_user_path(path_value, fallback):
        raw = str(path_value).strip() if path_value else fallback
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = project_root / candidate
        return str(candidate)
    
    # Ajouter ./bin au PATH pour que les scripts Perl trouvent les wrappers CWB Docker
    bin_path = str(project_root / "bin")
    os.environ["PATH"] = f"{bin_path}:{os.environ.get('PATH', '')}"
    
    # Les chemins sont toujours fournis par la GUI via create_analysis_structure()
    if not paths:
        raise ValueError("Les chemins d'analyse doivent être fournis via le paramètre 'paths'")
    
    # Organisation par groupe/config : Data/analyses/{analysis_group_name}/{config_id}/
    dir_tagged = str(paths["tagged"])
    dir_tagged_for_dmt4 = str(paths["tagged_for_dmt4"])
    dir_textes_vrt = str(paths["textes_vrt"])
    dir_cwb_corpus = str(paths["cwb_corpus"])  # Corpus CWB propre à chaque analyse
    dir_dmt4_files = str(paths["dmt4_files"])
    dir_lexiques = str(paths["lexiques"])
    dir_clustering_results = str(paths["clustering_results"])
    dir_patterns_results = str(paths["patterns_results"])
    dir_logs = str(paths["logs"])
    dir_underscore_fix = str(paths["underscore_fix"])
    dir_early_selection = str(paths.get("early_selection", "")) if paths.get("early_selection") else ""
    # Chemins source (ne changent pas)
    dir_textes_raw = _resolve_user_path(config.get("metadata_corpus_dir"), "Data/Corpus/Textes_raw")
    path_metadata = _resolve_user_path(config.get("path_metadata"), "Data/Corpus/metadata.tsv")
    
    # Définir le chemin du registry CWB (nouveau ou ancien système)
    registry_path = f"{dir_cwb_corpus}/registry"
    
    # Définir la variable d'environnement pour que les scripts Perl trouvent le corpus
    os.environ["CORPUS_REGISTRY_PATH"] = registry_path
    
    def _log(msg, level=1):
        """
        Log un message selon le niveau de verbosité.
        
        Args:
            msg: Le message à logger
            level: Niveau du message (0=minimal, 1=normal, 2=détaillé, 3=debug)
        """
        if level <= current_level:
            if log_callback:
                log_callback(format_log_message(level, msg))
            else:
                print(msg)
    
    def _progress(etape, pct):
        if progress_callback:
            progress_callback(etape, pct)

    def _should_stop():
        return bool(should_stop_callback and should_stop_callback())

    def _check_cancel():
        if _should_stop():
            _log("Arrêt demandé par l'utilisateur. Interruption en cours...", level=0)
            raise AnalysisCancelled("Analyse arrêtée par l'utilisateur.")
    
    # Configuration
    use_gpu = config.get("use_gpu", True)
    language = config.get("language", "fr")
    annotator_name = config.get("annotator", "stanza")  # stanza | spacy
    input_type = config.get("input_type", "raw_txt")
    input_source_path = str(config.get("input_source_path", "")).strip()
    earlySelection = config.get("earlySelection", False)
    seuil_early_selection = config.get("seuil_early_selection", 200)
    filter_specifs = config.get("filter_specifs", False)
    partition_cible = config.get("partition_cible", "test")
    seuil_banalité = config.get("seuil_banalité", 2)
    early_pos4lemma = config.get("early_pos4lemma", "ADJ|NOUN|VERB")
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
    path_metadata = _resolve_user_path(config.get("path_metadata"), "Data/Corpus/metadata.tsv")
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
    
    _log("-"*75, level=0)  # Séparateur = minimal
    _log("1. Annotation des données", level=0)  # Titre de section = minimal
    _progress("Annotation", 0)
    _check_cancel()
    
    selected_corpus = str(config.get("selected_corpus", "")).strip() or Path(dir_textes_raw).name
    start_time = time.time()

    if input_type == "raw_txt":
        try:
            annotator = get_annotator(annotator_name)
            _log(f"1.1. Annotation avec {annotator.get_name()}: POS, lemma, UD", level=1)
        except ValueError as e:
            _log(f"Erreur: {e}", level=0)
            raise

        actual_model_name = annotator.resolve_model_name(language, use_gpu)
        corpus_dir = Path(dir_textes_raw)
        if not corpus_dir.exists():
            raise FileNotFoundError(f"Dossier corpus introuvable: {dir_textes_raw}")

        textes = sorted(path.stem for path in corpus_dir.glob("*.txt"))
        if not textes:
            raise FileNotFoundError(
                f"Aucun fichier .txt trouvé dans le corpus: {dir_textes_raw}. "
                "Le dossier doit contenir les textes source et peut aussi contenir metadata.tsv."
            )

        if not annotator.check_model_available(language, use_gpu):
            _log(f"Modèle {annotator.get_name()} absent — téléchargement automatique en cours...", level=1)
            with StdoutLogger(log_callback, level=1):
                annotator.download_model(language, use_gpu, log_callback=lambda msg: _log(msg, level=1))
            actual_model_name = annotator.resolve_model_name(language, use_gpu)
            _log(f"Modèle {annotator.get_name()} téléchargé et prêt.", level=1)
        else:
            _log(f"Modèle {annotator.get_name()} '{actual_model_name}' déjà présent.", level=2)
        _check_cancel()

        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from gui.core.analysis_paths import build_annotation_cache_paths

        cache_paths = build_annotation_cache_paths(
            selected_corpus=selected_corpus,
            annotator_name=annotator_name,
            actual_model_name=actual_model_name,
            use_gpu=use_gpu,
        )
        source_manifest = _build_source_manifest(corpus_dir, textes)
        cache_info = {
            "pipeline_version": ANNOTATION_CACHE_VERSION,
            "selected_corpus": selected_corpus,
            "annotator": annotator_name,
            "language": language,
            "actual_model_name": actual_model_name,
            "use_gpu": use_gpu,
            "source_dir": str(corpus_dir),
            "source_manifest": source_manifest,
        }

        shared_tagged_dir = cache_paths["tagged"]
        shared_underscore_dir = cache_paths["underscore_fix"]

        if _annotation_cache_is_valid(cache_paths, cache_info, source_manifest):
            _log(f"Cache d'annotation partagé réutilisé : {cache_paths['root']}", level=1)
        else:
            _log(f"Cache d'annotation absent ou invalide, régénération : {cache_paths['root']}", level=1)
            _reset_annotation_cache(cache_paths)

            tagging_list = []
            for texte in textes:
                output_file = shared_tagged_dir / f"{texte}.conllu"
                input_file = Path(dir_textes_raw) / f"{texte}.txt"
                if output_file.exists():
                    _log(f"\t {texte}.conllu existe déjà dans le cache.", level=2)
                else:
                    _log(f"\t {texte}.conllu n'existe pas dans le cache. Annotation nécessaire...", level=2)
                    tagging_list.append((texte, input_file))

            if tagging_list:
                _log(f"{len(tagging_list)} fichier(s) à annoter.", level=1)

                def annotation_progress_callback(texte_id, current, total):
                    pct = int((current / total) * 15)
                    _progress(f"Annotation ({annotator.get_name()})", pct)

                actual_model_name = annotator.annotate_files(
                    input_files=tagging_list,
                    output_dir=shared_tagged_dir,
                    language=language,
                    use_gpu=use_gpu,
                    log_callback=lambda msg: _log(msg, level=3),
                    progress_callback=annotation_progress_callback,
                    should_stop_callback=_should_stop
                )
                cache_info["actual_model_name"] = actual_model_name
            else:
                _log("Tous les fichiers annotés sont déjà présents dans le cache partagé.", level=1)

            total_textes = len(textes)
            for idx, texte in enumerate(textes, start=1):
                _check_cancel()
                output_file = shared_underscore_dir / f"{texte}.conllu"
                if output_file.exists():
                    _log(f"\t [{idx}/{total_textes}] Underscore_fix déjà présent dans le cache pour {texte}.", level=3)
                else:
                    _log(f"\t [{idx}/{total_textes}] Underscore_fix : {texte}", level=2)
                    source = shared_tagged_dir / f"{texte}.conllu"
                    shutil.copy(source, shared_underscore_dir)
                    replace_underscore_in_conllu(str(output_file))

            _write_annotation_cache_info(cache_paths, cache_info)

        dir_tagged = str(shared_tagged_dir)
        dir_underscore_fix = str(shared_underscore_dir)
    else:
        actual_model_name = "Importé"
        imported_path = _resolve_optional_path(project_root, input_source_path)
        if not input_source_path:
            raise FileNotFoundError("Aucune source importée n'a été fournie pour ce type d'entrée.")

        tagged_dir_path = Path(dir_tagged)
        underscore_dir_path = Path(dir_underscore_fix)

        if input_type == "annotated_conllu":
            _log("1.1. Import d'un corpus annoté (.conllu)", level=1)
            if not imported_path.exists() or not imported_path.is_dir():
                raise FileNotFoundError(f"Dossier de corpus annoté introuvable: {imported_path}")
            textes = _copy_conllu_files(imported_path, tagged_dir_path)
            _generate_underscore_fix(tagged_dir_path, underscore_dir_path, textes, _log, _check_cancel)
            actual_model_name = "Importé (.conllu)"
        elif input_type == "prepared_zip":
            _log("1.1. Import d'une archive préparée (.zip)", level=1)
            if not imported_path.exists() or not imported_path.is_file():
                raise FileNotFoundError(f"Archive préparée introuvable: {imported_path}")
            extract_root = Path(paths["root"]) / "imported_archive_extracted"
            if extract_root.exists():
                shutil.rmtree(extract_root)
            extract_root.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(imported_path, "r") as zip_file:
                zip_file.extractall(extract_root)

            tagged_source = _find_first_matching_directory(
                extract_root,
                ("Textes_tagged", "textes_tagged", "Textes_tagged_stanza"),
            )
            underscore_source = _find_first_matching_directory(
                extract_root,
                ("underscore_fix",),
            )

            if not tagged_source and not underscore_source:
                raise FileNotFoundError(
                    "L'archive ne contient ni dossier Textes_tagged, ni dossier underscore_fix."
                )

            if tagged_source:
                textes = _copy_conllu_files(tagged_source, tagged_dir_path, recursive=True)
            else:
                textes = []

            if underscore_source:
                underscore_textes = _copy_conllu_files(underscore_source, underscore_dir_path, recursive=True)
                textes = underscore_textes or textes
                if not tagged_source:
                    dir_tagged = str(underscore_dir_path)
                _log("Archive préparée détectée avec underscore_fix : annotation et correction sautées.", level=1)
            else:
                if not tagged_source:
                    raise FileNotFoundError("L'archive doit contenir Textes_tagged si underscore_fix est absent.")
                _generate_underscore_fix(tagged_dir_path, underscore_dir_path, textes, _log, _check_cancel)
                _log("Archive préparée sans underscore_fix : correction appliquée sur Textes_tagged.", level=1)

            actual_model_name = "Importé (.zip)"
        else:
            raise ValueError(f"Type d'entrée non supporté: {input_type}")

        if not textes:
            raise FileNotFoundError("Aucun fichier .conllu exploitable n'a été trouvé dans la source importée.")

    config["actual_model_name"] = actual_model_name
    
    end_time = time.time()
    time_tag = end_time - start_time
    

    # ==================================
    # 2 - Fichiers DMT4
    # ==================================
    
    _log("-" * 75, level=0)  # Séparateur = minimal
    _log("2. Création des fichiers DMT4", level=0)  # Titre de section = minimal
    _progress("Création fichiers DMT4", 15)
    _check_cancel()
    
    # Créer ou nettoyer le dossier DMT4
    dmt4_prep_dir = dir_tagged_for_dmt4
    if os.path.exists(dmt4_prep_dir):
        _log("\t DMT4: Nettoyage du dossier existant...", level=2)
        # Supprimer les fichiers temporaires (merged, etc.)
        for f in os.listdir(dmt4_prep_dir):
            if not f.endswith('.conllu'):
                os.remove(os.path.join(dmt4_prep_dir, f))
    else:
        os.makedirs(dmt4_prep_dir, exist_ok=True)
    
    # Copier les fichiers CoNLL-U
    _log("\t DMT4: Copie des fichiers CoNLL-U...", level=2)
    for texte in textes:
        _check_cancel()
        destination = dmt4_prep_dir
        source = f"{dir_underscore_fix}/{texte}.conllu"
        dest_file = os.path.join(destination, f"{texte}.conllu")
        if not os.path.exists(dest_file):
            shutil.copy(source, destination)
            _log(f"\t\t Copie: {texte}.conllu", level=3)
    
    liste_textes = ["merged"]
    dmt4_merged_sorted = f"{dir_dmt4_files}/DMT4_merged_files_sorted.txt"
    
    if os.path.exists(dmt4_merged_sorted):
        _log("\t Le fichier DMT4 trié existe déjà.", level=1)
    else:
        _check_cancel()
        if not os.path.exists(dir_dmt4_files):
            os.makedirs(dir_dmt4_files, exist_ok=True)
        _log("\t DMT4: Création du fichier DMT4.", level=1)
        # S'assurer que le chemin se termine par / pour les fonctions de concaténation
        dmt4_prep_dir_slash = dmt4_prep_dir.rstrip("/") + "/"
        conll_dmt4.instancier_dict(dmt4_prep_dir_slash, dir_lexiques)
        # Ne sélectionner que les fichiers .conllu
        path = dmt4_prep_dir_slash
        file_list = [f for f in os.listdir(dmt4_prep_dir) if f.endswith('.conllu')]
        _log(f"\t DMT4: Concaténation de {len(file_list)} fichiers...", level=2)
        tools.concat_multiple_conll(path, file_list, "merged")
        for texte in liste_textes:
            conll_dmt4.transform_data(dmt4_prep_dir_slash, texte, Form, Lemma, Pos, Dep, Feats, dir_dmt4_files, dir_lexiques)
        # S'assurer que le chemin se termine par / pour sort_dmtfiles
        dir_dmt4_files_slash = dir_dmt4_files.rstrip("/") + "/"
        conll_dmt4.sort_dmtfiles(dir_dmt4_files_slash)
        for texte in liste_textes:
            conll_dmt4.make_DMT4_file(texte, dir_dmt4_files)
    
    path_tagged = dir_tagged.rstrip("/") + "/"
    path_vrt = dir_textes_vrt.rstrip("/") + "/"
    _check_cancel()
    with StdoutLogger(log_callback, level=2):
        conllu2vrt.transform(path_tagged, path_vrt)
    if not os.path.exists(dir_cwb_corpus):
        os.makedirs(dir_cwb_corpus, exist_ok=True)
    with StdoutLogger(log_callback, level=2):
        cwb.main(dir_cwb_corpus, dir_textes_vrt)
        
    if earlySelection:
        _check_cancel()
        _log("-" * 75, level=0)
        _log("2.1 Early Selection du lemme pour la recherche", level=0)
        path_lexique = f"{dir_lexiques}/dico_str_to_int_all_items.pk"
        early_selection_minsup = list_minsup_percent[0] if list_minsup_percent else 25
        if filter_specifs and len(list_minsup_percent) > 1:
            _log(
                f"Filtrage par spécificités actif : le minsup utilisé pour l'early selection sera {early_selection_minsup}% "
                f"(première valeur configurée).",
                level=2,
            )
        with StdoutLogger(log_callback, level=2):
            liste_earlyselection_lemma = early_selection.main(
                seuil_early_selection, 
                early_selection_minsup,
                path_metadata, 
                partition_cible, 
                seuil_banalité, 
                early_pos4lemma, 
                filter_specifs,
                path_out=dir_early_selection,
                path_lexique=path_lexique,
                registry_path=registry_path
            )
        
    if user_input_list:
        _check_cancel()
        path_lexique = f"{dir_lexiques}/dico_str_to_int_all_items.pk"
        lexique = tools.load_pickles(path_lexique)
        nom = f"user_input_{time.time()}"
        if dir_early_selection:
            os.makedirs(dir_early_selection, exist_ok=True)
            with open(f"{dir_early_selection}/{nom}.txt", "w") as f:
                f.write(str(liste_earlyselection_lemma))
        liste_lemma = []
        lignes = liste_earlyselection_lemma
        _log(str(lignes), level=3)
        for l in lignes:
            lemma_preformat = f'lemma_"{l}"'
            liste_lemma.append(lexique[lemma_preformat])
        
    # ==================================
    # 3 - Extraction des motifs
    # ==================================
    
    _log("-" * 75, level=0)
    _log("3. Extraction des motifs fréquents et clos", level=0)
    _progress("Fouille de motifs (BideSpanTree)", 30)
    start_time = time.time()
    _check_cancel()
    
    path_results = dir_patterns_results
    if not os.path.exists(path_results):
        os.makedirs(path_results, exist_ok=True)
    path_file_closed = f"{dir_patterns_results}/Closed"
    if not os.path.exists(path_file_closed):
        os.makedirs(path_file_closed, exist_ok=True)
    
    for nb_itemset_min in list_itemset_min:
        for gap_min in list_gap_min:
            for gap_max in list_gap_max:
                for minsup_percent in list_minsup_percent:
                    _check_cancel()
                    args = f"{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}"
                    if user_input_list:
                        args = f"user_input_list_{nom}_{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}"
                    if earlySelection:
                        args = f"{seuil_early_selection}early{early_pos4lemma}_specifs{filter_specifs}{partition_cible}_{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}"
                    args = args.replace("|", "-")
                    
                    if os.path.exists(f"{dir_patterns_results}/Closed/{args}_DMT4_merged_files_sorted_closed.txt"):
                        _log(f"\t Le fichier de motifs clos existe déjà pour {args}.", level=1)
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
                        _log(f"\t Nombre d'itemsets minimum {nb_itemset_min} ", level=2)
                        _log(f"\t Gap minimum {gap_min} ", level=2)
                        _log(f"\t Gap maximum {gap_max} ", level=2)
                        _log(f"\t Minimum Support {minsup_percent}% ", level=1)
                        
                        # Vérifier la taille du fichier DMT4
                        dmt4_size = os.path.getsize(dmt4_files)
                        _log(f"\t Fichier DMT4: {dmt4_files} ({dmt4_size} bytes)", level=2)
                        
                        file_out = f"{args}_DMT4_merged_files_sorted_closed.txt"
                        
                        _log("\t\t Extraction des motifs clos", level=1)
                
                        # Utiliser un chemin absolu pour le corpus dans Load.ini
                        dmt4_files_abs = os.path.abspath(dmt4_files)
                        
                        # Obtenir le répertoire racine du projet pour créer Load.ini au bon endroit
                        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        load_ini_path = os.path.join(project_root, "BideSpanTree", "bin", "Load.ini")
                        
                        _log(f"\t\t Création de {load_ini_path}", level=2)
                        with open(load_ini_path, "w", encoding="utf8") as set_up:
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
                            
                            _log("\t\t Tentative d'exécution directe du binaire...", level=2)
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
                            _log("\t\t ✓ Exécution directe réussie", level=1)
                            # Vérifier la taille du fichier de résultats
                            result_size = os.path.getsize(output_path_abs)
                            _log(f"\t\t Fichier de résultats: {output_path} ({result_size} bytes)", level=2)
                            if result_size == 0:
                                _log(f"\t\t ⚠ ATTENTION: Le fichier de résultats est vide!", level=0)
                                if result.stderr:
                                    _log(f"\t\t Stderr: {result.stderr}", level=1)
                        except (FileNotFoundError, subprocess.CalledProcessError, PermissionError, OSError) as e:
                            # Si direct échoue, essayer Docker
                            _log(f"\t\t Exécution directe impossible ({type(e).__name__}), tentative avec Docker...", level=1)
                            try:
                                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                output_path_rel = os.path.relpath(output_path_abs, base_dir)
                                output_path_docker = f"/data/{output_path_rel.replace(os.sep, '/')}"
                                subprocess.run(
                                    ["docker", "run", "--rm", "--platform", "linux/amd64",
                                     "-v", f"{base_dir}:/data",
                                     "ubuntu:22.04",
                                     "bash", "-c",
                                     (
                                         "cd /data/BideSpanTree/bin && "
                                         "chmod +x bidespantree && "
                                         f"mkdir -p \"$(dirname '{output_path_docker}')\" && "
                                         f"./bidespantree > '{output_path_docker}'"
                                     )],
                                    check=True,
                                    capture_output=True,
                                    text=True,
                                )
                                _log("\t\t ✓ Exécution avec Docker réussie", level=1)
                            except (FileNotFoundError, subprocess.CalledProcessError, OSError, PermissionError) as docker_err:
                                error_msg = docker_err.stderr if hasattr(docker_err, 'stderr') and docker_err.stderr else str(docker_err)
                                _log(f"\t\t ✗ Docker échoue aussi: {error_msg}", level=0)
                                
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
                            _log(f"Erreur lors de l'extraction des motifs: {str(e)}", level=0)

        end_time = time.time()
        time_DMT4 = end_time - start_time
    
    # ========================================
    # 4 - Calcul des motifs caractéristiques
    # ========================================
    
    _log("-" * 75, level=0)
    _log("4. Extraction des motifs caractéristiques", level=0)
    _progress("Calcul des motifs caractéristiques", 55)
    
    rep_clos = f"{dir_patterns_results}/Closed/"
    for f_clos in os.listdir(rep_clos):
        if "txt" not in f_clos:
            continue
        compute_emergent_sequential_patterns.from_txt_to_dict(os.path.join(rep_clos, f_clos))
    
    
    # ================================
    # 4.bis - Clustering interne
    # ================================
    
    if internal_clustering:
        _progress("Clustering interne", 60)
        start_time = time.time()
        _check_cancel()
        for d in [dir_clustering_results, f"{dir_clustering_results}/Clusters", f"{dir_clustering_results}/Medoids"]:
            if not os.path.exists(d):
                os.makedirs(d, exist_ok=True)
        nbr_pool = 10
        for nb_itemset_min in list_itemset_min:
            for gap_min in list_gap_min:
                for gap_max in list_gap_max:
                    for minsup_percent in list_minsup_percent:
                        _check_cancel()
                        # Vérifier que le fichier des motifs clos existe et n'est pas vide
                        closed_pattern_file = f"{dir_patterns_results}/Closed/{args}_DMT4_merged_files_sorted_closed.pk"
                        if not os.path.exists(closed_pattern_file):
                            _log(f"⚠ Fichier de motifs clos manquant: {closed_pattern_file}", level=0)
                            _log("Le clustering ne peut pas être effectué sans motifs clos.", level=0)
                            continue
                        
                        file_size = os.path.getsize(closed_pattern_file)
                        _log(f"Fichier de motifs clos: {closed_pattern_file} ({file_size} bytes)", level=2)
                        
                        if not os.path.exists(f"{dir_clustering_results}/Clusters/{args}_clustering_3.pk"):
                            _log("Exécution du clustering interne...", level=1)
                            # Rediriger stdout pour capturer les outputs du clustering
                            import io
                            old_stdout = sys.stdout
                            sys.stdout = io.StringIO()
                            try:
                                execute_internal_clustering.main(nbr_pool, args, dir_clustering_results, dir_patterns_results)
                                clustering_output = sys.stdout.getvalue()
                                # Rediriger chaque ligne vers le log
                                for line in clustering_output.split('\n'):
                                    if line.strip():
                                        _log(line, level=2)
                            finally:
                                sys.stdout = old_stdout
                        else:
                            _log("-" * 75, level=2)
                            _log("4.bis Clustering interne : fichier de clusters déjà existant.", level=1)
                            
        end_time = time.time()
        time_clustering = end_time - start_time
    
    # ==================================
    # 5 - Calcul statistiques (CQP + R)
    # ==================================
    
    _progress("Calcul statistiques (CQP + R)", 75)
    start_time = time.time()
    _check_cancel()
    for d in [f"{dir_patterns_results}/Specifs/", f"{dir_patterns_results}/R"]:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
    _log("-" * 75, level=0)
    _log("5. Calcul statistique des motifs caractéristiques", level=0)
    
    # Rediriger stdout vers le log pour capturer les messages des scripts
    with StdoutLogger(log_callback, level=2):
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
            _check_cancel()
            for nb_itemset_min in list_itemset_min:
                for gap_min in list_gap_min:
                    for gap_max in list_gap_max:
                        _check_cancel()
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
                            _check_cancel()
                            _log(f"Minsup: {minsup_percent}%", level=1)
                            path_out = f"{path_R}minsup{str(minsup_percent)}/"
                            if os.path.exists(path_out):
                                for dir in os.listdir(path_out):
                                    _log(f"Déjà calculé {dir}", level=2)
                                    fichiers = sorted(os.listdir(path_out + dir), key=lambda f: os.path.getmtime(os.path.join(path_out + dir, f)), reverse=True)
                                    # Filtrer pour ne garder que les fichiers avec timestamps valides
                                    fichiers = [f for f in fichiers if is_valid_timestamp_filename(f)]
                                    for f in fichiers:
                                        if "motifsTexte_" in f:
                                            file_path = path_out + dir + "/" + f
                                            # Vérifier que le fichier n'est pas vide/corrompu
                                            try:
                                                # Lire le fichier pour vérifier qu'il est valide
                                                df_test = pd.read_csv(file_path, sep="\t", index_col=0, nrows=1)
                                                if df_test.empty or len(df_test.columns) == 0:
                                                    _log(f"⚠️  Fichier corrompu détecté (vide ou sans colonnes) : {file_path}", level=0)
                                                    _log(f"   Recalcul nécessaire...", level=0)
                                                    break  # Sortir de la boucle pour forcer le recalcul
                                            except Exception as e:
                                                _log(f"⚠️  Erreur lecture fichier existant : {file_path}", level=0)
                                                _log(f"   {str(e)}", level=1)
                                                _log(f"   Recalcul nécessaire...", level=0)
                                                break  # Sortir de la boucle pour forcer le recalcul
                                            
                                            if internal_clustering:
                                                if "_FUS" in f:
                                                    results[f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"] = file_path
                                                else:
                                                    df_k = pd.read_csv(file_path, sep="\t", index_col=0)
                                                    path_input = f"{dir_lexiques}/dico_str_to_int_all_items.pk"
                                                    path_output = f"{dir_lexiques}/dico_int_to_str_all_items.pk"
                                                    lexic_int_str = formate_patterns.make_dict_int_to_str(path_input, path_output)
                                                    df_k = compute_CQP.fusion_internal_clusters(df_k, lexic_int_str, args, dir_clustering_results)
                                                    f_fus = f[:-4] + "_FUS.tsv"
                                                    df_k.to_csv(path_out + dir + "/" + f_fus, sep="\t")
                                                    results[f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"] = path_out + dir + "/" + f_fus
                                            else:
                                                results[f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"] = file_path
                                            break
                            else:
                                _log("Calcul en cours...", level=1)
                                results, path_out = compute_CQP.main(textes, minsup_percent, gap_min, gap_max, nb_itemset_min, specifs, df_metadata, modif, metadata, internal_clustering, results, path_out, mode, args, dir_clustering_results, dir_patterns_results, registry_path, dir_lexiques)
        
        for metadata in list_metadata:
            _check_cancel()
            _log(metadata, level=2)
            if not os.path.exists(f"{dir_patterns_results}/R/{metadata}"):
                os.makedirs(f"{dir_patterns_results}/R/{metadata}", exist_ok=True)
            
            # POS
            _log("pos", level=2)
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
                            _log(f"⚠️  Aucun fichier POS valide trouvé, recalcul nécessaire...", level=0)
                            file_out_pos, path_out, df_pos, file_total = compute_CQP.compute_freq_TextesPos_AFC(execution_time, path_pos, registry_path)
                    else:
                        file_out_pos, path_out, df_pos, file_total = compute_CQP.compute_freq_TextesPos_AFC(execution_time, path_pos, registry_path)
                    df_pos = compute_CQP.textes2metadata(df_pos, df_metadata, metadata).T
                else:
                    file_out_pos, path_out, df_pos, file_total = compute_CQP.compute_freq_TextesPos_AFC(execution_time, path_pos, registry_path)
                df_pos.to_csv(file_out_pos, sep="\t")
                _log(f"file_out_pos : {file_out_pos}", level=2)
                if mode == "auto":
                    subprocess.call(["Rscript", "./src/AFC.R", file_out_pos, path_out])
                df_pos = compute_CQP.add_total(df_pos)
                df_pos.to_csv(file_total, sep="\t")
                results[f"{metadata}_pos"] = file_out_pos
            else:
                _log(f"Le fichier de résultats pour POS existe déjà", level=1)
                doss = f"{dir_patterns_results}/R/{metadata}/pos/"
                liste = [doss + f for f in os.listdir(doss) if "posTexte_" in f and is_valid_timestamp_filename(f)]
                tri = sorted(liste, key=os.path.getmtime, reverse=True)
                if tri:
                    results[f"{metadata}_pos"] = tri[0]
                else:
                    _log(f"⚠ Aucun fichier POS trouvé dans {doss}", level=0)
        
        # Lemma
        for seuil in liste_seuils_lemma:
            _log(f"{seuil}lemma{downhill_pos4lemma}", level=2)
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
                            _log(f"⚠️  Aucun fichier Lemma valide trouvé, recalcul nécessaire...", level=0)
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
                _log(f"already computed {seuil}lemma{downhill_pos4lemma}", level=1)
                doss = f"{dir_patterns_results}/R/{metadata}/{seuil}lemma{downhill_pos4lemma}/"
                liste = [doss + f for f in os.listdir(doss) if f"{seuil}lemma{downhill_pos4lemma}Texte_" in f and is_valid_timestamp_filename(f)]
                tri = sorted(liste, key=os.path.getmtime, reverse=True)
                if tri:
                    results[f"{metadata}_{seuil}lemma{downhill_pos4lemma}"] = tri[0]
                else:
                    _log(f"⚠ Aucun fichier Lemma trouvé dans {doss}", level=0)
        
        # Bigrams
        for seuil in liste_seuils_bigrams:
            _log(f"{seuil}bigrams", level=2)
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
                            _log(f"⚠️  Aucun fichier Bigrams valide trouvé, recalcul nécessaire...", level=0)
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
                _log(f"already computed {seuil}bigrams", level=1)
                doss = f"{dir_patterns_results}/R/{metadata}/{seuil}bigramslemma/"
                liste = [doss + f for f in os.listdir(doss) if "bigramslemmaTexte_" in f and is_valid_timestamp_filename(f)]
                tri = sorted(liste, key=os.path.getmtime, reverse=True)
                if tri:
                    results[f"{metadata}_{seuil}bigramslemma"] = tri[0]
                else:
                    _log(f"⚠ Aucun fichier Bigrams trouvé dans {doss}", level=0)

        _log(str(results), level=3)
        
        # Réinitialiser les paramètres aux premières valeurs pour la section POS/Lemma/Bigrams
        nb_itemset_min = list_itemset_min[0] if list_itemset_min else 3
        gap_min = list_gap_min[0] if list_gap_min else 0
        gap_max = list_gap_max[0] if list_gap_max else 0
        minsup_percent = list_minsup_percent[0] if list_minsup_percent else 25
        
        end_time = time.time()
        time_stats = end_time - start_time
    
    _check_cancel()
    _progress("Analyse terminée", 100)
    
    # Calculer le temps total de l'analyse
    end_time_total = time.time()
    time_total = end_time_total - start_time_total
    
    # Afficher les temps dans les logs (mode auto et gui)
    if mode in ["auto", "gui"]:
        _log(f"Temps total d'annotation (Stanza) : {format_time(time_tag)}", level=1)
        _log(f"Temps d'extraction des motifs : {format_time(time_DMT4)}", level=1)
        _log(f"Temps de calcul statistique : {format_time(time_stats)}", level=1)
        if internal_clustering:
            _log(f"Temps de clustering interne : {format_time(time_clustering)}", level=1)
        _log(f"="*75, level=0)
        _log(f"⏱️  TEMPS TOTAL DE L'ANALYSE : {format_time(time_total)}", level=0)
        _log(f"="*75, level=0)
    
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
