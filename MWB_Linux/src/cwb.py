# -*- coding: utf-8 -*-
"""
Created on Sat Apr 19 20:41:36 2025

@author: hugodumoulin
Modifié par @JcharlesDS
"""


import os
import shutil
import subprocess
from pathlib import Path

from cwb_backend import local_binary, local_cwb_available, local_cwb_env, prepare_registry_variant

CWB_BUILD_LOG_VERSION = "20260605-local-cwb-main-registry"


def _ensure_cwb_output_dirs(data_merged_dir: Path, registry_dir: Path) -> None:
    """Crée explicitement les dossiers attendus par CWB."""
    registry_dir.mkdir(parents=True, exist_ok=True)
    data_root = data_merged_dir.parent
    data_root.mkdir(parents=True, exist_ok=True)
    data_merged_dir.mkdir(parents=True, exist_ok=True)


def _reset_cwb_output_dirs(cwb_corpus_dir: Path) -> None:
    """Supprime les anciens fichiers CWB avant un réencodage."""
    for relative_path in (
        Path("data") / "merged",
        Path("registry"),
        Path("registry_local"),
        Path("registry_docker"),
    ):
        target = cwb_corpus_dir / relative_path
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


def _cleanup_registry_variants(cwb_corpus_dir: Path) -> None:
    """Supprime les variantes de registry non nécessaires après un run local."""
    for name in ("registry_local", "registry_docker"):
        target = cwb_corpus_dir / name
        if target.is_dir():
            shutil.rmtree(target)
            print(f"  -> Registry auxiliaire supprimé: {target}")
        elif target.exists():
            target.unlink()
            print(f"  -> Registry auxiliaire supprimé: {target}")


def _docker_user_args() -> list[str]:
    """Retourne les arguments Docker pour écrire avec l'utilisateur courant."""
    if hasattr(os, "getuid") and hasattr(os, "getgid"):
        return ["--user", f"{os.getuid()}:{os.getgid()}"]
    return []


def main(dir_textes_vrt="", dir_cwb_corpus=""):
    """
    Encode et indexe un corpus pour CWB.
    
    Args:
        dir_textes_vrt: Chemin du dossier contenant merged.vrt
        dir_cwb_corpus: Chemin du dossier pour le corpus CWB (data + registry)
    """
    if not dir_textes_vrt:
        raise ValueError("dir_textes_vrt est requis pour cwb.main().")
    if not dir_cwb_corpus:
        raise ValueError("dir_cwb_corpus est requis pour cwb.main().")

    # Chemins absolus pour la création
    vrt_file = f"{dir_textes_vrt}/merged.vrt"
    registry_dir = f"{dir_cwb_corpus}/registry"
    data_merged_dir = f"{dir_cwb_corpus}/data/merged"
    
    # Convertir en chemins absolus et créer les répertoires
    cwd = Path(os.getcwd()).resolve()
    abs_vrt = Path(vrt_file).resolve()
    abs_cwb_corpus = Path(dir_cwb_corpus).resolve()
    abs_registry = Path(registry_dir).resolve()
    abs_data_merged = Path(data_merged_dir).resolve()
    
    _reset_cwb_output_dirs(abs_cwb_corpus)
    _ensure_cwb_output_dirs(abs_data_merged, abs_registry)
    
    # Convertir en chemins relatifs au CWD pour Docker
    rel_vrt = abs_vrt.relative_to(cwd)
    rel_data_merged = abs_data_merged.relative_to(cwd)
    rel_registry = abs_registry.relative_to(cwd)
    
    print(f"CWB encoding of corpus from {abs_vrt}...")
    print(f"  -> CWB build log version: {CWB_BUILD_LOG_VERSION}")
    print(f"  -> Registry: {abs_registry}")
    print(f"  -> Data: {abs_data_merged}")
    
    common_encode_args = [
        "-c", "utf8",
        "-xsB",
        "-N", "id",
        "-P", "lemma", "-P", "pos", "-P", "xpos", "-P", "feats",
        "-P", "head", "-P", "dep", "-P", "deps", "-P", "misc",
        "-P", "Gender", "-P", "Tense", "-P", "Number", "-P", "Case",
        "-P", "ner", "-P", "Person", "-P", "PronType", "-P", "Reflex",
        "-P", "VerbForm", "-P", "Definite", "-P", "Polarity",
        "-S", "text:0+id", "-S", "s:0+id"
    ]
    registry_file = abs_registry / "merged"

    local_encode_error = None
    cwb_local_available = local_cwb_available()
    if cwb_local_available:
        try:
            local_encode_bin = local_binary("cwb-encode") or "cwb-encode"
            print("  -> Backend CWB local utilise pour l'encodage")
            print(f"  -> Binaire cwb-encode local: {local_encode_bin}")
            print(f"  -> Verification dossier data local: {abs_data_merged} (exists={abs_data_merged.exists()})")
            print(f"  -> Verification dossier registry local: {abs_registry} (exists={abs_registry.exists()})")
            local_cmd = [
                local_encode_bin,
                "-f", str(abs_vrt),
                "-d", f"{abs_data_merged}/",
                "-R", str(registry_file),
                *common_encode_args,
            ]
            try:
                subprocess.run(
                    local_cmd,
                    cwd=str(cwd),
                    env=local_cwb_env(),
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                stderr_text = exc.stderr or ""
                if (
                    "does not exist" in stderr_text
                    and ("data directory" in stderr_text or "registry directory" in stderr_text)
                ):
                    print("  -> Recréation des dossiers CWB puis nouvelle tentative locale...")
                    _ensure_cwb_output_dirs(abs_data_merged, abs_registry)
                    subprocess.run(
                        local_cmd,
                        cwd=str(cwd),
                        env=local_cwb_env(),
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                else:
                    raise
            print("  -> Encodage CWB local reussi")
        except subprocess.CalledProcessError as exc:
            local_encode_error = exc
            print(f"  -> CWD local: {cwd}")
            print(f"  -> Data local is_dir: {abs_data_merged.is_dir()}")
            print(f"  -> Registry local is_dir: {abs_registry.is_dir()}")
            print(f"  -> Echec CWB local, bascule sur Docker: {exc.stderr or exc}")
    else:
        print("  -> CWB local indisponible, backend Docker utilise pour l'encodage")

    if not cwb_local_available or local_encode_error is not None:
        print("  -> Backend Docker utilise pour l'encodage")
        cmd_encode = [
            "docker", "run", "--rm",
            *_docker_user_args(),
            "-v", f"{cwd}:/workspace",
            "-w", "/workspace",
            "motifworkbench-cwb",
            "cwb-encode",
            "-f", str(rel_vrt),
            "-d", f"{rel_data_merged}/",
            "-R", str(rel_registry / "merged"),
            *common_encode_args,
        ]
        result_encode = os.system(" ".join(cmd_encode))
        if result_encode != 0:
            print(f"Erreur lors de l'encodage CWB (code: {result_encode})")
            return
        print("  -> Encodage CWB via Docker reussi")

    print(f"CWB indexing of corpus in {abs_registry}...")
    local_makeall_error = None
    local_makeall_success = False
    if cwb_local_available:
        try:
            local_makeall_bin = local_binary("cwb-makeall") or "cwb-makeall"
            print("  -> Backend CWB local utilise pour l'indexation")
            print(f"  -> Binaire cwb-makeall local: {local_makeall_bin}")
            subprocess.run(
                [local_makeall_bin, "-r", str(abs_registry), "-V", "merged"],
                cwd=str(cwd),
                env=local_cwb_env(),
                check=True,
                capture_output=True,
                text=True,
            )
            print("  -> Indexation CWB locale reussie")
            local_makeall_success = True
        except subprocess.CalledProcessError as exc:
            local_makeall_error = exc
            print(f"  -> Echec cwb-makeall local, bascule sur Docker: {exc.stderr or exc}")
    else:
        print("  -> CWB local indisponible, backend Docker utilise pour l'indexation")

    if not cwb_local_available or local_makeall_error is not None:
        print("  -> Backend Docker utilise pour l'indexation")
        docker_registry_dir = Path(prepare_registry_variant(str(abs_registry), "docker"))
        rel_registry_for_docker = docker_registry_dir.relative_to(cwd)
        cmd_makeall = [
            "docker", "run", "--rm",
            *_docker_user_args(),
            "-v", f"{cwd}:/workspace",
            "-w", "/workspace",
            "motifworkbench-cwb",
            "cwb-makeall",
            "-r", str(rel_registry_for_docker),
            "-V", "merged"
        ]
        result_makeall = os.system(" ".join(cmd_makeall))
        if result_makeall != 0:
            print(f"Erreur lors de l'indexation CWB (code: {result_makeall})")
        else:
            print("  -> Indexation CWB via Docker reussie")
    elif local_encode_error is None and local_makeall_success:
        _cleanup_registry_variants(abs_cwb_corpus)

#attention ! dans le registre, les chemins vers les fichiers de donnees
#sont resolus par rapport au dossier d'analyse courant.
#Les appels CQP doivent donc utiliser le registry de l'analyse concernee.

##requirements:
#brew install cwb
#et SURTOUT
#cpan
#install CWB::CQP
 
