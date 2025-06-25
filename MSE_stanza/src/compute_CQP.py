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


def compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, execution_time, path_out, total_motifs):
    motif_count = 0
    lexic_int_str = formate_patterns.make_dict_int_to_str()
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
    prefixe="motifs/"
    path_out=path_out+prefixe
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    file_out=f"{path_out}motifsTexte_df_{execution_time}.tsv"
    df_k.to_csv(file_out, sep="\t")
    subprocess.call(["Rscript", "./src/AFC.R", file_out, path_out]) #(moved here by analogy)
    return df_k, total_motifs, file_out
    
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
    prefixe="lemma/"
    path_out=path_out+prefixe
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    file_out = f"{path_out}{seuil}_lemmaTexte_df_{execution_time}.tsv"
    df_lemma.to_csv(file_out, sep="\t")
    subprocess.call(["Rscript", "./src/AFC.R", file_out, path_out]) 
    return file_out

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
    df_pos.to_csv(file_out, sep="\t")
    subprocess.call(["Rscript", "./src/AFC.R", file_out, path_out])
    return file_out


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

def main(types_textes, shortcut_specifs, shortcut_association, minsup_percent, specifs):
    execution_time = datetime.datetime.now()
    DMT4_clos_corpus = f"./Patterns_results/Closed/{minsup_percent}_00_DMT4_merged_files_sorted_closed.pk"
    liste_motifs_clos_corpus = tools.from_pk_corpus_to_list(DMT4_clos_corpus)
    total_motifs=len(liste_motifs_clos_corpus)
    T, dictionnaire_t = enslave_perl.cqp_general()
    
    path_R="./Patterns_results/R/"
    if not os.path.exists(path_R):
        os.mkdir(path_R)
    path_out = path_R+str(minsup_percent)+"/"
    results = {}
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    if not os.path.exists(f"./Patterns_results/R/{minsup_percent}/motifs"):
        df_k, total_motifs, file_out_motifs = compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, execution_time, path_out, total_motifs)
        compute_specifs(df_k, minsup_percent, execution_time, specifs, path_out, T, dictionnaire_t)
        results["motifs"] = file_out_motifs
    if not os.path.exists(f"./Patterns_results/R/{minsup_percent}/pos"):
        file_out_pos = compute_freq_TextesPos_AFC( execution_time, path_out)
        results["pos"] = file_out_pos
    if not os.path.exists(f"./Patterns_results/R/{minsup_percent}/lemma"):
        file_out_lemma = compute_freq_TextesLemma_AFC(total_motifs, execution_time, path_out)
        results["lemma"] = file_out_lemma
    if classification:
        if not os.path.exists("./Patterns_results/R/20000lemma"):
            file_out_20000lemma = compute_freq_Textes20000Lemma_noAFC(execution_time, path_R)
            results["20000lemma"] = file_out_20000lemma
        if not os.path.exists("./Patterns_results/R/10000bigramslemma"):
             file_out_bigrams, seuil = compute_freq_Textes_BigramsLemma_noAFC(execution_time, path_R)
             results[f"{seuil}bigrams"] = file_out_bigrams
    # if shortcut_association==False:
    #     dict_synth_add_association, columns = add_association_vocab(dict_synth, types_textes, columns)
    return results
    
    
    