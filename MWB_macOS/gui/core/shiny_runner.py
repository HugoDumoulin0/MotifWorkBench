"""
Préparation des résultats et lancement de Shiny pour une analyse sélectionnée.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import urlopen

from gui.core.analysis_paths import (
    get_analysis_root, list_analysis_group_names, list_configs_for_analysis_group,
)

_SHINY_PROCESS: subprocess.Popen | None = None
_SHINY_CONTEXT: tuple | None = None


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def last_results_json_path() -> Path:
    return project_root() / "logs" / "last_results_for_shiny.json"


def latest_analysis_root() -> Path | None:
    info = _read_json(project_root() / "logs" / "last_analysis.json")
    if info.get("analysis_group_name") and info.get("config_id"):
        return get_analysis_root(info["analysis_group_name"], info["config_id"]).resolve()
    patterns = info.get("patterns_results")
    return Path(patterns).resolve().parent if patterns else None


def _resolve_dataset_path(raw_path: str, root: Path) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        return root / path
    if path.is_relative_to(root):
        return path
    # A project can have moved since its old absolute-path manifest was saved.
    normalized = raw_path.replace("\\", "/")
    if "/Patterns_results/" in normalized:
        return root / "Patterns_results" / normalized.split("/Patterns_results/", 1)[1]
    return path


def _existing_datasets(mapping: dict, root: Path) -> dict[str, str]:
    datasets = {}
    for key, raw_path in mapping.items():
        if not isinstance(raw_path, str):
            continue
        path = _resolve_dataset_path(raw_path, root)
        if path.is_file() and path.stat().st_size:
            datasets[key] = str(path.resolve())
    return datasets


def save_results_for_shiny(
    results: dict[str, Any],
    analysis_root: str | Path | None = None,
    metadata_path: str | Path | None = None,
) -> Path:
    """Conserve les résultats de visualisation et le raccourci de dernière analyse."""
    if analysis_root is None:
        out = last_results_json_path()
        _write_json(out, results)
        return out

    root = Path(analysis_root).resolve()
    resolved = _existing_datasets(results, root)
    relative = {
        key: os.path.relpath(path, root)
        for key, path in resolved.items()
    }
    snapshot = root / "metadata.tsv"
    metadata = Path(metadata_path).expanduser() if metadata_path else None
    if metadata is not None and not metadata.is_absolute():
        metadata = project_root() / metadata
    if snapshot.is_file():
        metadata = snapshot
    context = {
        "schema_version": 1,
        "analysis_group_name": root.parent.name,
        "config_id": root.name,
        "analysis_root": str(root),
        "patterns_results": "Patterns_results",
        "metadata_path": os.path.relpath(metadata.resolve(), root) if metadata else None,
        "completed_at": datetime.now().isoformat(),
    }
    out = root / "results_for_shiny.json"
    _write_json(out, relative)
    _write_json(root / "shiny_context.json", context)
    _write_json(last_results_json_path(), resolved)
    _write_json(project_root() / "logs" / "last_analysis.json", {
        "analysis_group_name": root.parent.name,
        "config_id": root.name,
        "patterns_results": str(root / "Patterns_results"),
        "clustering_results": str(root / "Clustering_results"),
        "logs": str(project_root() / "logs"),
    })
    return out


def _motif_parameters(parts: tuple[str, ...]) -> str | None:
    directory = "/".join(parts)
    itemset = re.search(r"(?:^|/)itemset_min([^/]+)", directory)
    gapmin = re.search(r"(?:^|/)gap_min([^_/]+)", directory)
    gapmax = re.search(r"(?:^|[_/])gap_max([^/]+)", directory)
    minsup = re.search(r"(?:^|/)minsup([^/]+)", directory)
    if not all((itemset, gapmin, gapmax, minsup)):
        return None
    return "_".join(match.group(1) for match in (minsup, gapmin, gapmax, itemset))


def reconstruct_results_for_shiny(analysis_root: str | Path) -> dict[str, str]:
    """Retrouve les tableaux existants sans modifier le cache de calcul."""
    root = Path(analysis_root).resolve()
    config = _read_json(root / "analysis_info.json").get("config", {})
    candidates: dict[str, list[Path]] = {}
    matrices = root / "Patterns_results" / "R"
    for path in matrices.rglob("*Texte_df_*.tsv"):
        parts = path.relative_to(matrices).parts
        if len(parts) < 3 or not path.stat().st_size:
            continue
        metadata, representation = parts[:2]
        key = f"{metadata}_{representation}"
        if "motif" in representation.lower():
            suffix = _motif_parameters(parts)
            if suffix is None:
                continue
            needs_fused = config.get("internal_clustering", False) or "internal_clustering" in representation
            if needs_fused and not path.name.endswith("_FUS.tsv"):
                continue
            key += "_" + suffix
        candidates.setdefault(key, []).append(path)

    specifics = root / "Patterns_results" / "Specifs"
    for path in specifics.rglob("specif_*.tsv"):
        parts = path.relative_to(specifics).parts
        suffix = _motif_parameters(parts)
        if len(parts) < 3 or suffix is None or not path.stat().st_size:
            continue
        key = f"{parts[0]}_specifs_{suffix}"
        candidates.setdefault(key, []).append(path)

    return {
        key: str(max(paths, key=lambda path: (path.stat().st_mtime_ns, path.name)).resolve())
        for key, paths in candidates.items()
    }


def analysis_results_for_shiny(analysis_root: str | Path) -> dict[str, str]:
    root = Path(analysis_root).resolve()
    saved = _read_json(root / "results_for_shiny.json")
    if saved:
        datasets = _existing_datasets(saved, root)
        if datasets:
            return datasets
    if latest_analysis_root() == root:
        datasets = _existing_datasets(_read_json(last_results_json_path()), root)
        if datasets:
            return datasets
    return reconstruct_results_for_shiny(root)


def list_available_shiny_analyses() -> list[dict]:
    analyses = []
    for group in list_analysis_group_names():
        known = {info["config_id"]: info for info in list_configs_for_analysis_group(group)}
        group_root = get_analysis_root(group, "")
        for folder in sorted(group_root.iterdir(), reverse=True):
            if not folder.is_dir() or folder.name.startswith("."):
                continue
            info = known.get(folder.name, {"config_id": folder.name, "created_at": "", "config": {}})
            root = folder.resolve()
            try:
                datasets = analysis_results_for_shiny(root)
            except OSError:
                # A running analysis can replace its output files during refresh.
                continue
            if datasets:
                analyses.append({
                    **info,
                    "analysis_group_name": group,
                    "analysis_root": str(root),
                })
    return sorted(analyses, key=lambda entry: entry["config_id"], reverse=True)


def _file_content(path: Path) -> dict:
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat()
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if any(getattr(before, field) != getattr(after, field) for field in fields):
        raise OSError(f"Le tableau a changé pendant sa lecture : {path}")
    return {"size": after.st_size, "sha256": digest.hexdigest()}


def _compatible_view(root: Path) -> tuple[dict, dict] | None:
    """Identify comparable saved results, without certifying computation reuse.

    Only support and gaps may differ. Missing provenance keeps older analyses
    available individually, rather than assuming that their corpora still match.
    """
    state = _read_json(root / ".analysis_cache.json")
    completed = state.get("completed", {})
    try:
        if state.get("version") != 1:
            return None
        inputs = json.loads(completed["inputs"])
        if inputs.get("cacheable") is not True:
            return None
        config = json.loads(inputs["configuration"])
        for key in ("list_minsup_percent", "list_gap_min", "list_gap_max"):
            config.pop(key, None)
        metadata = _file_content(root / "metadata.tsv")
        expected_metadata = inputs["sources"]["metadata"]
        if any(metadata[key] != expected_metadata[key] for key in metadata):
            return None
        sizes_path = root / "Patterns_results" / "text_sizes.json"
        statistics = state["stages"]["statistics"]
        if statistics.get("success") is not True:
            return None
        sizes_fingerprint = _file_content(sizes_path)
        recorded_sizes = next((value for path, value in statistics["outputs"].items()
                               if _resolve_dataset_path(path, root).resolve() == sizes_path.resolve()), {})
        if any(sizes_fingerprint[key] != recorded_sizes.get(key) for key in sizes_fingerprint):
            return None
        sizes = _read_json(sizes_path)
        if not sizes.get("texts"):
            return None
        # Viewer changes do not change the scientific meaning of saved tables.
        code = {
            path.replace("\\", "/").split("/src/", 1)[1]: value["sha256"]
            for path, value in inputs["code"].items()
            if "/src/" in path.replace("\\", "/") and Path(path).name != "Shiny_CA.R"
        }
        if not code or not completed["results"] or not completed["outputs"]:
            return None
        signature = {
            "configuration": config, "sources": inputs["sources"],
            "code": code, "runtime": inputs["runtime"],
            "metadata": metadata, "text_sizes": sizes,
        }
        return signature, completed
    except (OSError, AttributeError, KeyError, TypeError, ValueError):
        return None


def _verified_view_tables(root: Path, datasets: dict, completed: dict) -> bool:
    """Check just the displayed tables against their saved completion record."""
    try:
        for key, path in datasets.items():
            recorded = completed["results"][key]
            if Path(path) != _resolve_dataset_path(recorded, root).resolve():
                return False
            expected = completed["outputs"][recorded]
            actual = _file_content(Path(path))
            if any(actual[field] != expected[field] for field in actual):
                return False
        return True
    except (OSError, KeyError, TypeError, ValueError):
        return False


def _support_gap_tables(root: Path, datasets: dict) -> dict:
    """Expose completed compatible variants through the existing R selectors."""
    selected = _compatible_view(root)
    if selected is None:
        return datasets
    signature, completed = selected
    if not _verified_view_tables(root, datasets, completed):
        return datasets
    combined = dict(datasets)
    for sibling in sorted(root.parent.iterdir(), reverse=True):
        if not sibling.is_dir() or sibling == root or sibling.name.startswith("."):
            continue
        other = _compatible_view(sibling)
        if other is None or other[0] != signature:
            continue
        try:
            candidates = analysis_results_for_shiny(sibling)
        except OSError:
            continue
        if not candidates or not _verified_view_tables(sibling, candidates, other[1]):
            continue
        for key, path in candidates.items():
            # Repeated representations (POS, lemmas, etc.) stay with the selected
            # analysis; each additional motif/specificity key retains its source.
            combined.setdefault(key, path)
    return combined


def prepare_analysis_for_shiny(analysis_root: str | Path) -> Path:
    root = Path(analysis_root).resolve()
    datasets = analysis_results_for_shiny(root)
    if not datasets:
        raise FileNotFoundError("Aucun tableau de résultats disponible pour cette analyse.")
    # A recovered visualization manifest never certifies pipeline reuse.
    out = root / "results_for_shiny.json"
    relative = {key: os.path.relpath(path, root) for key, path in datasets.items()}
    if _read_json(out) != relative:
        _write_json(out, relative)
    combined = _support_gap_tables(root, datasets)
    if combined != datasets:
        # Keep the original per-run manifest authoritative. Relative sibling
        # paths also survive moving the whole project to another location.
        out = root / "shiny_selection.json"
        relative = {key: os.path.relpath(path, root) for key, path in combined.items()}
        if _read_json(out) != relative:
            _write_json(out, relative)
    return out


def shiny_url(host: str = "127.0.0.1", port: int = 3838) -> str:
    return f"http://{host}:{port}"


def is_shiny_responding(host: str = "127.0.0.1", port: int = 3838, timeout: float = 1.0) -> bool:
    try:
        with urlopen(shiny_url(host, port), timeout=timeout) as response:
            return response.status == 200
    except (URLError, OSError):
        return False


def is_shiny_running(host: str = "127.0.0.1", port: int = 3838) -> bool:
    return _SHINY_PROCESS is not None and _SHINY_PROCESS.poll() is None


def _launch_context(json_path: Path, root: Path, host: str, port: int) -> tuple:
    digest = hashlib.sha256(json_path.read_bytes())
    for path in (root / "shiny_context.json", root / "analysis_info.json", root / "metadata.tsv",
                 root / "Patterns_results" / "text_sizes.json"):
        if path.is_file():
            digest.update(path.read_bytes())
    context = _read_json(root / "shiny_context.json")
    configured_metadata = context.get("metadata_path")
    metadata_base = root
    if not configured_metadata:
        configured_metadata = _read_json(root / "analysis_info.json").get("config", {}).get("path_metadata")
        metadata_base = project_root()
    if configured_metadata and not (root / "metadata.tsv").is_file():
        metadata = Path(configured_metadata).expanduser()
        if not metadata.is_absolute():
            metadata = metadata_base / metadata
        if metadata.is_file():
            digest.update(metadata.read_bytes())
    for path in _existing_datasets(_read_json(json_path), root).values():
        digest.update(str(path).encode("utf-8"))
        with Path(path).open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    return (str(root), host, port, digest.hexdigest())


def launch_shiny_embedded(
    json_path: Path,
    host: str = "127.0.0.1",
    port: int = 3838,
    analysis_root: str | Path | None = None,
) -> subprocess.Popen:
    global _SHINY_PROCESS, _SHINY_CONTEXT
    json_path = Path(json_path).resolve()
    root = Path(analysis_root).resolve() if analysis_root else latest_analysis_root()
    if root is None:
        root = json_path.parent
    script = project_root() / "src" / "Shiny_CA.R"
    if not script.is_file() or not json_path.is_file():
        raise FileNotFoundError("Le script Shiny ou le fichier de résultats est introuvable.")
    context = _launch_context(json_path, root, host, port)
    if is_shiny_running() and context == _SHINY_CONTEXT:
        return _SHINY_PROCESS
    stop_shiny()
    if is_shiny_responding(host, port, timeout=0.3):
        raise RuntimeError(f"Le port {port} est déjà utilisé par un autre serveur.")
    log_path = root / "shiny.log"
    with log_path.open("a", encoding="utf-8") as log:
        _SHINY_PROCESS = subprocess.Popen(
            ["Rscript", str(script), str(json_path), host, str(port), str(root)],
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,
            cwd=project_root(),
        )
    _SHINY_CONTEXT = context
    return _SHINY_PROCESS


def stop_shiny(host: str = "127.0.0.1", port: int = 3838) -> None:
    """Arrête uniquement le processus Shiny lancé par cette application."""
    global _SHINY_PROCESS, _SHINY_CONTEXT
    if _SHINY_PROCESS is not None:
        if _SHINY_PROCESS.poll() is None:
            _SHINY_PROCESS.terminate()
            try:
                _SHINY_PROCESS.wait(timeout=3)
            except subprocess.TimeoutExpired:
                _SHINY_PROCESS.kill()
                _SHINY_PROCESS.wait(timeout=3)
        _SHINY_PROCESS = None
    _SHINY_CONTEXT = None


def wait_for_shiny(
    host: str = "127.0.0.1",
    port: int = 3838,
    timeout_s: float = 30.0,
    should_stop: Callable[[], bool] | None = None,
) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if should_stop is not None and should_stop():
            return False
        if not is_shiny_running():
            return False
        if is_shiny_responding(host, port, timeout=0.5):
            return True
        time.sleep(0.2)
    return False
