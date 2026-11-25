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
import unicodedata
import hashlib
import pickle
import ast
import inspect

from analysis_cache import file_fingerprint, paths_fingerprint, content_fingerprint

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


ANNOTATION_CACHE_VERSION = 2


def _file_signature(path: Path) -> dict:
    """Identifie le contenu, même si la taille et la date sont conservées."""
    return file_fingerprint(path)


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

    for key in ("pipeline_version", "selected_corpus", "annotator", "language", "actual_model_name", "use_gpu", "runtime", "code"):
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
    expected_outputs = cache_info.get("outputs")
    return bool(expected_outputs) and expected_outputs == paths_fingerprint(
        [tagged_dir, underscore_dir]
    )


def _write_annotation_cache_info(cache_paths: dict, cache_info: dict) -> None:
    cache_paths["root"].mkdir(parents=True, exist_ok=True)
    cache_info["outputs"] = paths_fingerprint(
        [cache_paths["tagged"], cache_paths["underscore_fix"]]
    )
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


def _conllu_files(source_dir: Path, recursive: bool = False) -> list[Path]:
    """Liste les textes en excluant les fichiers annexes des archives macOS."""
    pattern = source_dir.rglob("*.conllu") if recursive else source_dir.glob("*.conllu")
    return sorted(
        path for path in pattern
        if path.is_file() and not any(
            part == "__MACOSX" or part.startswith("._")
            for part in path.relative_to(source_dir).parts
        )
    )


def _copy_conllu_files(source_dir: Path, destination_dir: Path, recursive: bool = False, metadata_ids=()) -> list[str]:
    """Copie les fichiers .conllu d'un dossier vers un autre et retourne leurs stems."""
    conllu_files = _conllu_files(source_dir, recursive)
    if not conllu_files:
        raise FileNotFoundError(f"Aucun fichier .conllu trouvé dans {source_dir}")

    exact_ids = set(map(str, metadata_ids))
    canonical_ids = {}
    for text_id in exact_ids:
        canonical_ids.setdefault(unicodedata.normalize("NFC", text_id), set()).add(text_id)
    copies = []
    for path in conllu_files:
        text_id = path.stem
        if text_id not in exact_ids:
            matches = canonical_ids.get(unicodedata.normalize("NFC", text_id), set())
            if not matches:
                # Some ZIP creators write UTF-8 bytes without setting the ZIP
                # Unicode flag. Repair only a name confirmed by the metadata.
                try:
                    decoded = text_id.encode("cp437").decode("utf-8")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    decoded = text_id
                matches = canonical_ids.get(unicodedata.normalize("NFC", decoded), set())
            if len(matches) > 1:
                raise ValueError(f"Identifiant de texte ambigu dans les métadonnées : {text_id}")
            if matches:
                text_id = next(iter(matches))
        copies.append((path, text_id))
    if len({unicodedata.normalize("NFC", text_id) for _, text_id in copies}) != len(copies):
        raise ValueError("Plusieurs fichiers importés portent le même identifiant de texte.")

    destination_dir.mkdir(parents=True, exist_ok=True)
    for existing in destination_dir.glob("*.conllu"):
        existing.unlink()

    stems = []
    for path, text_id in copies:
        target = destination_dir / f"{text_id}.conllu"
        shutil.copy2(path, target)
        stems.append(text_id)
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
    """Préfère le dossier de textes à un éventuel dossier d'emballage homonyme."""
    lowered = {name.lower() for name in dir_names}
    candidates = []
    for candidate in sorted(base_dir.rglob("*")):
        if not candidate.is_dir() or candidate.name.lower() not in lowered:
            continue
        if any(part == "__MACOSX" or part.startswith("._")
               for part in candidate.relative_to(base_dir).parts):
            continue
        candidates.append(candidate)
        if _conllu_files(candidate):
            return candidate
    return candidates[0] if candidates else None


def build_pattern_key(nb_itemset_min, minsup_percent, gap_min, gap_max, restriction=None):
    """Utilise la même identité dans l'extraction, le clustering et les statistiques."""
    key = f"{nb_itemset_min}_{float(minsup_percent):.15g}_{gap_min}_{gap_max}"
    if restriction:
        encoded = json.dumps(restriction, sort_keys=True, ensure_ascii=False).encode("utf-8")
        key = f"selected_{hashlib.sha256(encoded).hexdigest()[:20]}_{key}"
    return key


def _reset_generated_directory(directory):
    directory = Path(directory)
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True, exist_ok=True)


def _validate_pickle(path, expected_type=dict):
    with open(path, "rb") as stream:
        value = pickle.load(stream)
    if not isinstance(value, expected_type):
        raise ValueError(f"Résultat invalide : {path}")
    return value


def _validate_matrix(path):
    table = pd.read_csv(path, sep="\t", index_col=0, quoting=3)
    if not len(table.columns) or table.index.has_duplicates:
        raise ValueError(f"Tableau incomplet : {path}")
    table.apply(pd.to_numeric, errors="raise")
    return table


def _stage_provenance(cache, modules, runtime_fields, functions=()):
    """Select only the implementation and tools used by this computation."""
    recorded_code = cache.run_inputs.get("code", {})
    code = {module: value["sha256"] for module in modules for path, value in recorded_code.items()
            if (Path(path).name == module or str(Path(path)).endswith("/" + module))
            and isinstance(value, dict) and "sha256" in value}
    if not code and recorded_code and not any(Path(path).suffix for path in recorded_code):
        code = recorded_code
    helpers = {function.__name__: ast.dump(ast.parse(inspect.getsource(function)), include_attributes=False)
               for function in functions}
    runtime = cache.run_inputs.get("runtime", {})
    selected = {}
    for field in ("python", *runtime_fields):
        value = runtime
        for part in field.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if value is not None:
            selected[field] = value
    if not selected and runtime:
        selected = runtime
    def content_only(value):
        if isinstance(value, dict):
            return {key: content_only(item) for key, item in value.items() if key != "path"}
        return value
    selected = content_only(selected)
    signature = {"version": 2, "code": code, "helpers": helpers, "runtime": selected}
    return hashlib.sha256(json.dumps(signature, sort_keys=True).encode("utf-8")).hexdigest()


def _reuse_preparation(cache, name, inputs, dependencies, log):
    record = cache.state["stages"].get(name)
    if record and cache.stage_valid(name, inputs, record["outputs"], dependencies):
        return cache.get_stage_result(name)
    candidate = cache.find_reusable_stage(name, inputs, dependencies)
    if candidate:
        result = cache.adopt_stage(name, inputs, candidate, dependencies)
        log(f"{name} : résultats vérifiés réutilisés depuis {Path(candidate['root']).name}.", level=1)
        return result
    return None


def _reuse_result_files(cache, name, inputs, outputs, dependencies, log):
    if cache.stage_valid(name, inputs, outputs, dependencies):
        return True
    candidate = cache.find_reusable_stage(name, inputs, dependencies)
    if candidate:
        cache.restore_stage_files(name, inputs, candidate, outputs, dependencies)
        log(f"{name} : résultats vérifiés réutilisés depuis {Path(candidate['root']).name}.", level=1)
        return True
    return False


def run_analysis(config, progress_callback=None, log_callback=None, paths=None, should_stop_callback=None, analysis_cache=None):
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
    
    # Les chemins sont toujours fournis par la GUI via create_analysis_structure()
    if not paths:
        raise ValueError("Les chemins d'analyse doivent être fournis via le paramètre 'paths'")

    if analysis_cache is None:
        from analysis_cache import AnalysisCache, FileLock, build_run_inputs, atomic_json, snapshot_file

        with FileLock(project_root / "logs" / ".pipeline.lock"), AnalysisCache(paths["root"]) as cache:
            if should_stop_callback and should_stop_callback():
                raise AnalysisCancelled("Analyse arrêtée par l'utilisateur.")
            run_inputs = build_run_inputs(project_root, config)
            cache.run_inputs = run_inputs
            # Other entry modes also generate reports or launch Shiny as a
            # side effect. Their full output set is outside the GUI cache.
            cache.cacheable = run_inputs["cacheable"] and config.get("mode") == "gui"
            previous = cache.completed_results(run_inputs)
            if previous is not None:
                if should_stop_callback and should_stop_callback():
                    raise AnalysisCancelled("Analyse arrêtée par l'utilisateur.")
                if log_callback:
                    log_callback(format_log_message(0, "Analyse complète vérifiée : résultats réutilisés."))
                if progress_callback:
                    progress_callback("Résultats existants vérifiés", 100)
                imported = cache.state["stages"].get("import", {}).get("result") or {}
                if imported.get("model"):
                    config["actual_model_name"] = imported["model"]
                return previous
            if not run_inputs["cacheable"] and log_callback:
                log_callback(format_log_message(0, "Provenance incomplète : les étapes seront recalculées."))
            runtime_config = dict(config)
            metadata_source = Path(_resolve_user_path(config.get("path_metadata"), "Data/Corpus/metadata.tsv"))
            metadata_snapshot = Path(paths["root"]) / "metadata.tsv"
            snapshot_file(metadata_source, metadata_snapshot)
            runtime_config["path_metadata"] = str(metadata_snapshot)
            results = run_analysis(
                runtime_config, progress_callback, log_callback, paths,
                should_stop_callback, analysis_cache=cache,
            )
            final_inputs = build_run_inputs(project_root, config)
            changed_inputs = any(final_inputs.get(key) != run_inputs.get(key)
                                 for key in ("configuration", "sources", "code"))
            if changed_inputs or (run_inputs["cacheable"] and final_inputs != run_inputs):
                cache.invalidate_all()
                raise RuntimeError("Les entrées ont changé pendant le calcul. Relancez l'analyse.")
            if should_stop_callback and should_stop_callback():
                raise AnalysisCancelled("Analyse arrêtée par l'utilisateur.")
            cache.complete_run(run_inputs, results)
            atomic_json(Path(paths["root"]) / "results_for_shiny.json", results)
            if "actual_model_name" in runtime_config:
                config["actual_model_name"] = runtime_config["actual_model_name"]
            return results

    # This environment is shared by the CQP helpers and is set under the lock.
    bin_path = str(project_root / "bin")
    os.environ["PATH"] = f"{bin_path}:{os.environ.get('PATH', '')}"
    
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
    automatic_selection = earlySelection and not user_input_list
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

    stage_common = {
        key: hashlib.sha256(json.dumps(analysis_cache.run_inputs.get(key), sort_keys=True).encode("utf-8")).hexdigest()
        for key in ("code", "runtime")
    }
    metadata_preview = pd.read_csv(path_metadata, sep="\t", index_col=0, dtype=str)
    if metadata_preview.index.astype(str).str.normalize("NFC").has_duplicates:
        raise ValueError("Le fichier de métadonnées contient des identifiants en double.")
    required_metadata = set(list_metadata) - {"id"}
    if automatic_selection and filter_specifs:
        required_metadata.add(partition_cible)
    missing_metadata = required_metadata - set(metadata_preview.columns)
    if missing_metadata:
        raise ValueError("Métadonnées introuvables : " + ", ".join(sorted(missing_metadata)))
    if not list_metadata or not all((list_itemset_min, list_gap_min, list_gap_max, list_minsup_percent)):
        raise ValueError("Sélectionnez une métadonnée et des paramètres de motifs complets.")

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
    source_paths = analysis_cache.run_inputs.get("sources", {}).get("corpus", {})
    source_content = content_fingerprint(source_paths) if source_paths else {}
    if input_type == "prepared_zip" and len(source_content) == 1:
        source_content = next(iter(source_content.values()))
    annotation_fields = ("annotator", "model_name", "model", "formatter", "installed_versions", "environment") if input_type == "raw_txt" else ()
    import_modules = ("replace_underscore.py", "base.py", "spacy_annotator.py", "stanza_annotator.py")
    if input_type == "raw_txt":
        import_modules += ("annotators/__init__.py",)
    import_inputs = {
        "implementation": _stage_provenance(
            analysis_cache, import_modules,
            annotation_fields, (_conllu_files, _copy_conllu_files, _generate_underscore_fix, _find_first_matching_directory),
        ),
        "sources": source_content,
        "input_type": input_type,
        "metadata_ids": sorted(metadata_preview.index.astype(str)),
    }
    if input_type == "raw_txt":
        import_inputs["annotation"] = [annotator_name, language, use_gpu]
    import_outputs = [dir_tagged, dir_underscore_fix]
    imported = _reuse_preparation(analysis_cache, "import", import_inputs, (), _log)
    if imported is not None:
        dir_tagged = imported["tagged"]
        dir_underscore_fix = imported["underscore_fix"]
        textes = imported["texts"]
        actual_model_name = imported["model"]
        import_outputs = list(analysis_cache.state["stages"]["import"]["outputs"])
        _log("Import vérifié : corpus annoté et correction réutilisés.", level=1)
    elif input_type == "raw_txt":
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
            "runtime": stage_common["runtime"],
            "code": stage_common["code"],
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
        analysis_cache.begin_stage("import")
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
            textes = _copy_conllu_files(imported_path, tagged_dir_path, metadata_ids=metadata_preview.index)
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
                textes = _copy_conllu_files(tagged_source, tagged_dir_path, recursive=True, metadata_ids=metadata_preview.index)
            else:
                textes = []

            if underscore_source:
                underscore_textes = _copy_conllu_files(underscore_source, underscore_dir_path, recursive=True, metadata_ids=metadata_preview.index)
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

    if imported is None and input_type == "raw_txt":
        import_outputs = [dir_tagged, dir_underscore_fix]
    if imported is None:
        analysis_cache.begin_stage("import")
        analysis_cache.complete_stage(
            "import", import_inputs, import_outputs,
            result={"tagged": dir_tagged, "underscore_fix": dir_underscore_fix,
                    "texts": textes, "model": actual_model_name},
        )

    missing_ids = {unicodedata.normalize("NFC", name) for name in textes} - set(metadata_preview.index.astype(str).str.normalize("NFC"))
    if missing_ids:
        raise ValueError("Textes absents des métadonnées : " + ", ".join(sorted(missing_ids)))

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
    
    dmt4_inputs = {
        "implementation": _stage_provenance(
            analysis_cache, ("conll_dmt4.py", "formate_patterns.py", "tools.py"), ("packages.pandas", "packages.numpy"),
            (_validate_pickle,),
        ),
        "source": content_fingerprint([dir_underscore_fix]),
        "attributes": [Form, Lemma, Pos, Dep, Feats],
    }
    dmt4_outputs = [dir_dmt4_files, dir_lexiques]
    prepared = _reuse_preparation(analysis_cache, "dmt4", dmt4_inputs, ("import",), _log)
    if prepared is not None:
        dir_dmt4_files = prepared["dmt4_files"]
        dir_lexiques = prepared["lexiques"]
        _log("DMT4 et lexiques vérifiés : réutilisation.", level=1)
    else:
        analysis_cache.begin_stage("dmt4")
        for directory in (dir_tagged_for_dmt4, dir_dmt4_files, dir_lexiques):
            _reset_generated_directory(directory)
        for texte in textes:
            _check_cancel()
            shutil.copy2(Path(dir_underscore_fix) / f"{texte}.conllu", dir_tagged_for_dmt4)
        preparation = dir_tagged_for_dmt4.rstrip("/") + "/"
        conll_dmt4.instancier_dict(preparation, dir_lexiques)
        lexicon = _validate_pickle(Path(dir_lexiques) / "dico_str_to_int_all_items.pk")
        if not lexicon:
            raise ValueError("Le lexique DMT4 est vide.")
        file_list = sorted(path.name for path in Path(dir_tagged_for_dmt4).glob("*.conllu"))
        tools.concat_multiple_conll(preparation, file_list, "merged")
        conll_dmt4.transform_data(preparation, "merged", Form, Lemma, Pos, Dep, Feats, dir_dmt4_files, dir_lexiques)
        conll_dmt4.sort_dmtfiles(dir_dmt4_files.rstrip("/") + "/")
        conll_dmt4.make_DMT4_file("merged", dir_dmt4_files)
        sorted_dmt4 = Path(dir_dmt4_files) / "DMT4_merged_files_sorted.txt"
        if not sorted_dmt4.is_file() or sorted_dmt4.stat().st_size == 0:
            raise ValueError("La préparation DMT4 n'a produit aucune séquence exploitable.")
        formate_patterns.make_dict_int_to_str(
            str(Path(dir_lexiques) / "dico_str_to_int_all_items.pk"),
            str(Path(dir_lexiques) / "dico_int_to_str_all_items.pk"),
        )
        analysis_cache.complete_stage(
            "dmt4", dmt4_inputs, dmt4_outputs, dependencies=("import",),
            result={"dmt4_files": dir_dmt4_files, "lexiques": dir_lexiques},
        )

    vrt_inputs = {
        "implementation": _stage_provenance(analysis_cache, ("conllu2vrt.py",), ("packages.conllu",)),
        "source": content_fingerprint([dir_tagged]),
    }
    converted = _reuse_preparation(analysis_cache, "vrt", vrt_inputs, ("import",), _log)
    if converted is not None:
        dir_textes_vrt = converted["textes_vrt"]
        _log("VRT vérifié : réutilisation.", level=1)
    else:
        analysis_cache.begin_stage("vrt")
        _reset_generated_directory(dir_textes_vrt)
        _check_cancel()
        with StdoutLogger(log_callback, level=2):
            conllu2vrt.transform(dir_tagged.rstrip("/") + "/", dir_textes_vrt.rstrip("/") + "/")
        merged_vrt = Path(dir_textes_vrt) / "merged.vrt"
        if not merged_vrt.is_file() or not merged_vrt.stat().st_size:
            raise RuntimeError("La conversion VRT est incomplète.")
        analysis_cache.complete_stage("vrt", vrt_inputs, [dir_textes_vrt], dependencies=("import",),
                                      result={"textes_vrt": dir_textes_vrt})

    cwb_inputs = {
        "implementation": _stage_provenance(
            analysis_cache, ("cwb.py",),
            ("tools.cwb-encode", "tools.cwb-makeall", "tools.native_cwb-encode", "tools.native_cwb-makeall", "wrappers", "docker_images"),
        ),
        "source": content_fingerprint([dir_textes_vrt]),
    }
    indexed = _reuse_preparation(analysis_cache, "cwb", cwb_inputs, ("vrt",), _log)
    if indexed is not None:
        dir_cwb_corpus = indexed["cwb_corpus"]
        _log("Index CWB vérifié : réutilisation.", level=1)
    else:
        analysis_cache.begin_stage("cwb")
        _reset_generated_directory(dir_cwb_corpus)
        _check_cancel()
        with StdoutLogger(log_callback, level=2):
            cwb.main(dir_cwb_corpus, dir_textes_vrt)
        registry_file = Path(dir_cwb_corpus) / "registry" / "merged"
        index_files = list((Path(dir_cwb_corpus) / "data" / "merged").glob("*.corpus"))
        if not registry_file.is_file() or not registry_file.stat().st_size or not index_files:
            raise RuntimeError("L'index CWB est incomplet.")
        analysis_cache.complete_stage("cwb", cwb_inputs, [dir_cwb_corpus], dependencies=("vrt",),
                                      result={"cwb_corpus": dir_cwb_corpus})
    registry_path = str(Path(dir_cwb_corpus) / "registry")
    os.environ["CORPUS_REGISTRY_PATH"] = registry_path

    early_dependencies = []
    effective_restriction = []
    nom = ""
    if user_input_list:
        lexique = tools.load_pickles(str(Path(dir_lexiques) / "dico_str_to_int_all_items.pk"))
        manual_lemmas = config.get("liste_earlyselection_lemma", [])
        for lemma in manual_lemmas:
            encoded = f'lemma_"{lemma}"'
            if encoded not in lexique:
                raise ValueError(f"Lemme de sélection absent du corpus : {lemma}")
            effective_restriction.append(lexique[encoded])
        nom = hashlib.sha256(json.dumps(manual_lemmas, ensure_ascii=False).encode("utf-8")).hexdigest()[:20]
        _log("Lemmes ciblés (liste manuelle) : " + ", ".join(manual_lemmas), level=1)
    elif automatic_selection:
        _check_cancel()
        early_inputs = {
            **stage_common,
            "parameters": [seuil_early_selection, list_minsup_percent[0], partition_cible,
                           seuil_banalité, early_pos4lemma, filter_specifs],
            "metadata": file_fingerprint(Path(path_metadata)),
        }
        early_outputs = [dir_early_selection]
        early_dependencies = ["early_selection"]
        if analysis_cache.stage_valid("early_selection", early_inputs, early_outputs, dependencies=("dmt4", "cwb")):
            effective_restriction = analysis_cache.get_stage_result("early_selection")
            _log("Early selection vérifiée : réutilisation.", level=1)
        else:
            analysis_cache.begin_stage("early_selection")
            _reset_generated_directory(dir_early_selection)
            with StdoutLogger(log_callback, level=2):
                effective_restriction = early_selection.main(
                    seuil_early_selection, list_minsup_percent[0], path_metadata,
                    partition_cible, seuil_banalité, early_pos4lemma, filter_specifs,
                    path_out=dir_early_selection,
                    path_lexique=str(Path(dir_lexiques) / "dico_str_to_int_all_items.pk"),
                    registry_path=registry_path,
                )
            analysis_cache.complete_stage(
                "early_selection", early_inputs, early_outputs,
                dependencies=("dmt4", "cwb"), result=effective_restriction,
            )

    if (earlySelection or user_input_list) and not effective_restriction:
        raise ValueError("La sélection ne contient aucun lemme présent dans le corpus.")

    def pattern_key(nb_itemset_min, minsup_percent, gap_min, gap_max):
        return build_pattern_key(nb_itemset_min, minsup_percent, gap_min, gap_max, effective_restriction)

    # ==================================
    # 3 - Extraction des motifs
    # ==================================
    
    _log("-" * 75, level=0)
    _log("3. Extraction des motifs clos", level=0)
    _progress("Fouille de motifs (BideSpanTree)", 30)
    start_time = time.time()
    _check_cancel()
    
    path_results = dir_patterns_results
    if not os.path.exists(path_results):
        os.makedirs(path_results, exist_ok=True)
    path_file_closed = f"{dir_patterns_results}/Closed"
    if not os.path.exists(path_file_closed):
        os.makedirs(path_file_closed, exist_ok=True)
    
    extraction_stages = []
    extraction_signatures = {}
    for nb_itemset_min in list_itemset_min:
        for gap_min in list_gap_min:
            for gap_max in list_gap_max:
                for minsup_percent in list_minsup_percent:
                    _check_cancel()
                    args = pattern_key(nb_itemset_min, minsup_percent, gap_min, gap_max)
                    stage = f"extraction:{args}"
                    extraction_stages.append(stage)
                    closed_text = Path(dir_patterns_results) / "Closed" / f"{args}_DMT4_merged_files_sorted_closed.txt"
                    closed_pickle = closed_text.with_suffix(".pk")
                    extraction_outputs = [closed_text, closed_pickle]
                    extraction_inputs = {
                        "implementation": _stage_provenance(
                            analysis_cache, ("tools.py", "compute_emergent_sequential_patterns.py"), ("tools.bidespantree",),
                            (build_pattern_key, _validate_pickle),
                        ),
                        "dmt4": content_fingerprint([dir_dmt4_files, dir_lexiques]),
                        "attributes": [Form, Lemma, Pos, Dep, Feats],
                        "parameters": [nb_itemset_min, minsup_percent, gap_min, gap_max, threads],
                        "restriction": effective_restriction,
                    }
                    if effective_restriction:
                        # Older restricted runs could merge two OR lists under one cache key.
                        extraction_inputs["restriction_mode"] = "single_or"
                    extraction_signatures[args] = extraction_inputs
                    extraction_dependencies = ["dmt4", *early_dependencies]
                    if _reuse_result_files(analysis_cache, stage, extraction_inputs, extraction_outputs, extraction_dependencies, _log):
                        _log(f"Motifs clos vérifiés : réutilisation pour {args}.", level=1)
                    else:
                        analysis_cache.begin_stage(stage)
                        for output_file in extraction_outputs:
                            output_file.unlink(missing_ok=True)
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
                            if effective_restriction:
                                set_up.write("OR=" + ",".join(map(str, effective_restriction)) + "\n")
                        
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
                                _log(f"\t\t Aucun motif extrait pour {args}.", level=1)
                                if result.stderr:
                                    _log(f"\t\t Stderr: {result.stderr}", level=1)
                        except (FileNotFoundError, subprocess.CalledProcessError, PermissionError, OSError) as e:
                            # Si direct échoue, essayer Docker
                            _log(f"\t\t Exécution directe impossible ({type(e).__name__}), tentative avec Docker...", level=1)
                            # A fallback executor needs its own provenance before
                            # its results can become an automatic cache hit.
                            analysis_cache.cacheable = False
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
                            raise
                        _check_cancel()
                        compute_emergent_sequential_patterns.from_txt_to_dict(str(closed_text))
                        motifs = _validate_pickle(closed_pickle)
                        analysis_cache.complete_stage(
                            stage, extraction_inputs, extraction_outputs,
                            dependencies=extraction_dependencies, result={"motif_count": len(motifs)},
                        )

        end_time = time.time()
        time_DMT4 = end_time - start_time
    
    # ========================================
    # 4 - Calcul des motifs caractéristiques
    # ========================================
    
    _log("-" * 75, level=0)
    _log("4. Extraction des motifs caractéristiques", level=0)
    _progress("Calcul des motifs caractéristiques", 55)
    
    _log("Les dictionnaires de motifs clos sont validés avec leur extraction.", level=1)
    
    
    # ================================
    # 4.bis - Clustering interne
    # ================================
    
    clustering_stages = []
    time_clustering = 0
    if internal_clustering:
        _progress("Clustering interne", 60)
        start_time = time.time()
        for directory in (dir_clustering_results, Path(dir_clustering_results) / "Clusters", Path(dir_clustering_results) / "Medoids"):
            Path(directory).mkdir(parents=True, exist_ok=True)
        for nb_itemset_min in list_itemset_min:
            for gap_min in list_gap_min:
                for gap_max in list_gap_max:
                    for minsup_percent in list_minsup_percent:
                        _check_cancel()
                        args = pattern_key(nb_itemset_min, minsup_percent, gap_min, gap_max)
                        closed_pickle = Path(dir_patterns_results) / "Closed" / f"{args}_DMT4_merged_files_sorted_closed.pk"
                        motifs = _validate_pickle(closed_pickle)
                        stage = f"clustering:{args}"
                        clustering_stages.append(stage)
                        cluster_inputs = {
                            "implementation": _stage_provenance(
                                analysis_cache, ("mesure_S2MP.py", "regroupement.py", "execute_internal_clustering.py", "formate_patterns.py"),
                                ("packages.numpy", "packages.scipy", "packages.pandas"), (_validate_pickle,),
                            ),
                            "alignment": config.get("internal_clustering_alignment"),
                            "extraction": extraction_signatures[args],
                            "closed": content_fingerprint([closed_pickle]),
                        }
                        cluster_outputs = [
                            Path(dir_clustering_results) / folder / f"{args}_{suffix}_{level}.pk"
                            for level in (1, 2, 3)
                            for folder, suffix in (("Clusters", "clustering"), ("Medoids", "medoids"))
                        ] if motifs else []
                        dependencies = (f"extraction:{args}",)
                        if _reuse_result_files(analysis_cache, stage, cluster_inputs, cluster_outputs, dependencies, _log):
                            _log(f"Clusters et médoïdes vérifiés : réutilisation pour {args}.", level=1)
                            continue
                        analysis_cache.begin_stage(stage)
                        for output_file in cluster_outputs:
                            output_file.unlink(missing_ok=True)
                            output_file.with_suffix(".txt").unlink(missing_ok=True)
                        if motifs:
                            with StdoutLogger(log_callback, level=2):
                                execute_internal_clustering.main(10, args, dir_clustering_results, dir_patterns_results)
                            _check_cancel()
                            for output_file in cluster_outputs:
                                _validate_pickle(output_file)
                        analysis_cache.complete_stage(stage, cluster_inputs, cluster_outputs, dependencies=dependencies)
        time_clustering = time.time() - start_time

    # ==================================
    # 5 - Calcul statistiques (CQP + R)
    # ==================================
    
    _progress("Calcul statistiques (CQP + R)", 75)
    start_time = time.time()
    _check_cancel()
    statistics_inputs = {
        **stage_common,
        "metadata": file_fingerprint(Path(path_metadata)),
        "metadata_columns": list_metadata,
        "specifs": specifs,
        "internal_clustering": internal_clustering,
        "lemma_thresholds": liste_seuils_lemma,
        "lemma_pos": downhill_pos4lemma,
        "bigram_thresholds": liste_seuils_bigrams,
    }
    statistics_outputs = [
        Path(dir_patterns_results) / "R",
        Path(dir_patterns_results) / "Specifs",
        Path(dir_patterns_results) / "text_sizes.json",
        Path(path_metadata),
    ]
    statistics_dependencies = ["cwb", *extraction_stages, *clustering_stages]
    if analysis_cache.stage_valid("statistics", statistics_inputs, statistics_outputs, dependencies=statistics_dependencies):
        results = analysis_cache.get_stage_result("statistics")
        _log("Tableaux statistiques vérifiés : réutilisation.", level=1)
    else:
        analysis_cache.begin_stage("statistics")
        for directory in statistics_outputs[:2]:
            _reset_generated_directory(directory)
        statistics_outputs[2].unlink(missing_ok=True)
        results = {}
        with StdoutLogger(log_callback, level=2):
            df_metadata = pd.read_csv(path_metadata, sep="\t", index_col=0, dtype=str)
            import enslave_perl
            text_sizes = enslave_perl.save_text_sizes(str(statistics_outputs[2]))
            missing_texts = {unicodedata.normalize("NFC", name) for name in textes} - {unicodedata.normalize("NFC", name) for name in text_sizes[1]}
            if missing_texts:
                raise ValueError("Tailles CWB manquantes pour : " + ", ".join(sorted(missing_texts)))
            modif = ""
            if user_input_list:
                modif = f"user_input_list_{nom}_"
            elif automatic_selection:
                modif = f"{seuil_early_selection}early{early_pos4lemma}_specifs{filter_specifs}{partition_cible}_"
            if internal_clustering:
                modif += "internal_clustering_"
            metadata_order = sorted(list_metadata, key=lambda name: name != "id")
            for metadata in metadata_order:
                for nb_itemset_min in list_itemset_min:
                    for gap_min in list_gap_min:
                        for gap_max in list_gap_max:
                            for minsup_percent in list_minsup_percent:
                                _check_cancel()
                                args = pattern_key(nb_itemset_min, minsup_percent, gap_min, gap_max)
                                closed_pickle = Path(dir_patterns_results) / "Closed" / f"{args}_DMT4_merged_files_sorted_closed.pk"
                                if not _validate_pickle(closed_pickle):
                                    _log(f"Aucun motif pour {args} : résultat vide validé.", level=1)
                                    continue
                                path_out = (Path(dir_patterns_results) / "R" / metadata / f"{modif}motifs"
                                            / f"itemset_min{nb_itemset_min}" / f"gap_min{gap_min}_gap_max{gap_max}"
                                            / f"minsup{minsup_percent}")
                                path_out.mkdir(parents=True, exist_ok=True)
                                results, _ = compute_CQP.main(
                                    textes, minsup_percent, gap_min, gap_max, nb_itemset_min,
                                    specifs, df_metadata, modif, metadata, internal_clustering,
                                    results, str(path_out) + "/", mode, args,
                                    dir_clustering_results, dir_patterns_results, registry_path, dir_lexiques,
                                    text_sizes=text_sizes,
                                )
                                result_key = f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"
                                if result_key not in results:
                                    raise RuntimeError(f"Le calcul n'a pas produit le tableau demandé : {result_key}")
                                if specifs and f"{metadata}_specifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}" not in results:
                                    raise RuntimeError(f"Le calcul n'a pas produit les spécificités demandées pour {metadata}.")

            # Count each comparison representation once, then use the existing
            # metadata aggregation for each selected partition.
            representations = [("pos", "pos", None)]
            representations += [(f"{seuil}lemma{downhill_pos4lemma}", "lemma", seuil) for seuil in liste_seuils_lemma]
            representations += [(f"{seuil}bigramslemma", "bigrams", seuil) for seuil in liste_seuils_bigrams]
            comparison_counts = {}
            for metadata in metadata_order:
                for representation, kind, seuil in representations:
                    _check_cancel()
                    if representation not in comparison_counts:
                        comparison_dir = Path(dir_patterns_results) / "R" / metadata
                        comparison_dir.mkdir(parents=True, exist_ok=True)
                        base = str(comparison_dir) + "/"
                        execution_time = datetime.datetime.now()
                        if kind == "pos":
                            file_out, _, table, _ = compute_CQP.compute_freq_TextesPos_AFC(execution_time, base, registry_path)
                        elif kind == "lemma":
                            file_out, _, table, _ = compute_CQP.compute_freq_TextesLemma_AFC(seuil, execution_time, base, downhill_pos4lemma, registry_path)
                        else:
                            file_out, _, table = compute_CQP.compute_freq_Textes_BigramsLemma_noAFC(execution_time, base, seuil, registry_path)
                        comparison_counts[representation] = (table, Path(file_out).name)
                    raw_table, filename = comparison_counts[representation]
                    table = raw_table.copy() if metadata == "id" else compute_CQP.textes2metadata(raw_table, df_metadata, metadata).T
                    target_dir = Path(dir_patterns_results) / "R" / metadata / representation
                    target_dir.mkdir(parents=True, exist_ok=True)
                    file_out = target_dir / filename
                    table.to_csv(file_out, sep="\t")
                    if kind != "bigrams":
                        total_name = filename.replace("Texte_", "TexteOrdered_", 1)
                        compute_CQP.add_total(table).to_csv(target_dir / total_name, sep="\t")
                    results[f"{metadata}_{representation}"] = str(file_out)
                    if mode == "auto":
                        subprocess.run(["Rscript", str(Path(__file__).parent / "AFC.R"), str(file_out), str(target_dir)], check=True)
        _check_cancel()
        for file_out in results.values():
            _validate_matrix(file_out)
        analysis_cache.complete_stage(
            "statistics", statistics_inputs, statistics_outputs,
            dependencies=statistics_dependencies, result=results,
        )
    time_stats = time.time() - start_time

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
