#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pont entre Python et les scripts Perl/CQP utilises par MotifWorkBench.
Essaie d'abord le CWB local, puis Docker en fallback.
"""

from __future__ import annotations

from cwb_backend import run_perl_cqp_script


def _run_script(script_rel: str, args: list[str], registry_path: str, timeout: int = 60):
    return run_perl_cqp_script(script_rel, args, registry_path=registry_path, timeout=timeout)


def cqp_freq_textes(pattern, registry_path=""):
    """
    Interroge CQP pour obtenir les fréquences d'un motif par texte.
    """
    ligne_de_table = {}
    query = f"pattern = {pattern}"

    result = _run_script("src/cqp_freq_textes.pl", [query], registry_path, timeout=60)
    output = result.stdout

    if result.returncode != 0:
        print(f"[CQP] Erreur d'exécution du script Perl (code {result.returncode})")
        if result.stderr:
            print(f"    stderr: {result.stderr[:200]}")
        return ligne_de_table

    if not output or len(output.strip()) == 0:
        return ligne_de_table

    output_lines = output.splitlines()
    if len(output_lines) < 8:
        if any("error" in line.lower() or "no corpus" in line.lower() for line in output_lines):
            print("[CQP] Erreur dans la sortie:")
            for line in output_lines[:5]:
                print(f"    {line}")
        return ligne_de_table

    for line in output_lines[5:(len(output_lines) - 3)]:
        if not line.startswith("#"):
            part = line.split("\t")
            if len(part) >= 2:
                texte = part[0][30:].strip()
                try:
                    freq = int(part[1].strip())
                    ligne_de_table[texte] = freq
                except ValueError:
                    pass
    return ligne_de_table


def cqp_general(registry_path=""):
    """
    Obtient les statistiques générales du corpus via CQP.
    """
    result = _run_script("src/cqp_general.pl", [], registry_path, timeout=60)
    output_lines = result.stdout.splitlines()
    T = output_lines[4].strip()
    dictionnaire_t = {}
    for line in output_lines[8:(len(output_lines) - 3)]:
        part = line.split("\t")
        texte = part[0][30:].strip()
        t = int(part[1].strip())
        dictionnaire_t[texte] = t
    return T, dictionnaire_t


def cqp_index_property(property, registry_path=""):
    """
    Indexe une propriété spécifique du corpus.
    """
    script = f"src/cqp_index_{property}.pl"
    result = _run_script(script, [], registry_path, timeout=60)
    output_lines = result.stdout.splitlines()
    liste_property = []
    for line in output_lines[4:(len(output_lines) - 3)]:
        part = line.split("\t")
        res = part[1].strip()
        res = res.split("  ")[0]
        liste_property.append(res)
    return liste_property


def cqp_index_lemma(pos, registry_path=""):
    """
    Indexe les lemmes filtrés par POS.
    """
    query = f'A = [lemma=".*" & pos="{pos}"]'
    result = _run_script("src/cqp_index_lemma.pl", [query], registry_path, timeout=60)
    output_lines = result.stdout.splitlines()
    liste_lemma = []
    for line in output_lines[4:(len(output_lines) - 3)]:
        part = line.split("\t")
        lemma = part[1].strip()
        lemma = lemma.split("  ")[0]
        liste_lemma.append(lemma)
    return liste_lemma


def cqp_index_pos(registry_path=""):
    """
    Indexe toutes les catégories POS du corpus.
    """
    result = _run_script("src/cqp_index_pos.pl", [], registry_path, timeout=60)
    output_lines = result.stdout.splitlines()
    liste_pos = []
    for line in output_lines[4:(len(output_lines) - 3)]:
        part = line.split("\t")
        pos = part[1].strip()
        pos = pos.split("  ")[0]
        liste_pos.append(pos)
    return liste_pos
