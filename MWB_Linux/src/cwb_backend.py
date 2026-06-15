#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend CWB/CQP avec priorite au local puis fallback Docker.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

_logged_local_failures: set[tuple[str, tuple[str, ...]]] = set()


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def docker_user_args() -> list[str]:
    """Retourne les arguments Docker pour écrire avec l'utilisateur courant."""
    if hasattr(os, "getuid") and hasattr(os, "getgid"):
        return ["--user", f"{os.getuid()}:{os.getgid()}"]
    return []


def _is_project_docker_wrapper(path: Path) -> bool:
    """Repère les wrappers Docker du projet qui ne sont pas un vrai CWB local."""
    try:
        if not path.is_file():
            return False
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return "docker run" in content and "motifworkbench-cwb" in content


def local_binary(name: str) -> str | None:
    """Retourne un vrai binaire local, en ignorant les wrappers Docker du projet."""
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory:
            continue
        candidate = Path(directory) / name
        if candidate.exists() and os.access(candidate, os.X_OK):
            if _is_project_docker_wrapper(candidate):
                continue
            return str(candidate)
    return None


def local_cwb_env() -> dict[str, str]:
    """Environnement PATH filtré pour éviter les wrappers Docker en mode local."""
    env = os.environ.copy()
    safe_dirs: list[str] = []
    for directory in env.get("PATH", "").split(os.pathsep):
        if not directory:
            continue
        dir_path = Path(directory)
        if any(_is_project_docker_wrapper(dir_path / name) for name in ("cwb-encode", "cwb-makeall", "cqp")):
            continue
        safe_dirs.append(directory)
    env["PATH"] = os.pathsep.join(safe_dirs)
    return env


def local_cqp_available() -> bool:
    return local_binary("cqp") is not None and shutil.which("perl") is not None


def local_cwb_available() -> bool:
    return (
        local_binary("cwb-encode") is not None
        and local_binary("cwb-makeall") is not None
        and local_cqp_available()
    )


def force_docker_cwb() -> bool:
    """Indique si le run courant doit forcer Docker pour CWB/CQP."""
    return os.environ.get("MWB_FORCE_DOCKER_CWB", "").strip() == "1"


def prepare_registry_variant(
    registry_path: str,
    mode: str,
    corpus_id: str = "merged",
) -> str:
    """
    Prépare une variante de registry adaptée au backend cible.

    - `local`: HOME/INFO absolus sur l'hôte
    - `docker`: HOME/INFO relatifs à la racine du projet montée dans /workspace
    """
    if mode not in {"local", "docker"}:
        return str(Path(registry_path).resolve())

    registry_dir = Path(registry_path).resolve()
    registry_file = registry_dir / corpus_id
    if not registry_file.exists():
        return str(registry_dir)

    variant_dir = registry_dir.parent / f"{registry_dir.name}_{mode}"
    variant_file = variant_dir / corpus_id
    try:
        lines = registry_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return str(registry_dir)

    root = project_root().resolve()
    updated_lines: list[str] = []

    for line in lines:
        if line.startswith("HOME ") or line.startswith("INFO "):
            key, value = line.split(None, 1)
            clean_value = value.strip().strip('"').strip("'")
            path_value = Path(clean_value)
            absolute_value = path_value if path_value.is_absolute() else (root / path_value).resolve()
            if mode == "local":
                updated_lines.append(f"{key} {absolute_value}")
            else:
                try:
                    docker_value = absolute_value.relative_to(root)
                except ValueError:
                    docker_value = path_value
                updated_lines.append(f"{key} {docker_value}")
            continue
        updated_lines.append(line)

    if updated_lines == lines:
        stale_variant_dir = registry_dir.parent / f"{registry_dir.name}_{mode}"
        if stale_variant_dir.exists():
            shutil.rmtree(stale_variant_dir)
            print(f"[CWB] Registry {mode} inutile, suppression de {stale_variant_dir}")
        return str(registry_dir)

    variant_dir = registry_dir.parent / f"{registry_dir.name}_{mode}"
    variant_file = variant_dir / corpus_id
    try:
        variant_dir.mkdir(parents=True, exist_ok=True)
        tmp_registry = variant_file.with_name(f"{variant_file.name}.tmp")
        tmp_registry.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
        tmp_registry.replace(variant_file)
        print(f"[CWB] Registry {mode} prepare pour {variant_file}")
    except OSError as exc:
        print(f"[CWB] Impossible de preparer le registry {mode} {variant_file}: {exc}")
        return str(registry_dir)

    return str(variant_dir)


def _has_cqp_runtime_error(result: subprocess.CompletedProcess) -> bool:
    """
    Détecte les erreurs CQP "silencieuses" :
    certains appels retournent code 0 tout en écrivant "CQP Error" en sortie.
    """
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    error_markers = (
        "CQP Error",
        "Couldn't open directory",
        "No corpus activated",
        "is undefined",
    )
    combined = f"{stdout}\n{stderr}"
    return any(marker in combined for marker in error_markers)


def _log_local_failure_details(
    script_rel: str,
    script_args: list[str],
    result: subprocess.CompletedProcess,
) -> None:
    """
    Logue une fois les détails utiles du premier échec local
    pour faciliter le diagnostic des différences CQP local/Docker.
    """
    key = (script_rel, tuple(script_args))
    if key in _logged_local_failures:
        return
    _logged_local_failures.add(key)

    print(f"[CWB] Diagnostic échec local pour {script_rel}")
    if script_args:
        print(f"[CWB] Arguments: {script_args}")

    stderr = (result.stderr or "").strip()
    stdout = (result.stdout or "").strip()
    if stderr:
        print(f"[CWB] stderr local: {stderr[:1200]}")
    if stdout:
        print(f"[CWB] stdout local: {stdout[:1200]}")


def _should_retry_local_registry(result: subprocess.CompletedProcess) -> bool:
    """Détecte les erreurs locales qui méritent une régénération du registry local."""
    combined = f"{result.stdout or ''}\n{result.stderr or ''}"
    retry_markers = (
        "Couldn't open directory",
        "Corpus ``MERGED'' is undefined",
        "No corpus activated",
    )
    return any(marker in combined for marker in retry_markers)


def _docker_script_command(script_rel: str, registry_path: str, script_args: list[str]) -> list[str]:
    root = project_root()
    abs_registry = Path(prepare_registry_variant(registry_path, "docker")).resolve()
    abs_root = root.resolve()

    try:
        rel_registry = abs_registry.relative_to(abs_root)
        registry_arg = str(rel_registry)
    except ValueError:
        registry_arg = registry_path

    return [
        "docker", "run", "--rm",
        *docker_user_args(),
        "-e", f"CORPUS_REGISTRY_PATH={registry_arg}",
        "-v", f"{root}:/workspace",
        "-w", "/workspace",
        "motifworkbench-cwb",
        "perl", script_rel,
        *script_args,
    ]


def run_perl_cqp_script(
    script_rel: str,
    script_args: list[str],
    registry_path: str,
    timeout: int = 60,
) -> subprocess.CompletedProcess:
    """
    Lance un script Perl qui interroge CQP.
    Essaie d'abord le local, puis Docker en fallback.
    """
    root = project_root()
    script_path = root / script_rel
    env = local_cwb_env()
    resolved_registry = str(Path(registry_path).resolve())
    local_registry = prepare_registry_variant(resolved_registry, "local")
    env["CORPUS_REGISTRY_PATH"] = local_registry

    local_error: subprocess.CompletedProcess | None = None
    if force_docker_cwb():
        print(f"[CWB] Docker forcé pour ce run, backend Docker utilise pour {script_rel}")
    elif local_cqp_available():
        print(f"[CWB] Backend local utilise pour {script_rel}")
        print(f"[CWB] Registry local: {local_registry}")
        local_cmd = ["perl", str(script_path), *script_args]
        local_result = subprocess.run(
            local_cmd,
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if local_result.returncode != 0 or _has_cqp_runtime_error(local_result):
            if _should_retry_local_registry(local_result):
                print(f"[CWB] Regeneration du registry local puis nouvelle tentative pour {script_rel}...")
                local_registry = prepare_registry_variant(resolved_registry, "local")
                env["CORPUS_REGISTRY_PATH"] = local_registry
                print(f"[CWB] Registry local regenere: {local_registry}")
                local_result = subprocess.run(
                    local_cmd,
                    cwd=str(root),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
        if local_result.returncode == 0 and not _has_cqp_runtime_error(local_result):
            print(f"[CWB] Execution locale reussie pour {script_rel}")
            return local_result
        local_error = local_result
        _log_local_failure_details(script_rel, script_args, local_result)
        print(f"[CWB] Echec local pour {script_rel}, bascule sur Docker...")
    else:
        print(f"[CWB] CQP local indisponible, Docker utilise pour {script_rel}")

    print(f"[CWB] Backend Docker utilise pour {script_rel}")
    docker_cmd = _docker_script_command(script_rel, registry_path, script_args)
    docker_result = subprocess.run(
        docker_cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if docker_result.returncode == 0 and not _has_cqp_runtime_error(docker_result):
        print(f"[CWB] Execution Docker reussie pour {script_rel}")
        return docker_result

    if local_error is not None:
        print(f"[CWB] Echec Docker apres fallback pour {script_rel}")
        return local_error
    print(f"[CWB] Echec Docker pour {script_rel}")
    return docker_result
