#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de concordancier basé sur CWB/CQP.
Recherche des termes dans le corpus avec contexte KWIC.
@jcharlesDS (2026)
"""

import subprocess
import re
import os


def _project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _local_env(registry_path):
    if not registry_path:
        raise ValueError("registry_path est requis pour interroger le corpus CWB.")
    env = os.environ.copy()
    bin_dir = os.path.join(_project_root(), "bin")
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env["CORPUS_REGISTRY_PATH"] = registry_path
    return env


def search_concordances(query, search_type="word", context_words=10, registry_path=None, corpus="MERGED"):
    """
    Recherche des concordances dans le corpus CWB.
    
    Args:
        query: Terme à rechercher
        search_type: Type de recherche ("word", "lemma", "pos")
        context_words: Nombre de mots de contexte à gauche et à droite
        registry_path: Chemin vers le registre CWB
        corpus: Nom du corpus (par défaut MERGED)
    
    Returns:
        Liste de tuples (contexte_gauche, terme, contexte_droit, source_id)
    """
    # Construire la requête CQP selon le type
    if search_type == "word":
        cqp_pattern = f'[word="{query}" %c]'  # %c = case-insensitive
    elif search_type == "lemma":
        cqp_pattern = f'[lemma="{query}" %c]'
    elif search_type == "pos":
        cqp_pattern = f'[pos="{query.upper()}"]'
    else:
        raise ValueError(f"Type de recherche invalide: {search_type}")

    return search_concordances_cqp_pattern(
        cqp_pattern=cqp_pattern,
        context_words=context_words,
        registry_path=registry_path,
        corpus=corpus,
    )


def search_concordances_cqp_pattern(cqp_pattern, context_words=10, registry_path=None, corpus="MERGED"):
    """
    Recherche des concordances dans le corpus CWB à partir d'une requête CQP déjà construite.
    """
    if not registry_path:
        raise ValueError("Aucun registry CWB n'a ete fourni pour la recherche de concordances.")

    project_root = _project_root()
    script_path = os.path.join(project_root, "src", "cqp_concordances.pl")
    local_cmd = ["perl", script_path, cqp_pattern, str(context_words)]
    
    try:
        result = subprocess.run(
            local_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root,
            env=_local_env(registry_path),
        )

        if result.returncode != 0:
            docker_cmd = [
                "docker", "run", "--rm",
                "-v", f"{project_root}:/workspace",
                "-w", "/workspace",
                "motifworkbench-cwb",
                "perl", "./src/cqp_concordances.pl",
                cqp_pattern,
                str(context_words)
            ]
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=project_root,
                env=_local_env(registry_path),
            )
        
        if result.returncode != 0:
            print(f"Erreur CQP: {result.stderr}")
            print(f"Stdout: {result.stdout}")
            return []
        
        # Parser la sortie
        concordances = []
        output_lines = result.stdout.splitlines()
        
        for line in output_lines:
            # Format attendu: position: <text_id ID>: contexte_gauche --> TERME <-- contexte_droit
            if "-->" in line and "<--" in line:
                # Extraire l'ID source (format: <text_id ID>)
                source_match = re.search(r'<text_id ([^>]+)>', line)
                source_id = source_match.group(1) if source_match else "?"
                
                # Retirer la partie avec position et text_id pour garder seulement le contexte
                # Format: "position: <text_id ID>: contexte..."
                line_clean = re.sub(r'^\s*\d+:\s*<text_id[^>]+>:\s*', '', line)
                
                # Extraire les parties
                parts = line_clean.split("-->")
                if len(parts) == 2:
                    left_context = parts[0].strip()
                    
                    middle_parts = parts[1].split("<--")
                    if len(middle_parts) == 2:
                        keyword = middle_parts[0].strip()
                        right_context = middle_parts[1].strip()
                        
                        concordances.append((left_context, keyword, right_context, source_id))
        
        return concordances
        
    except subprocess.TimeoutExpired:
        print("Timeout lors de la recherche CQP")
        return []
    except Exception as e:
        print(f"Erreur lors de la recherche: {e}")
        import traceback
        traceback.print_exc()
        return []


def format_concordances_for_display(concordances, max_context_chars=60):
    """
    Formate les concordances pour l'affichage dans un tableau.
    
    Args:
        concordances: Liste de tuples (left, keyword, right, source)
        max_context_chars: Longueur max des contextes
    
    Returns:
        Liste de tuples formatés pour QTableWidget
    """
    formatted = []
    
    for left, keyword, right, source in concordances:
        # Tronquer les contextes si trop longs
        if len(left) > max_context_chars:
            left = "... " + left[-max_context_chars:]
        
        if len(right) > max_context_chars:
            right = right[:max_context_chars] + " ..."
        
        formatted.append((left, keyword, right, source))
    
    return formatted
