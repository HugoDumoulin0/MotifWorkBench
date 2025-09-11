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

def compute_early_df_lemmes(seuil):
    T, dictionnaire_t = enslave_perl.cqp_general()
    registry_path = "./Data/cwb-corpus/registry"
    lignes_table = []
    print("indexing lemma")
    liste_lemma = enslave_perl.cqp_index_lemma()
    print("index done")
    nombre = len(liste_lemma[:seuil])
    print(f"Computing {nombre} lemma freq X texte...")
    print("index done")
    indice=0
    for lemma in liste_lemma[:seuil]:
        req = f'[lemma="{lemma}"]'
        indice+=1
        print(f"{lemma} {indice}")
        ligne_de_table = enslave_perl.cqp_freq_textes(req)
        lignes_table.append(ligne_de_table)
    df_lemma = pd.DataFrame(lignes_table, index=liste_lemma[:seuil])
    df_lemma = df_lemma.fillna(0)
    df_lemma = df_lemma.apply(pd.to_numeric)
    return df_lemma, T, dictionnaire_t

# def textes2metadata(df, df_target, metadata):
#     df_combined = df.T
#     df_combined[metadata] = df_target[metadata]
#     # On groupe par target et on additionne les lemmes
#     df_targetXlemmes = df_combined.groupby(metadata).sum()  
#     return df_targetXlemmes

def dictionnaire_t_target(dictionnaire_t, df_target,partition_cible):
    df_target["taille"]=df_target.index.map(dictionnaire_t)
    dictionnaire_t_result = df_target.groupby(partition_cible)["taille"].sum().to_dict()
    return dictionnaire_t_result

def compute_specifs(df_k, path_out, T, dictionnaire_t, seuil,minsup_percent, execution_time):
    dictionnaire_f = df_k.T.sum(axis=1).to_dict()
    dictionnaire_k = df_k.to_dict()
    données_specifs = []
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
    file_out=f"{path_out}{seuil}SpecifsLemma.tsv"
    print("file specif out !")
    # file_out_spec = "./Patterns_results/Specifs_noZero/spec_R_temp.tsv" #Store data under temp file to give to R with fixed name
    # file_out_spec = "./Patterns_results/Specifs_noZero/{}_spec_R_df_{}.tsv".format(mins,execution_time)
    df_spec.to_csv(file_out, sep="\t", encoding="utf-8", index=False)
    print("begining computing with R")
    subprocess.call(["Rscript", "./src/compute_specifs_noZero.r", str(minsup_percent), str(execution_time), path_out, file_out]) #Run R!
    
def tri_lemma(execution_time,seuil_banalité):
    liste = os.listdir("./Data/earlySPECIFS")
    for file in liste:
        if f"specif_{execution_time}" in file:
            df = pd.read_csv(f"./Data/earlySPECIFS/{file}", sep="\t", index_col=0, quoting=3)
    # df.drop(columns=["std_dev"], inplace=True)
    lignes = df[df.gt(seuil_banalité).any(axis=1)].index.tolist()
    return lignes
    
def main(seuil, minsup_percent, path_metadata, partition_cible, seuil_banalité):
    if not os.path.exists("./Data/earlySPECIFS"):
        os.mkdir("./Data/earlySPECIFS/")
    path_out = "./Data/earlySPECIFS/"
    path_lexique = "./Data/Lexiques/dico_str_to_int_all_items.pk"
    lexique = tools.load_pickles(path_lexique)
    df_target = pd.read_csv(path_metadata, sep="\t", index_col=0)
    # execution_time = datetime.datetime.now()
    execution_time  = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mmin%Ss")
    df_lemma, T, dictionnaire_t= compute_early_df_lemmes(seuil)
    df_targetXlemmes = compute_CQP.textes2metadata(df_lemma, df_target, partition_cible)
    dictionnaire_t_result = dictionnaire_t_target(dictionnaire_t, df_target, partition_cible)
    compute_specifs(df_targetXlemmes, path_out, T, dictionnaire_t_result, seuil, minsup_percent, execution_time)
    lignes = tri_lemma(execution_time, seuil_banalité)
    print(lignes)
    liste_lemma = []
    for l in lignes:
        lemma_preformat = f'lemma_"{l}"'
        liste_lemma.append(lexique[lemma_preformat])
    return liste_lemma
        #aller chercher le dico from str to int de  lexique
        # mettre sous format de liste à donner aux extracteurs


    
# main(20,"")
###attention sorties incohérentes
