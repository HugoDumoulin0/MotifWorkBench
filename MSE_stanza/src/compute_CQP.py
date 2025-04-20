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


def compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, minsup_percent):
    total_motifs=len(liste_motifs_clos_corpus)
    motif_count = 0
    lexic_int_str = formate_patterns.make_dict_int_to_str()
    liste_motifs_str = []
    
    for motif in liste_motifs_clos_corpus:
        liste_motifs_str.append(formate_patterns.from_int_to_str(motif, lexic_int_str))
        
    registry_path = "./Data/cwb-corpus/registry"
    lignes_table = [] 
    
    print("Computing motif freq X texte...")
    for motif in liste_motifs_str:
        trad_motif = str(tools.read_req_CQP(motif))
        print(trad_motif)
        ligne_de_table = enslave_perl.cqp_motifs(trad_motif)
        lignes_table.append(ligne_de_table)
        
    df_k = pd.DataFrame(lignes_table, index=liste_motifs_str)
    df_k = df_k.apply(pd.to_numeric)
    df_k.to_csv(f"./Patterns_results/Specifs_noZero/{minsup_percent}_AFC_R_df.tsv", sep="\t")
    subprocess.call(["Rscript", "./src/AFC.r"]) #(moved here by analogy)
    return df_k
    

def compute_specifs(df_k, minsup_percent, execution_time, specifs):
    dictionnaire_f = df_k.sum(axis=1).to_dict()
    dictionnaire_k = df_k.T.to_dict()
    T, dictionnaire_t = enslave_perl.cqp_general()
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
    file_out_spec = "./Patterns_results/Specifs_noZero/spec_R_temp.tsv" #Store data under temp file to give to R with fixed name
    # file_out_spec = "./Patterns_results/Specifs_noZero/{}_spec_R_df_{}.tsv".format(mins,execution_time)
    df_spec.to_csv(file_out_spec, sep="\t", encoding="utf-8", index=False)
    if specifs==True:
        subprocess.call(["Rscript", "./src/compute_specifs_noZero.r", str(minsup_percent), str(execution_time)]) #Run R!
    



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
        


def clean_last_AFC():
    liste = os.listdir("./Patterns_results/Specifs_noZero")
    for fichier in liste:
        if fichier.endswith("_AFC_R_df.tsv"):
            os.remove(f"./Patterns_results/Specifs_noZero/{fichier}")

def main(types_textes, shortcut_specifs, shortcut_association, minsup_percent, specifs):
    execution_time = datetime.datetime.now()
    DMT4_clos_corpus = f"./Patterns_results/Closed/{minsup_percent}_00_DMT4_merged_files_sorted_closed.pk"
    liste_motifs_clos_corpus = tools.from_pk_corpus_to_list(DMT4_clos_corpus)
    cwb.main()
    # if shortcut_association==False:
    #     dict_synth_add_association, columns = add_association_vocab(dict_synth, types_textes, columns)
    clean_last_AFC()
    df_k = compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, minsup_percent)
    compute_specifs(df_k, minsup_percent, execution_time, specifs)
    
    
    