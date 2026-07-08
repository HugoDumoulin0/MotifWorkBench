#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import subprocess

import pandas as pd

import compute_CQP
import enslave_perl
import tools
from r_runtime import resolve_rscript


def compute_early_df_lemmes(seuil, early_pos4lemma, registry_path=""):
    if not registry_path:
        raise ValueError("registry_path est requis pour compute_early_df_lemmes().")
    T, dictionnaire_t = enslave_perl.cqp_general(registry_path)
    lignes_table = []
    print("indexing lemma")
    liste_lemma = enslave_perl.cqp_index_lemma(early_pos4lemma, registry_path)
    print("index done")
    nombre = len(liste_lemma[:seuil])
    print(f"Computing {nombre} lemma freq X texte...")
    print("index done")
    indice = 0
    for lemma in liste_lemma[:seuil]:
        req = f'[lemma="{lemma}"]'
        indice += 1
        print(f"{indice} {lemma}")
        ligne_de_table = enslave_perl.cqp_freq_textes(req, registry_path)
        lignes_table.append(ligne_de_table)
    df_lemma = pd.DataFrame(lignes_table, index=liste_lemma[:seuil])
    df_lemma = df_lemma.fillna(0)
    df_lemma = df_lemma.apply(pd.to_numeric)
    return df_lemma, T, dictionnaire_t


def dictionnaire_t_target(dictionnaire_t, df_target, partition_cible):
    df_target["taille"] = df_target.index.map(dictionnaire_t)
    dictionnaire_t_result = df_target.groupby(partition_cible)["taille"].sum().to_dict()
    return dictionnaire_t_result


def compute_specifs_function(df_k, path_out, T, dictionnaire_t, seuil, minsup_percent, execution_time, early_pos4lemma):
    dictionnaire_f = df_k.T.sum(axis=1).to_dict()
    dictionnaire_k = df_k.to_dict()
    donnees_specifs = []
    safe_early_pos4lemma = compute_CQP.sanitize_path_component(early_pos4lemma)
    for motif in dictionnaire_k.keys():
        for texte in dictionnaire_k[motif].keys():
            donnees_specifs.append({
                "fichier": texte,
                "motif": motif,
                "k": dictionnaire_k[motif][texte],
                "f": dictionnaire_f[motif],
                "t": dictionnaire_t[texte],
                "T": T,
            })
    df_spec = pd.DataFrame(donnees_specifs)
    file_out = f"{path_out}{seuil}{safe_early_pos4lemma}SpecifsLemma.tsv"
    print("file specif out !")
    df_spec.to_csv(file_out, sep="	", encoding="utf-8", index=False)
    print("begining computing with R")
    subprocess.call([
        resolve_rscript(), "./src/compute_specifs.r", str(minsup_percent), str(execution_time),
        path_out, file_out, str(seuil), str(safe_early_pos4lemma)
    ])
    return f"{path_out}specif_{seuil}{safe_early_pos4lemma}{execution_time}.tsv"


def tri_lemma(df, seuil_banalite):
    lignes = df[df.gt(seuil_banalite).any(axis=1)].index.tolist()
    return lignes


def main(seuil, minsup_percent, path_metadata, partition_cible, seuil_banalite, early_pos4lemma, filter_specifs, dir_early_selection="", dir_lexiques="", registry_path=""):
    if not dir_early_selection:
        raise ValueError("dir_early_selection est requis pour early_selection.main().")
    if not dir_lexiques:
        raise ValueError("dir_lexiques est requis pour early_selection.main().")
    if not registry_path:
        raise ValueError("registry_path est requis pour early_selection.main().")

    execution_time = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mmin%Ss")
    path_out = dir_early_selection + "/"
    path_lexique = f"{dir_lexiques}/dico_str_to_int_all_items.pk"
    lexique = tools.load_pickles(path_lexique)
    if not os.path.exists(dir_early_selection):
        os.makedirs(dir_early_selection, exist_ok=True)

    raw_early_pos4lemma = early_pos4lemma if early_pos4lemma else ".*"
    safe_early_pos4lemma = compute_CQP.sanitize_path_component(raw_early_pos4lemma)

    make_again = True
    for file in os.listdir(dir_early_selection):
        if file.startswith(f"{filter_specifs}_specif{seuil_banalite}_{seuil}{safe_early_pos4lemma}") and file.endswith(".tsv"):
            make_again = False
            print(f"EarlySelection computing already exists with {file}\n delete it if you want to compute from scratch")
            df = pd.read_csv(f"{dir_early_selection}/{file}", sep="	", index_col=0, quoting=3)
            lignes = df.index.tolist()
            if filter_specifs is True:
                lignes = tri_lemma(df, seuil_banalite)
            break

    if make_again is True:
        df_target = pd.read_csv(path_metadata, sep="	", index_col=0)
        df_lemma, T, dictionnaire_t = compute_early_df_lemmes(seuil, raw_early_pos4lemma, registry_path)
        df_targetXlemmes = compute_CQP.textes2metadata(df_lemma, df_target, partition_cible)
        if filter_specifs is True:
            dictionnaire_t_result = dictionnaire_t_target(dictionnaire_t, df_target, partition_cible)
            specif_path = compute_specifs_function(
                df_targetXlemmes, path_out, T, dictionnaire_t_result,
                seuil, minsup_percent, execution_time, raw_early_pos4lemma
            )
            if os.path.exists(specif_path):
                df_spec = pd.read_csv(specif_path, sep="	", index_col=0, quoting=3)
                lignes = tri_lemma(df_spec, seuil_banalite)
            else:
                lignes = df_lemma.index.tolist()
            df_lemma.to_csv(
                f"{dir_early_selection}/{filter_specifs}_specif{seuil_banalite}_{seuil}{safe_early_pos4lemma}.tsv",
                sep="	"
            )
        else:
            lignes = df_lemma.index.tolist()
            df_lemma.to_csv(
                f"{dir_early_selection}/{filter_specifs}_specif{seuil_banalite}_{seuil}{safe_early_pos4lemma}.tsv",
                sep="	"
            )

    print(lignes)
    with open(f"{dir_early_selection}/List_{filter_specifs}_specif{seuil_banalite}_{seuil}{safe_early_pos4lemma}.txt", "w", encoding="utf-8") as f:
        f.write(str(lignes))

    liste_lemma = []
    for l in lignes:
        lemma_preformat = f'lemma_"{l}"'
        if lemma_preformat in lexique:
            liste_lemma.append(lexique[lemma_preformat])
    return liste_lemma
