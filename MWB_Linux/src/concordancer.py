#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de concordancier basé sur CWB/CQP.
Recherche des termes dans le corpus avec contexte KWIC.
@jcharlesDS (2026)
"""

import json
import os
import re
import subprocess

import pandas as pd
from pathlib import Path

from cwb_backend import run_perl_cqp_script

def search_concordances(query, search_type="word", context_words=10, registry_path="", corpus="MERGED"):
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
    elif search_type == "cqp":
        cqp_pattern = query
    else:
        raise ValueError(f"Type de recherche invalide: {search_type}")
    
    try:
        if not registry_path:
            print("[Concordancier] Aucun registry CWB fourni.")
            return []

        registry_path = str(Path(registry_path).resolve())
        if not Path(registry_path).exists():
            print(f"[Concordancier] Registry introuvable : {registry_path}")
            return []

        result = run_perl_cqp_script(
            "src/cqp_concordances.pl",
            [cqp_pattern, str(context_words)],
            registry_path=registry_path,
            timeout=30,
        )
        
        if result.returncode != 0:
            print(f"Erreur CQP: {result.stderr}")
            print(f"Stdout: {result.stdout}")
            return []

        if "CQP Error" in (result.stdout or "") or "CQP Error" in (result.stderr or ""):
            print(f"[Concordancier] Erreur CQP détectée pour le registry {registry_path}")
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
        
        print(f"[Concordancier] {len(concordances)} concordance(s) trouvée(s) dans {registry_path}")
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

def enrich_concordances_with_metadata(concordances, metadata_path=None):
    """
    Enrichit les concordances avec les métadonnées

    Args:
        concordances: Listes de tuples (left, keyword, right, source_id)
        metadata_path: Chemin vers metadata.tsv (None = auto-détection)
    
    Returns:
        Liste de dicts avec colonnes enrichies
    """
    
    # Auto-détection du fichier
    if metadata_path is None:
        project_root = Path(__file__).resolve().parents[1]
        
        # Essayer depuis last_analysis.json
        last_analysis_path = project_root / "logs" / "last_analysis.json"
        if last_analysis_path.exists():
            try:
                with open(last_analysis_path) as f:
                    config = json.load(f)
                    metadata_path = config.get("path_metadata")
                    
                    # Fallback 1 : reconstruire depuis path_corpus si disponible
                    if not metadata_path and "path_corpus" in config:
                        path_corpus = config["path_corpus"]
                        if path_corpus:
                            candidate = Path(path_corpus) / "metadata.tsv"
                            if candidate.exists():
                                metadata_path = str(candidate)
                                print(f"[Fallback] Métadonnées reconstruites depuis path_corpus : {metadata_path}")
                    
                    # Fallback 2 : chercher via analysis_group_name / corpus_name legacy
                    analysis_group_name = config.get("analysis_group_name") or config.get("corpus_name")
                    if not metadata_path and analysis_group_name:
                        corpus_dir = project_root / "Data" / "Corpus"
                        
                        if corpus_dir.exists():
                            # Stratégie 1: reconstruire le nom du corpus depuis le groupe d'analyses
                            corpus_slug = analysis_group_name.replace("analyse_", "").replace("corpus_", "").replace("_", " ").strip()
                            
                            for folder in corpus_dir.iterdir():
                                if folder.is_dir():
                                    folder_slug = folder.name.replace("_", " ").lower()
                                    corpus_slug_lower = corpus_slug.lower()
                                    
                                    # Correspondance si les slugs se ressemblent
                                    if corpus_slug_lower in folder_slug or folder_slug in corpus_slug_lower:
                                        candidate = folder / "metadata.tsv"
                                        if candidate.exists():
                                            metadata_path = str(candidate)
                                            print(f"[Fallback] Métadonnées du corpus '{analysis_group_name}' trouvées : {metadata_path}")
                                            break
                            
                            # Si pas trouvé, avertir mais ne pas prendre le premier venu
                            if not metadata_path:
                                print(f"⚠ Aucun metadata.tsv trouvé pour le corpus '{analysis_group_name}'")
                                print(f"  Dossiers disponibles : {[f.name for f in corpus_dir.iterdir() if f.is_dir()]}")

            except Exception as e:
                print(f"⚠ Erreur lecture last_analysis.json : {e}")
        
        # Pas de fallback hardcodé : si aucune analyse n'a été lancée, retourner données sans enrichissement
        if not metadata_path:
            print("[Concordancier] ⚠ Aucune métadonnée détectée - lancez une analyse d'abord pour activer les filtres")
            return [{"left_context": c[0], "keyword": c[1], "right_context": c[2], "source_id": c[3]} for c in concordances]

    # Charger le fichier
    try:
        df_metadata = pd.read_csv(metadata_path, sep="\t", index_col=0)
        metadata_columns = df_metadata.columns.tolist()
        print(f"✓ Métadonnées chargées depuis {metadata_path}")
        print(f"  Colonnes détectées : {metadata_columns}")
        print(f"  Nombre de textes : {len(df_metadata)}")
    except FileNotFoundError:
        print(f"⚠ Metadata non trouvé : {metadata_path}")
        # Retourner la forme basique
        return [
            {
                'left_context': left,
                'keyword': keyword,
                'right_context': right,
                'source_id': source_id
            }
            for left, keyword, right, source_id in concordances
        ]
    except Exception as e:
        print(f"⚠ Erreur de lecture metadata : {e}")
        import traceback
        traceback.print_exc()
        return [
            {
                'left_context': left,
                'keyword': keyword,
                'right_context': right,
                'source_id': source_id
            }
            for left, keyword, right, source_id in concordances
        ]
    
    
    # Enrichir les concordances
    enriched = []
    matches_found = 0
    for left, keyword, right, source_id in concordances:
        # Récupérer les métadonnées du texte source:
        if source_id in df_metadata.index:
            metadata_row = df_metadata.loc[source_id].to_dict()
            matches_found += 1
        else:
            metadata_row = {col: "" for col in metadata_columns}
        
        enriched.append({
            'left_context': left,
            'keyword': keyword,
            'right_context': right,
            'source_id': source_id, 
            **metadata_row # Ajouter les colonnes de metadata
            })
    
    print(f"✓ Enrichissement terminé : {matches_found}/{len(concordances)} concordances avec métadonnées")
    return enriched

def get_metadata_columns(metadata_path=None):
    """
    Récupère la liste des colonnes disponibles dans le fichier metadata.tsv

    Args:
        metadata_path: Chemin vers metadata.tsv (None = auto-détection)
    
    Returns:
        Liste des nom de colonnes (ex: ["genre", "période", "auteur"])
    """
    
    # Auto-détection du metadata.tsv
    if metadata_path is None:
        project_root = Path(__file__).resolve().parents[1]
        
        # Essayer depuis last_analysis.json
        last_analysis_path = project_root / "logs" / "last_analysis.json"
        if last_analysis_path.exists():
            try:
                with open(last_analysis_path) as f:
                    config = json.load(f)
                    metadata_path = config.get("path_metadata")
            except:
                pass
        
        # Pas de fallback : si aucune analyse, retourner liste vide
        if not metadata_path:
            return []
    
    # Charger metadata.tsv
    try:
        df_metadata = pd.read_csv(metadata_path, sep="\t", index_col=0)
        return df_metadata.columns.tolist()
    except:
        return []  # Aucune colonne trouvée
