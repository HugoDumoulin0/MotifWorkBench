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
import compute_CQP
import tools

def compute_early_df_lemmes(seuil, early_pos4lemma):
    T, dictionnaire_t = enslave_perl.cqp_general()
    registry_path = "./Data/cwb-corpus/registry"
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
    df_target["taille"]=df_target.index.map(dictionnaire_t)
    dictionnaire_t_result = df_target.groupby(partition_cible)["taille"].sum().to_dict()
    return dictionnaire_t_result

def compute_specifs(df_k, path_out, T, dictionnaire_t, seuil,minsup_percent, execution_time,early_pos4lemma):
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
    subprocess.call(["Rscript", "./src/compute_specifs_noZero.r", str(minsup_percent), str(execution_time), path_out, file_out, str(seuil), str(early_pos4lemma)]) #Run R!
    
def tri_lemma(execution_time,seuil_banalité,seuil,early_pos4lemma):
    liste = os.listdir("./Data/earlySPECIFS")
    fichiers = sorted(liste, key=lambda f: os.path.getmtime(os.path.join("./Data/earlySPECIFS", f)),reverse=True)
    if early_pos4lemma==".*":
        early_pos4lemma="allPos"
    for file in fichiers:
        if f"specif_{seuil}{early_pos4lemma}" in file:
            df = pd.read_csv(f"./Data/earlySPECIFS/{file}", sep="\t", index_col=0, quoting=3)
    lignes = df[df.gt(seuil_banalité).any(axis=1)].index.tolist()
    return lignes
    
def main(seuil, minsup_percent, path_metadata, partition_cible, seuil_banalité,early_pos4lemma):
    if not os.path.exists("./Data/earlySPECIFS"):
        os.mkdir("./Data/earlySPECIFS/")
    execution_time  = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mmin%Ss")
    path_out = "./Data/earlySPECIFS/"
    path_lexique = "./Data/Lexiques/dico_str_to_int_all_items.pk"
    lexique = tools.load_pickles(path_lexique)
    for file in os.listdir("./Data/earlySPECIFS"):
        if f"specif_{seuil}" in file:
            print(f"EarlySpecifs computing already exists with {file} \n delete it if you want to compute from scratch")
            break
    else:
        df_target = pd.read_csv(path_metadata, sep="\t", index_col=0)
        df_lemma, T, dictionnaire_t= compute_early_df_lemmes(seuil, early_pos4lemma)
        df_targetXlemmes = compute_CQP.textes2metadata(df_lemma, df_target, partition_cible)
        dictionnaire_t_result = dictionnaire_t_target(dictionnaire_t, df_target, partition_cible)
        compute_specifs(df_targetXlemmes, path_out, T, dictionnaire_t_result, seuil, minsup_percent, execution_time,early_pos4lemma)
        
    lignes = tri_lemma(execution_time, seuil_banalité,seuil,early_pos4lemma)
    print(lignes)
    liste_lemma = []
    for l in lignes:
        lemma_preformat = f'lemma_"{l}"'
        liste_lemma.append(lexique[lemma_preformat])
    return liste_lemma

