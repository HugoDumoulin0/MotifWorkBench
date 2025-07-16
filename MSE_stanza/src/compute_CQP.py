#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 17:28:58 2025

@author: hugodumoulin
"""



import formate_patterns
import time
import tools
import os
import pandas as pd
# import stats_vocab
import re
# import compute_am_r
import datetime
import subprocess
import enslave_perl
import cwb
from config import *


def textes2metadata(df, df_target, metadata):
    df_combined = df.T
    df_target = df_target.astype(str)
    df_combined[metadata] = df_target[metadata]
    # On groupe par target et on additionne les lemmes
    df_targetXlemmes = df_combined.groupby(metadata).sum()  
    return df_targetXlemmes


def add_total(df):
    df_total = df.copy()
    df_total["total"] = df.sum(axis=1)
    df_total = df_total.sort_values(by="total", ascending=False)
    return df_total

def compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, execution_time, path_out, total_motifs, lexic_int_str):
    motif_count = 0
    liste_motifs_str = []
    
    for motif in liste_motifs_clos_corpus:
        liste_motifs_str.append(formate_patterns.from_int_to_str(motif, lexic_int_str))
        
    registry_path = "./Data/cwb-corpus/registry"
    lignes_table = [] 
    
    nombre = len(liste_motifs_str)
    print(f"Computing {nombre} motifs freq X texte...")
    for motif in liste_motifs_str:
        trad_motif = str(tools.read_req_CQP(motif))
        print(trad_motif)
        ligne_de_table = enslave_perl.cqp_freq_textes(trad_motif)
        lignes_table.append(ligne_de_table)
        
    df_k = pd.DataFrame(lignes_table, index=liste_motifs_str)
    df_k = df_k.fillna(0)
    df_k = df_k.apply(pd.to_numeric) 
    prefixe=f"{total_motifs}motifs/"
    path_out=path_out+prefixe
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    file_out=f"{path_out}{total_motifs}motifsTexte_df_{execution_time}.tsv"
    file_total =f"{path_out}{total_motifs}motifsTexteOrdered_df_{execution_time}.tsv"
    # df_k.to_csv(file_out, sep="\t")
    # subprocess.call(["Rscript", "./src/AFC.R", file_out, path_out]) #(moved here by analogy)
    # df_k_total=add_total(df_k)
    # df_k_total.to_csv(file_total, sep="\t")
    return df_k, path_out, total_motifs, file_out, file_total
    
def compute_freq_TextesLemma_AFC(seuil, execution_time, path_out):
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
    prefixe=f"{seuil}lemma/"
    path_out=path_out+prefixe
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    file_out = f"{path_out}{seuil}_lemmaTexte_df_{execution_time}.tsv"
    file_total = f"{path_out}{seuil}_lemmaTexteOrdered_df_{execution_time}.tsv"

    # df_lemma.to_csv(file_out, sep="\t")
    # subprocess.call(["Rscript", "./src/AFC.R", file_out, path_out]) 
    # df_lemma=add_total(df_lemma)
    # df_lemma.to_csv(file_total, sep="\t")
    return file_out, path_out, df_lemma, file_total

def compute_freq_Textes_BigramsLemma_noAFC(execution_time, path_R):
    registry_path = "./Data/cwb-corpus/registry"
    lignes_table = []
    seuil = 10000
    print("indexing bigrams lemma")
    liste_bigrams_lemma = enslave_perl.cqp_index_property("bigrams_lemma")
    print("index done")
    print(f"Computing {seuil} bigrams_lemma freq X texte...")
    print("index done")
    indice=0
    for big in liste_bigrams_lemma[:seuil]:
        lemma1, lemma2 = big.split(" ")
        req = f'[lemma="{lemma1}"][lemma="{lemma2}"]'
        indice+=1
        print(f"{req} {indice}")
        ligne_de_table = enslave_perl.cqp_freq_textes(req)
        lignes_table.append(ligne_de_table)
    df_lemma = pd.DataFrame(lignes_table, index=liste_bigrams_lemma[:seuil])
    df_lemma = df_lemma.fillna(0)
    df_lemma = df_lemma.apply(pd.to_numeric)
    prefixe=f"{seuil}bigramslemma/"
    path_out=path_R+prefixe
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    file_out_bigrams = f"{path_out}{seuil}bigramslemmaTexte_df_{execution_time}.tsv"
    df_lemma.to_csv(file_out_bigrams, sep="\t")
    return file_out_bigrams, seuil

def compute_freq_Textes20000Lemma_noAFC(execution_time, path_R):
    registry_path = "./Data/cwb-corpus/registry"
    lignes_table = []
    print("indexing 20 000 lemma")
    liste_lemma = enslave_perl.cqp_index_lemma()
    print("index done")
    print("Computing 20 000 lemma freq X texte...")
    total=20000
    indice = 0
    for lemma in liste_lemma[:20000]:
        indice += 1
        lemma = f'[lemma="{lemma}"]'
        print(f"{lemma} {indice}")
        ligne_de_table = enslave_perl.cqp_freq_textes(lemma)
        lignes_table.append(ligne_de_table)
    df_lemma = pd.DataFrame(lignes_table, index=liste_lemma[:20000])
    df_lemma = df_lemma.fillna(0)
    df_lemma = df_lemma.apply(pd.to_numeric)
    prefixe="20000lemma/"
    path_out=path_R+prefixe
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    file_out = f"{path_out}{total}lemmaTexte_df_{execution_time}.tsv"
    df_lemma.to_csv(file_out, sep="\t")
    return file_out

def compute_freq_TextesPos_AFC(execution_time, path_out):
    registry_path = "./Data/cwb-corpus/registry"
    lignes_table = []
    print("indexing pos")
    liste_pos = enslave_perl.cqp_index_pos()
    print("index done")
    nombre = len(liste_pos)
    print(f"Computing {nombre} pos freq X texte...")
    for pos in liste_pos:
        pos = f'[pos="{pos}"]'
        ligne_de_table = enslave_perl.cqp_freq_textes(pos)
        lignes_table.append(ligne_de_table)
    df_pos = pd.DataFrame(lignes_table, index=liste_pos)
    df_pos = df_pos.fillna(0)
    df_pos = df_pos.apply(pd.to_numeric)
    prefixe="pos/"
    path_out=path_out+prefixe
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    file_out= f"{path_out}posTexte_df_{execution_time}.tsv"
    file_total= f"{path_out}posTexteOrdered_df_{execution_time}.tsv"

    # df_pos.to_csv(file_out, sep="\t")
    # subprocess.call(["Rscript", "./src/AFC.R", file_out, path_out])
    # df_pos=add_total(df_pos)
    # df_pos.to_csv(file_total, sep="\t")
    return file_out, path_out, df_pos, file_total


def compute_specifs(df_k, minsup_percent, execution_time, specifs, path_out, T, dictionnaire_t):
    dictionnaire_f = df_k.sum(axis=1).to_dict()
    dictionnaire_k = df_k.T.to_dict()
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
    prefixe="motifs/"
    path_out=path_out+prefixe
    file_out=f"{path_out}SpecifsMotifsTexte_df_{execution_time}.tsv"
    # file_out_spec = "./Patterns_results/Specifs_noZero/spec_R_temp.tsv" #Store data under temp file to give to R with fixed name
    # file_out_spec = "./Patterns_results/Specifs_noZero/{}_spec_R_df_{}.tsv".format(mins,execution_time)
    df_spec.to_csv(file_out, sep="\t", encoding="utf-8", index=False)
    default_folder = "./Patterns_results/R"
    if specifs==True:
        subprocess.call(["Rscript", "./src/compute_specifs_noZero.r", str(minsup_percent), str(execution_time), default_folder, file_out]) #Run R!

# def add_association_vocab(dict_synth, liste_fichiers, columns):
#     index_filtered, T = stats_vocab.build_index_filtered(liste_fichiers)
#     for fichier in liste_fichiers:
#         print(fichier)
#         count_total = 0
#         for motif in dict_synth[fichier]:
#             if dict_synth[fichier][str(motif)][7]==None or dict_synth[fichier][str(motif)][7]=="inf" or dict_synth[fichier][str(motif)][7]>2:
#                 count_total += 1
#         total_motifs=count_total
#         motif_count = 0
#         for motif in dict_synth[fichier]:                
#             if dict_synth[fichier][str(motif)][7]==None or dict_synth[fichier][str(motif)][7]=="inf" or dict_synth[fichier][str(motif)][7]>2:
#                 print(motif)
#                 forme = dict_synth[fichier][str(motif)][1]
#                 start_time_iter = time.time()
#                 motif_count += 1
#                 if re.search("wp_", forme):
#                     indice_association=""
#                 else:
#                     req=stats_vocab.read_req(forme)
#                     print(req)
#                     indice_association = stats_vocab.association_req_vocab_specific(req, index_filtered, fichier, T)
#                     print(indice_association)
#                 end_time_iter = time.time()
#                 iteration_time = end_time_iter - start_time_iter
#                 remaining_motifs = total_motifs - motif_count
#                 estimated_time_remaining = iteration_time * remaining_motifs
#                 print(f"Dans {fichier}, temps estimé restant pour {remaining_motifs} fichier(s) : {estimated_time_remaining/60:.2f} minutes")
#             else:
#                 indice_association=""
#             dict_synth[fichier][str(motif)].append(indice_association)
#         dict_synth_add_association = dict_synth
#         columns.append("association_vocab")
#     return dict_synth_add_association, columns
        


# def clean_last_AFC():
#     liste = os.listdir("./Patterns_results/Specifs_noZero")
#     for fichier in liste:
#         if fichier.endswith("_AFC_R_df.tsv"):
#             os.remove(f"./Patterns_results/Specifs_noZero/{fichier}")


def fusion_internal_clusters(df, lexic_int_str):
    internal_clusters = tools.load_pickles("./Clustering_results/Clusters/clustering_3.pk")
    medoids_clusters = tools.load_pickles("./Clustering_results/Medoids/medoids_3.pk")
    
    internal_clusters_str = {}
    for cluster_id, motifs in internal_clusters.items():
        internal_clusters_str[cluster_id]=[formate_patterns.from_int_to_str(motif, lexic_int_str) for motif in motifs]

    medoids_clusters_str = {k : formate_patterns.from_int_to_str(valeur[0], lexic_int_str) for k, valeur in medoids_clusters.items()}
    
    dfs_fusionnes = []
    
    for cluster_id, lignes_a_fusionner in internal_clusters_str.items():
        # Extraire les lignes du cluster
        print(lignes_a_fusionner)
        df_cluster = df.loc[lignes_a_fusionner]
        # Faire la somme des lignes (en ignorant l'index, en sommant les colonnes numériques)
        df_somme = df_cluster.sum(numeric_only=True).to_frame().T

        # Récupérer la ligne du médoïde
        medoid_index = medoids_clusters_str[cluster_id]
        df_medoid = df.loc[[medoid_index]]

        # Remplacer les colonnes numériques par la somme
        for col in df_somme.columns:
            df_medoid[col] = df_somme[col].values[0]    
            
        dfs_fusionnes.append(df_medoid)

    df_result = pd.concat(dfs_fusionnes)
    return df_result
     
def main(types_textes, shortcut_specifs, shortcut_association, minsup_percent,gap_min, gap_max, nb_itemset_min, specifs, df_metadata, metadata, internal_clustering):
    execution_time = datetime.datetime.now()
    lexic_int_str = formate_patterns.make_dict_int_to_str()
    DMT4_clos_corpus = f"./Patterns_results/Closed/{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}_DMT4_merged_files_sorted_closed.pk"
    liste_motifs_clos_corpus = tools.from_pk_corpus_to_list(DMT4_clos_corpus)
    total_motifs=len(liste_motifs_clos_corpus)
    T, dictionnaire_t = enslave_perl.cqp_general()
    
    path_R=f"./Patterns_results/R/{metadata}/itemset_min{nb_itemset_min}/gap_min{gap_min}/gap_max{gap_max}/"
    if not os.path.exists(path_R):
        path="./Patterns_results/R/"
        if not os.path.exists(path):
            os.mkdir(path)
        path= f"./Patterns_results/R/{metadata}/"
        if not os.path.exists(path):
            os.mkdir(path)
        path=f"./Patterns_results/R/{metadata}/itemset_min{nb_itemset_min}"
        if not os.path.exists(path):
            os.mkdir(path)
        path=f"./Patterns_results/R/{metadata}/itemset_min{nb_itemset_min}/gap_min{gap_min}/"
        if not os.path.exists(path):
            os.mkdir(path)
        path=f"./Patterns_results/R/{metadata}/itemset_min{nb_itemset_min}/gap_min{gap_min}/gap_max{gap_max}/"
        if not os.path.exists(path):
            os.mkdir(path)
    path_out = f"{path_R}minsup{str(minsup_percent)}/"
    results = {}
    if not os.path.exists(path_out):
            os.mkdir(path_out)

    if total_motifs>0:
        if not os.path.exists(f"{path_out}motifs"):
            df_k, path_out, total_motifs, file_out_motifs, file_total = compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, execution_time, path_out, total_motifs, lexic_int_str)
            if not metadata=="id":
                df_k = textes2metadata(df_k, df_metadata, metadata).T
            df_k.to_csv(file_out_motifs, sep="\t")
            if internal_clustering==True:
                df_k = fusion_internal_clusters(df_k, lexic_int_str)
                file_out_motifs = file_out_motifs[:-4]+"_FUS.tsv"
                df_k.to_csv(file_out_motifs, sep="\t")
            subprocess.call(["Rscript", "./src/AFC.R", file_out_motifs, path_out]) 
            df_k_total=add_total(df_k)
            df_k_total.to_csv(file_total, sep="\t")
        
                
            if specifs:       
                compute_specifs(df_k, minsup_percent, execution_time, specifs, path_out, T, dictionnaire_t)
            results["motifs"] = file_out_motifs
        # if not os.path.exists(f"{path_out}pos"):
        #     file_out_pos = compute_freq_TextesPos_AFC( execution_time, path_out)
        #     results["pos"] = file_out_pos
        # if not os.path.exists(f"{path_out}lemma"):
        #     file_out_lemma = compute_freq_TextesLemma_AFC(total_motifs, execution_time, path_out)
        #     results["lemma"] = file_out_lemma
        if classification:
            if not os.path.exists("f{path_out}20000lemma"):
                file_out_20000lemma = compute_freq_Textes20000Lemma_noAFC(execution_time, path_R)
                results["20000lemma"] = file_out_20000lemma
            if not os.path.exists("f{path_out}10000bigramslemma"):
                 file_out_bigrams, seuil = compute_freq_Textes_BigramsLemma_noAFC(execution_time, path_R)
                 results[f"{seuil}bigrams"] = file_out_bigrams
    else:
        if not os.path.exists(f"{path_out}zero-motifs"):
                os.mkdir(f"{path_out}zero-motifs")
    # if shortcut_association==False:
    #     dict_synth_add_association, columns = add_association_vocab(dict_synth, types_textes, columns)
    return results, path_out
    
    
    