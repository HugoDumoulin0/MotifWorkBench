#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 24 17:57:05 2025

@author: hugodumoulin
"""



import pandas as pd
import enslave_perl
import subprocess
import os
import datetime
from pathlib import Path
import compute_CQP
import tools

def compute_early_df_lemmes(seuil, early_pos4lemma, registry_path):
    """
    Calcule le dataframe des lemmes pour early selection.
    
    Args:
        seuil: Nombre de lemmes à considérer
        early_pos4lemma: Pattern POS pour filtrer les lemmes
        registry_path: Chemin vers le registry CWB
    """
    T, dictionnaire_t = enslave_perl.cqp_general()
    lignes_table = []
    print("indexing lemma")
    liste_lemma = enslave_perl.cqp_index_lemma(early_pos4lemma)
    print("index done")
    nombre = len(liste_lemma[:seuil])
    print(f"Computing {nombre} lemma freq X texte...")
    print("index done")
    indice=0
    for lemma in liste_lemma[:seuil]:
        req = f'[lemma="{lemma}"]'
        indice+=1
        print(f"{indice} {lemma}")
        ligne_de_table = enslave_perl.cqp_freq_textes(req)
        lignes_table.append(ligne_de_table)
    df_lemma = pd.DataFrame(lignes_table, index=liste_lemma[:seuil])
    df_lemma = df_lemma.fillna(0)
    df_lemma = df_lemma.apply(pd.to_numeric)
    return df_lemma, T, dictionnaire_t

def dictionnaire_t_target(dictionnaire_t, df_target,partition_cible):
    """Agrège les tailles de textes par colonne de métadonnées."""
    df_target["taille"]=df_target.index.map(dictionnaire_t)
    dictionnaire_t_result = df_target.groupby(partition_cible)["taille"].sum().to_dict()
    return dictionnaire_t_result


def _load_specif_rows(specif_output_path, seuil_banalité):
    df_specif = pd.read_csv(specif_output_path, sep="\t", index_col=0, quoting=3)
    return df_specif, tri_lemma(df_specif, seuil_banalité)

def compute_specifs_function(df_k, path_out, T, dictionnaire_t, seuil,minsup_percent, execution_time,early_pos4lemma):
    dictionnaire_f = df_k.T.sum(axis=1).to_dict()
    dictionnaire_k = df_k.to_dict()
    données_specifs = []
    if early_pos4lemma==".*":
        early_pos4lemma="allPos"
    for motif in dictionnaire_k.keys():
        for texte in dictionnaire_k[motif].keys():
            données_specifs.append({
                "fichier":texte,
                "motif":motif,
                "k":dictionnaire_k[motif][texte],
                "f":dictionnaire_f[motif],
                "t":dictionnaire_t[texte],
                "T":T    
                })
    df_spec = pd.DataFrame(données_specifs)
    file_out=f"{path_out}{seuil}{early_pos4lemma}SpecifsLemma.tsv"
    print("file specif out !")
    df_spec.to_csv(file_out, sep="\t", encoding="utf-8", index=False)
    print("begining computing with R")
    compute_CQP._run_specifs_rscript(
        minsup_percent,
        execution_time,
        path_out,
        file_out,
        seuil,
        early_pos4lemma,
    )
    return f"{path_out}specif_{seuil}{early_pos4lemma}{execution_time}.tsv"
    
def tri_lemma(df,seuil_banalité):
    lignes = df[df.gt(seuil_banalité).any(axis=1)].index.tolist()
    return lignes
    
def main(seuil, minsup_percent, path_metadata, partition_cible, seuil_banalité, early_pos4lemma, filter_specifs, path_out=None, path_lexique=None, registry_path=None):
    """
    Early selection des lemmes pour la recherche.
    
    Args:
        path_out: Chemin vers le dossier earlySelection (fourni par main.py)
        path_lexique: Chemin vers le fichier dico_str_to_int_all_items.pk (fourni par main.py)
        registry_path: Chemin vers le registry CWB (fourni par main.py)
        partition_cible: Nom de la colonne metadata utilisee pour regrouper les textes
    """
    execution_time = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mmin%Ss")
    
    project_root = Path(__file__).resolve().parents[1]

    # Utiliser les chemins fournis ou les chemins alignés sur la structure actuelle.
    if path_out is None:
        path_out = str(project_root / "Data" / "earlySelection")
    if path_lexique is None:
        path_lexique = str(project_root / "Data" / "Lexiques" / "dico_str_to_int_all_items.pk")
    if registry_path is None:
        raise ValueError("registry_path doit etre fourni a early_selection.main().")
    
    # Normaliser le chemin pour qu'il se termine par /
    if not path_out.endswith("/"):
        path_out += "/"
    
    lexique = tools.load_pickles(path_lexique)
    
    # Créer le dossier si nécessaire
    if not os.path.exists(path_out):
        os.makedirs(path_out, exist_ok=True)
    
    if early_pos4lemma == ".*":
        early_pos4lemma = "allPos"
    
    make_again = True
    for file in os.listdir(path_out):
        if file.startswith(f"{filter_specifs}_specif{seuil_banalité}_{seuil}{early_pos4lemma}") and file.endswith(".tsv"):
            make_again = False
            print(f"EarlySelection computing already exists with {file} \\n delete it if you want to compute from scratch")
            df = pd.read_csv(f"{path_out}{file}", sep="\\t", index_col=0, quoting=3)
            lignes = df.index.tolist()
            if filter_specifs == True:
                lignes = tri_lemma(df, seuil_banalité)
            break
    
    if make_again == True:
        df_target = pd.read_csv(path_metadata, sep="\\t", index_col=0)
        df_lemma, T, dictionnaire_t = compute_early_df_lemmes(seuil, early_pos4lemma, registry_path)
        df_targetXlemmes = compute_CQP.textes2metadata(df_lemma, df_target, partition_cible)
        if filter_specifs == True:
            dictionnaire_t_result = dictionnaire_t_target(dictionnaire_t, df_target, partition_cible)
            specif_output_path = compute_specifs_function(
                df_targetXlemmes,
                path_out,
                T,
                dictionnaire_t_result,
                seuil,
                minsup_percent,
                execution_time,
                early_pos4lemma,
            )
            df_specif, lignes = _load_specif_rows(specif_output_path, seuil_banalité)
            df_specif.to_csv(f"{path_out}{filter_specifs}_specif{seuil_banalité}_{seuil}{early_pos4lemma}.tsv", sep="\\t")
        else:
            lignes = df_lemma.index.tolist()
    
    print(lignes)
    with open(f"{path_out}List_{filter_specifs}_specif{seuil_banalité}_{seuil}{early_pos4lemma}.txt", "w") as f:
        f.write(str(lignes))
    
    liste_lemma = []
    for l in lignes:
        lemma_preformat = f'lemma_"{l}"'
        liste_lemma.append(lexique[lemma_preformat])
    
    return liste_lemma
