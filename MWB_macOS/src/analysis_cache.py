"""Verified, per-analysis reuse of completed pipeline stages.

State files attest exact inputs and output bytes. Missing provenance is a miss.
The caller retains responsibility for parsing and validating scientific outputs
before recording a completed stage.
"""

from __future__ import annotations

from copy import deepcopy
from contextvars import ContextVar
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile


CACHE_VERSION = 1
_fingerprint_memo = ContextVar("analysis_fingerprint_memo", default=None)


def canonical_config(config: dict) -> str:
    """Compare explicit settings without inferring defaults for old records."""
    excluded = {"mode", "analysis_group_name", "actual_model_name"}
    return _json({key: value for key, value in config.items() if key not in excluded})


def _json(value) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False,
        separators=(",", ":"), default=_json_default,
    )


def _digest(value) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _json_default(value):
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Unsupported cache input: {type(value).__name__}")


def file_fingerprint(path) -> dict:
    """Hash file bytes, rejecting files changed while they are being read."""
    path = Path(path).absolute()
    current = path.stat()
    identity = (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns, current.st_ctime_ns)
    memo = _fingerprint_memo.get()
    key = (str(path), identity)
    if memo is not None and key in memo:
        return memo[key].copy()
    digest = hashlib.sha256()
    with path.open("rb") as source:
        before = os.fstat(source.fileno())
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
        after = os.fstat(source.fileno())
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    current = path.stat()
    for stat in (after, current):
        if identity != (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns):
            raise OSError(f"File changed while checking reuse: {path}")
    result = {"path": str(path), "size": before.st_size, "sha256": digest.hexdigest()}
    if memo is not None:
        memo[(str(path), identity)] = result.copy()
    return result


def paths_fingerprint(paths) -> dict:
    """Snapshot exact file and directory membership, including empty folders."""
    result = {}
    for path in sorted({Path(item).absolute() for item in paths}, key=str):
        if path.is_dir():
            members = {}
            for member in sorted(path.rglob("*")):
                name = member.relative_to(path).as_posix()
                if member.is_dir():
                    members[name] = {"directory": True}
                else:
                    members[name] = file_fingerprint(member)
            result[str(path)] = {"directory": True, "members": members}
        else:
            result[str(path)] = file_fingerprint(path)
    return result


def content_fingerprint(paths) -> dict:
    """Compare the same named artifacts across different analysis folders."""
    def portable(value):
        if isinstance(value, dict):
            return {key: portable(item) for key, item in value.items() if key != "path"}
        return value

    return {Path(path).name: portable(snapshot)
            for path, snapshot in paths_fingerprint(paths).items()}


def atomic_json(path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(_json(value))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def snapshot_file(source, destination) -> None:
    """Publish a verified byte-for-byte source snapshot inside the analysis."""
    source, destination = Path(source), Path(destination)
    expected = file_fingerprint(source)
    if source.resolve() == destination.resolve():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(descriptor)
    try:
        shutil.copyfile(source, temporary)
        actual = file_fingerprint(temporary)
        if actual["sha256"] != expected["sha256"] or file_fingerprint(source) != expected:
            raise RuntimeError("Le fichier source a changé pendant la création de l'instantané.")
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def recorded_stage_result(root, name):
    """Resolve already validated artifact locations for result viewers."""
    visited = set()
    root = Path(root).absolute()
    try:
        with (root / ".analysis_cache.json").open(encoding="utf-8") as stream:
            state = json.load(stream)
        record = state["stages"][name]
        if not record.get("success"):
            return None
        result = deepcopy(record.get("result"))
        while record.get("reference"):
            reference = record["reference"]
            identity = (reference["root"], reference["name"])
            if identity in visited:
                return None
            visited.add(identity)
            with (Path(reference["root"]) / ".analysis_cache.json").open(encoding="utf-8") as stream:
                state = json.load(stream)
            record = state["stages"][reference["name"]]
            if not record.get("success") or _digest(record) != reference["signature"]:
                return None
        return result if record.get("success") else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


class FileLock:
    """Nonblocking process lock, also released after process termination."""

    def __init__(self, path):
        self.path = Path(path)
        self.handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+")
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self.handle.close()
            self.handle = None
            raise RuntimeError("Une analyse utilise déjà ces fichiers. Attendez sa fin avant de relancer.") from error
        return self

    def __exit__(self, *exc):
        if self.handle is not None:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()
            self.handle = None


class AnalysisCache:
    """Small dependency-aware extension of the annotation cache-info pattern."""

    def __init__(self, root):
        self.root = Path(root).absolute()
        self.path = self.root / ".analysis_cache.json"
        self.lock = FileLock(self.root / ".analysis.lock")
        self.run_inputs = {}
        self.memo_token = None
        self.cacheable = True
        self.state = {"version": CACHE_VERSION, "stages": {}}

    def __enter__(self):
        self.lock.__enter__()
        if _fingerprint_memo.get() is None:
            self.memo_token = _fingerprint_memo.set({})
        try:
            with self.path.open(encoding="utf-8") as source:
                state = json.load(source)
            if (state.get("version") == CACHE_VERSION and isinstance(state.get("stages"), dict)
                    and all(isinstance(value, dict)
                            and isinstance(value.get("dependencies"), dict)
                            and isinstance(value.get("outputs"), dict)
                            and isinstance(value.get("inputs"), str)
                            for value in state["stages"].values())):
                self.state = state
        except (OSError, ValueError, AttributeError):
            pass
        return self

    def __exit__(self, *exc):
        self.lock.__exit__(*exc)
        if self.memo_token is not None:
            _fingerprint_memo.reset(self.memo_token)
            self.memo_token = None

    def _save(self):
        atomic_json(self.path, self.state)

    def invalidate(self, name):
        stages = self.state["stages"]
        invalid = {name}
        changed = True
        while changed:
            changed = False
            for key, stage in stages.items():
                if key not in invalid and invalid.intersection(stage.get("dependencies", {})):
                    invalid.add(key)
                    changed = True
        for key in invalid:
            stages.pop(key, None)
        self.state.pop("completed", None)
        self._save()

    def begin_stage(self, name):
        self.invalidate(name)

    def invalidate_all(self):
        self.state = {"version": CACHE_VERSION, "stages": {}}
        self._save()

    def _record_valid(self, name, visiting=None, validated=None, require_cacheable=False):
        validated = {} if validated is None else validated
        memo_key = (name, require_cacheable)
        if memo_key in validated:
            return validated[memo_key]
        stage = self.state["stages"].get(name)
        visiting = set() if visiting is None else visiting
        if not isinstance(stage, dict) or stage.get("success") is not True or name in visiting:
            return False
        if require_cacheable and stage.get("cacheable") is not True:
            return False
        visiting = visiting | {name}
        try:
            reference = stage.get("reference")
            if reference:
                source_root = Path(reference["root"])
                if source_root.resolve() == self.root.resolve():
                    return False
                with AnalysisCache(source_root) as source:
                    original = source.state["stages"].get(reference["name"])
                    if original is None or _digest(original) != reference["signature"]:
                        return False
                    if not source._record_valid(reference["name"], require_cacheable=True):
                        return False
            if stage["outputs"] != paths_fingerprint(stage["outputs"]):
                return False
            for dependency, signature in stage["dependencies"].items():
                if not self._record_valid(dependency, visiting, validated, require_cacheable):
                    return False
                if signature != _digest(self.state["stages"][dependency]):
                    return False
            validated[memo_key] = True
            return True
        except (OSError, ValueError, KeyError, TypeError, RuntimeError):
            return False

    def find_reusable_stage(self, name, inputs, dependencies=()):
        """Find a proven compatible stage in another configuration of this group."""
        if not self.cacheable:
            return None
        for root in sorted(self.root.parent.iterdir(), reverse=True):
            if not root.is_dir() or root.resolve() == self.root.resolve():
                continue
            if not (root / ".analysis_cache.json").is_file():
                continue
            try:
                with AnalysisCache(root) as source:
                    record = source.state["stages"].get(name)
                    if (record and record["inputs"] == _json(inputs)
                            and set(record["dependencies"]) == set(dependencies)
                            and source._record_valid(name, require_cacheable=True)):
                        return {"root": str(root), "name": name,
                                "signature": _digest(record), "record": deepcopy(record)}
            except (OSError, ValueError, KeyError, TypeError, RuntimeError):
                continue
        return None

    def adopt_stage(self, name, inputs, candidate, dependencies=()):
        """Reference verified immutable artifacts, keeping CWB registry paths intact."""
        with AnalysisCache(candidate["root"]) as source:
            original = source.state["stages"].get(candidate["name"])
            if (original is None or _digest(original) != candidate["signature"]
                    or original["inputs"] != _json(inputs)
                    or not source._record_valid(candidate["name"], require_cacheable=True)):
                raise RuntimeError("Les résultats à réutiliser ont changé. Relancez l'analyse.")
            original = deepcopy(original)
        self.complete_stage(name, inputs, original["outputs"], dependencies, original.get("result"))
        self.state["stages"][name]["reference"] = {
            "root": candidate["root"], "name": candidate["name"],
            "signature": candidate["signature"],
        }
        self._save()
        return deepcopy(original.get("result"))

    def restore_stage_files(self, name, inputs, candidate, outputs, dependencies=()):
        """Reuse small result files in their existing per-analysis locations."""
        with AnalysisCache(candidate["root"]) as source:
            original = source.state["stages"].get(candidate["name"])
            if (original is None or _digest(original) != candidate["signature"]
                    or original["inputs"] != _json(inputs)
                    or not source._record_valid(candidate["name"], require_cacheable=True)):
                raise RuntimeError("Les résultats à réutiliser ont changé. Relancez l'analyse.")
            sources = {Path(path).name: Path(path) for path in original["outputs"]}
            targets = {Path(path).name: Path(path) for path in outputs}
            if set(sources) != set(targets) or any(not path.is_file() for path in sources.values()):
                raise ValueError("Les fichiers de résultats ne correspondent pas à cette étape.")
            self.begin_stage(name)
            for filename, target in targets.items():
                snapshot_file(sources[filename], target)
                report = sources[filename].with_suffix(".txt")
                if target.suffix == ".pk" and report.name not in sources and report.is_file():
                    snapshot_file(report, target.with_suffix(".txt"))
            result = deepcopy(original.get("result"))
        self.complete_stage(name, inputs, outputs, dependencies, result)
        return result

    def stage_valid(self, name, inputs, outputs, dependencies=()):
        stage = self.state["stages"].get(name)
        valid = False
        try:
            valid = (self.cacheable and self._record_valid(name, require_cacheable=True)
                     and stage["inputs"] == _json(inputs)
                     and set(stage["outputs"]) == {str(Path(path).absolute()) for path in outputs}
                     and set(stage["dependencies"]) == set(dependencies))
        except (TypeError, KeyError, ValueError):
            pass
        if not valid:
            self.invalidate(name)
        return valid

    def complete_stage(self, name, inputs, outputs, dependencies=(), result=None):
        dependency_records = {}
        for dependency in dependencies:
            if not self._record_valid(dependency):
                raise RuntimeError(f"Incomplete dependency for {name}: {dependency}")
            dependency_records[dependency] = _digest(self.state["stages"][dependency])
        self.state["stages"][name] = {
            "success": True, "cacheable": self.cacheable, "inputs": _json(inputs),
            "outputs": paths_fingerprint(outputs), "dependencies": dependency_records,
            "result": deepcopy(result),
        }
        self.state.pop("completed", None)
        self._save()

    def get_stage_result(self, name):
        if not self._record_valid(name):
            return None
        return deepcopy(self.state["stages"][name].get("result"))

    def completed_results(self, run_inputs):
        completed = self.state.get("completed")
        try:
            if not self.cacheable or not completed or completed["inputs"] != _json(run_inputs):
                return None
            if completed["stages"] != {key: _digest(value) for key, value in self.state["stages"].items()}:
                return None
            validated = {}
            if not all(self._record_valid(name, validated=validated, require_cacheable=True)
                       for name in self.state["stages"]):
                return None
            if completed["outputs"] != paths_fingerprint(completed["outputs"]):
                return None
            return deepcopy(completed["results"])
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def complete_run(self, run_inputs, results):
        if not self.cacheable:
            return
        validated = {}
        if not self.state["stages"] or not all(
                self._record_valid(name, validated=validated, require_cacheable=True)
                for name in self.state["stages"]):
            raise RuntimeError("L'analyse comporte une étape incomplète et ne peut pas être réutilisée.")
        if not isinstance(results, dict) or not all(isinstance(value, str) for value in results.values()):
            raise ValueError("Invalid completed analysis results")
        self.state["completed"] = {
            "inputs": _json(run_inputs), "results": deepcopy(results),
            "outputs": paths_fingerprint(results.values()),
            "stages": {key: _digest(value) for key, value in self.state["stages"].items()},
        }
        self._save()


def _source_path(project_root, value, fallback):
    path = Path(value or fallback).expanduser()
    return path.absolute() if path.is_absolute() else (project_root / path).absolute()


def _distribution_fingerprint(name):
    distribution = importlib.metadata.distribution(name)
    files = distribution.files
    if not files:
        raise ValueError(f"No package file manifest: {name}")
    paths = [distribution.locate_file(item) for item in files
             if not str(item).endswith((".pyc", ".pyo")) and distribution.locate_file(item).is_file()]
    return {"version": distribution.version, "files": _fingerprint_summary(paths)}


def _fingerprint_summary(paths):
    snapshots = paths_fingerprint(paths)
    return {"entries": len(snapshots), "sha256": _digest(snapshots)}


def build_run_inputs(project_root, config):
    """Conservative whole-run provenance, with explicit cache eligibility."""
    project_root = Path(project_root).absolute()
    result = {"version": CACHE_VERSION, "configuration": canonical_config(config),
              "sources": {}, "code": {}, "runtime": {}, "cacheable": True}
    try:
        metadata = _source_path(project_root, config.get("path_metadata"), "Data/Corpus/metadata.tsv")
        result["sources"]["metadata"] = file_fingerprint(metadata)
        input_type = config.get("input_type", "raw_txt")
        if input_type == "raw_txt":
            corpus = _source_path(project_root, config.get("metadata_corpus_dir"), "Data/Corpus/Textes_raw")
            source_paths = sorted(corpus.glob("*.txt"))
        elif input_type == "annotated_conllu":
            corpus = _source_path(project_root, config.get("input_source_path"), "")
            source_paths = sorted(corpus.glob("*.conllu"))
        elif input_type == "prepared_zip":
            source_paths = [_source_path(project_root, config.get("input_source_path"), "")]
        else:
            raise ValueError(f"Unknown input type: {input_type}")
        if not source_paths:
            raise ValueError("No source files")
        result["sources"]["corpus"] = paths_fingerprint(source_paths)
        code = [path for folder in (project_root / "src", project_root / "gui/core", project_root / "gui/config")
                for path in folder.rglob("*") if path.is_file() and path.suffix in {".py", ".R", ".r", ".pl"}]
        result["code"] = paths_fingerprint(code)
        runtime = result["runtime"]
        runtime["python"] = {"version": sys.version, "executable": file_fingerprint(sys.executable),
                             "platform": platform.platform(), "machine": platform.machine()}
        runtime["installed_versions"] = dict(sorted(
            (distribution.metadata["Name"], distribution.version)
            for distribution in importlib.metadata.distributions()
            if distribution.metadata["Name"]
        ))
        runtime["environment"] = {name: os.environ.get(name) for name in (
            "PYTHONHASHSEED", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
            "CUDA_VISIBLE_DEVICES", "R_LIBS", "R_LIBS_USER", "R_ENVIRON", "R_PROFILE",
        )}
        runtime["packages"] = {name: _distribution_fingerprint(name) for name in ("pandas", "numpy", "scipy", "conllu")}
        runtime["tools"] = {}
        pipeline_path = str(project_root / "bin") + os.pathsep + os.environ.get("PATH", "")
        for name in ("Rscript", "perl", "cqp", "cwb-encode", "cwb-makeall"):
            executable = shutil.which(name, path=pipeline_path)
            if not executable:
                raise ValueError(f"Missing tool provenance: {name}")
            runtime["tools"][name] = file_fingerprint(executable)
        docker_images = set()
        for name in ("cqp", "cwb-encode", "cwb-makeall"):
            native = next((Path(prefix) / name for prefix in ("/opt/homebrew/bin", "/usr/local/bin")
                           if os.access(Path(prefix) / name, os.X_OK)), None)
            if native is None:
                docker_images.add("motifworkbench-cwb")
            else:
                runtime["tools"][f"native_{name}"] = file_fingerprint(native)
        binary = project_root / "BideSpanTree/bin/bidespantree"
        runtime["tools"]["bidespantree"] = file_fingerprint(binary)
        with binary.open("rb") as source:
            header = source.read(4)
        native_macho = header in (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xca\xfe\xba\xbe")
        if not os.access(binary, os.X_OK) or (sys.platform == "darwin" and not native_macho):
            docker_images.add("ubuntu:22.04")
        if docker_images:
            docker = shutil.which("docker")
            if not docker:
                raise ValueError("Missing Docker provenance")
            runtime["tools"]["docker"] = file_fingerprint(docker)
            runtime["docker_images"] = {}
            for image in sorted(docker_images):
                inspected = subprocess.run([docker, "image", "inspect", "--format", "{{.Id}}", image],
                                           check=True, capture_output=True, text=True, timeout=10)
                identity = inspected.stdout.strip()
                if not identity.startswith("sha256:"):
                    raise ValueError(f"Unknown Docker image identity: {image}")
                runtime["docker_images"][image] = identity
        runtime["wrappers"] = paths_fingerprint((project_root / "bin",))
        # Hash installed R package contents, including compiled numerical code.
        r_info = subprocess.run([shutil.which("Rscript"), "-e",
                                'needed <- c("dplyr","textometry","data.table","tidyr","tidyverse"); '
                                'cat(jsonlite::toJSON(list(libraries=.libPaths(),home=R.home(),'
                                'specifs_packages_available=all(needed %in% rownames(installed.packages()))), auto_unbox=TRUE))'],
                               check=True, capture_output=True, text=True, timeout=30)
        r_settings = json.loads(r_info.stdout)
        r_libraries = r_settings["libraries"]
        if isinstance(r_libraries, str):
            r_libraries = [r_libraries]
        r_home = Path(r_settings["home"])
        runtime["r_libraries"] = _fingerprint_summary([*r_libraries, r_home / "lib", r_home / "etc"])
        profiles = [path for path in (project_root / ".Rprofile", Path.home() / ".Rprofile",
                                     project_root / ".Renviron", Path.home() / ".Renviron") if path.exists()]
        runtime["r_profiles"] = _fingerprint_summary(profiles)
        if (config.get("specifs", False) or (config.get("earlySelection", False) and config.get("filter_specifs", False))):
            if not r_settings.get("specifs_packages_available", False):
                raise ValueError("R specificity packages are not installed yet")
        if input_type == "raw_txt":
            annotator_name = config.get("annotator", "stanza")
            from annotators import get_annotator
            annotator = get_annotator(annotator_name)
            model = annotator.resolve_model_name(config.get("language", "fr"), config.get("use_gpu", True))
            runtime["annotator"] = _distribution_fingerprint(annotator_name)
            runtime["model_name"] = model
            if annotator_name == "spacy":
                runtime["model"] = _distribution_fingerprint(model)
                runtime["formatter"] = _distribution_fingerprint("spacy-conll")
            elif annotator_name == "stanza":
                from stanza.resources.common import DEFAULT_MODEL_DIR
                runtime["model"] = _fingerprint_summary((Path(DEFAULT_MODEL_DIR) / model,
                                                         Path(DEFAULT_MODEL_DIR) / "resources.json"))
            else:
                raise ValueError(f"Unknown annotator: {annotator_name}")
    except (OSError, ValueError, TypeError, ImportError, subprocess.SubprocessError) as error:
        result["cacheable"] = False
        result["provenance_error"] = str(error)
    return result
