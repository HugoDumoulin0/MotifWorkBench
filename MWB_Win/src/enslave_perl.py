#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pont entre Python et les scripts Perl/CQP utilises par MotifWorkBench.
Essaie d'abord le CWB local, puis Docker en fallback.
"""

from __future__ import annotations

import re

from cwb_backend import run_perl_cqp_script


def _run_script(script_rel: str, args: list[str], registry_path: str, timeout: int = 60):
    return run_perl_cqp_script(script_rel, args, registry_path=registry_path, timeout=timeout)


def _extract_count_from_line(line: str) -> tuple[str, int] | None:
    """Extrait une paire (clé, fréquence) d'une ligne CQP group/group-by."""
    stripped = line.rstrip()
    if not stripped or stripped.startswith("#") or stripped.startswith("["):
        return None

    match = re.match(r"^\s*(.*?)\s+(-?\d+)\s*$", stripped)
    if not match:
        return None

    label = match.group(1).strip()
    if label.lower().startswith("(all)"):
        label = label[5:].strip()
    count = int(match.group(2))
    return label, count


def _extract_total_value(output_lines: list[str]) -> str:
    """Récupère la première ligne composée uniquement d'un entier."""
    for line in output_lines:
        stripped = line.strip()
        if re.fullmatch(r"-?\d+", stripped):
            return stripped
    return "0"




def _extract_count_item_line(line: str) -> str | None:
    """Extrait l'item d'une sortie CQP `count A by ...`."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or stripped.startswith("["):
        return None

    match = re.match(r"^\s*\d+\s+(.*?)\s+\[#\d+-#\d+\]\s*$", stripped)
    if not match:
        return None

    item = match.group(1).strip()
    if item.lower().startswith("(all)"):
        item = item[5:].strip()
    return item or None

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

    for line in output_lines:
        parsed = _extract_count_from_line(line)
        if not parsed:
            continue
        texte, freq = parsed
        if texte.lower() == "(all)":
            continue
        ligne_de_table[texte] = freq
    return ligne_de_table


def cqp_general(registry_path=""):
    """
    Obtient les statistiques générales du corpus via CQP.
    """
    result = _run_script("src/cqp_general.pl", [], registry_path, timeout=60)
    output_lines = result.stdout.splitlines()
    T = _extract_total_value(output_lines)
    dictionnaire_t = {}
    for line in output_lines:
        parsed = _extract_count_from_line(line)
        if not parsed:
            continue
        texte, t = parsed
        if texte.lower() == "(all)":
            continue
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
    for line in output_lines:
        parsed = _extract_count_from_line(line)
        if parsed:
            liste_property.append(parsed[0])
    return liste_property


def cqp_index_lemma(pos, registry_path=""):
    """
    Indexe les lemmes filtrés par POS.
    """
    query = f'A = [lemma=".*" & pos="{pos}"]'
    result = _run_script("src/cqp_index_lemma.pl", [query], registry_path, timeout=60)
    output_lines = result.stdout.splitlines()
    liste_lemma = []
    for line in output_lines:
        item = _extract_count_item_line(line)
        if item:
            liste_lemma.append(item)
    return liste_lemma


def cqp_index_pos(registry_path=""):
    """
    Indexe toutes les catégories POS du corpus.
    """
    result = _run_script("src/cqp_index_pos.pl", [], registry_path, timeout=60)
    output_lines = result.stdout.splitlines()
    liste_pos = []
    for line in output_lines:
        parsed = _extract_count_from_line(line)
        if parsed:
            liste_pos.append(parsed[0])
    return liste_pos
