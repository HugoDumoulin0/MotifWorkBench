# -*- coding: utf-8 -*-
"""
Created on Sat Apr 19 20:41:36 2025

@author: hugodumoulin
Modifié par @JcharlesDS
"""


import os
import subprocess


def _prepend_local_bin_to_path():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_bin = os.path.join(project_root, "bin")
    os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH', '')}"


def _run_command(command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def main(dir_cwb_corpus, dir_textes_vrt):
    """
    Encodage et indexation CWB du corpus.
    
    Args:
        dir_cwb_corpus: Chemin vers le dossier cwb-corpus (contient registry/ et data/)
        dir_textes_vrt: Chemin vers le dossier contenant merged.vrt
    """
    _prepend_local_bin_to_path()

    registry_dir = os.path.join(dir_cwb_corpus, "registry")
    data_dir = os.path.join(dir_cwb_corpus, "data")
    data_merged_dir = os.path.join(data_dir, "merged")
    merged_vrt = os.path.join(dir_textes_vrt, "merged.vrt")
    
    if not os.path.exists(registry_dir):
        os.makedirs(registry_dir, exist_ok=True)
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    if not os.path.exists(data_merged_dir):
        os.makedirs(data_merged_dir, exist_ok=True)
    
    print("CWB encoding of corpus...")
    cmd_encode = [
        "cwb-encode",
        "-f", merged_vrt,
        "-d", data_merged_dir + "/",
        "-R", os.path.join(registry_dir, "merged"),
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
    try:
        result_encode = _run_command(cmd_encode)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        error_output = getattr(exc, "stderr", "") or str(exc)
        print(f"Erreur lors de l'encodage CWB: {error_output}")
        return
    if result_encode.stdout:
        print(result_encode.stdout, end="")
    
    print("CWB indexing of corpus...")
    cmd_makeall = [
        "cwb-makeall",
        "-r", registry_dir,
        "-V", "MERGED"
    ]
    try:
        result_makeall = _run_command(cmd_makeall)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        error_output = getattr(exc, "stderr", "") or str(exc)
        print(f"Erreur lors de l'indexation CWB: {error_output}")
        return
    if result_makeall.stdout:
        print(result_makeall.stdout, end="")

# Attention : le registre contient des chemins relatifs vers les donnees
# de l'analyse courante. Les appels CQP doivent donc toujours recevoir
# explicitement le registry genere pour cette analyse.

##requirements:
#brew install cwb
#et SURTOUT
#cpan
#install CWB::CQP
 
