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
    

def compute_specifs(df_k, minsup_percent, execution_time):
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
    subprocess.call(["Rscript", "./src/compute_specifs_noZero.r", str(minsup_percent), str(execution_time)]) #Run R!
    
        


    
# def compute_k_specifs(types_textes, liste_motifs_clos_corpus, T, dictionnaire_t, minsup_percent):
#     dictionnaire_k = {}
#     total_textes=len(types_textes)
#     texte_count = 0
#     occ_count = 0
#     formate_patterns.make_dict_int_to_str()
#     for type_texte in types_textes:
#         start_time = time.time()
#         dictionnaire_k[type_texte]={}
#         taille_texte = dictionnaire_t[type_texte] 
#         print(type_texte)
#         file_path = f"./Data/Textes_tagged_stanza/{type_texte}/{type_texte}"
#         dict_file_motif = count_motifs_orig.count_motif(file_path, liste_motifs_clos_corpus, type_texte)
#         dictionnaire_k[type_texte]=dict_file_motif
#         end_time = time.time()
#         texte_count += 1
#         occ_count += taille_texte
#         iteration_time = end_time - start_time
#         remaining_textes = total_textes - texte_count
#         remaining_occ = T - occ_count
#         estimated_time_remaining = (iteration_time * remaining_occ)/taille_texte
#         print(f"Compte des fréquences par texte : pour minsup {minsup_percent}, temps estimé restant pour {remaining_textes} texte(s) : {estimated_time_remaining/60:.2f} minutes")
#     return dictionnaire_k
                       
# def compute_f_specifs(dictionnaire_k, liste_motifs_clos_corpus):
#     dictionnaire_f = {}
#     for motif in liste_motifs_clos_corpus:
#         f = 0
#         for type_texte in dictionnaire_k.keys():
#                 f += dictionnaire_k[type_texte][str(motif)]
#         dictionnaire_f[str(motif)]=f
#     return dictionnaire_f

# def compute_t_specifs(types_textes):
#     dictionnaire_t = {}
#     for type_texte in types_textes:
#         corpus_path = f"./Data/Textes_tagged_stanza/{type_texte}/{type_texte}"
#         dictionnaire_t[type_texte] = tools.count_tokens_in_conll(corpus_path)
#     return dictionnaire_t
    
# def compute_T_specifs(dictionnaire_t):
#     T = 0
#     for type_texte in dictionnaire_t.keys():
#         T += dictionnaire_t[type_texte]
#     return T


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
        
# def all_synth_tsv_out(dict_synth, liste_motifs, minsup_percent, execution_time):
#     dict_out = {}
#     mins=minsup_percent
#     lexic_int_str = formate_patterns.make_dict_int_to_str()
#     liste_fichier = []
#     for fichier in dict_synth:
#         liste_fichier.append(fichier)
#     for motif in liste_motifs:
#         dict_out[str(motif)]=[motif,
#                                 formate_patterns.from_int_to_str(motif, lexic_int_str)]
#         for fichier in liste_fichier:
#     # for fichier in liste_fichier:
#         # for motif in dict_synth[fichier]:
#             dict_out[str(motif)].append(dict_synth[fichier][str(motif)][7])
#                 # else:
#                 #     dict_out[motif].append("None")
#     file_out = "./Patterns_results/Specifs_noZero/{}_synthèse_{}.pk".format(mins, execution_time)
#     tools.save_pickles_results(dict_out, file_out)
#     columns = ["motifs_int", "motifs_str"]
#     columns=columns+liste_fichier
#     df = pd.DataFrame.from_dict(dict_out, orient="index", columns=columns)
#     df.to_csv(file_out.replace("pk", "tsv"), sep="\t", encoding="utf-8")
#     return dict_out

# def df_spec(dict_synth, liste_motifs, minsup_percent,execution_time):
#     mins = minsup_percent
#     donnees_spec = []
#     lexic_int_str = formate_patterns.make_dict_int_to_str()
#     for fichier in dict_synth.keys():
#         for motif in liste_motifs:
#             donnees_spec.append({
#                     "fichier":fichier,
#                     "motif":formate_patterns.from_int_to_str(motif, lexic_int_str),
#                     "k":dict_synth[fichier][str(motif)][2],
#                     "f":dict_synth[fichier][str(motif)][4],
#                     "t":dict_synth[fichier][str(motif)][5],
#                     "T":dict_synth[fichier][str(motif)][6]
#                     })
#     df_spec = pd.DataFrame(donnees_spec)
#     file_out_spec = "./Patterns_results/Specifs_noZero/spec_R_temp.tsv" #Store data under temp file to give to R with fixed name
#     # file_out_spec = "./Patterns_results/Specifs_noZero/{}_spec_R_df_{}.tsv".format(mins,execution_time)
#     df_spec.to_csv(file_out_spec, sep="\t", encoding="utf-8", index=False)
    
#     subprocess.call(["Rscript", "./src/compute_specifs_noZero.r", str(minsup_percent), str(execution_time)]) #Run R!
    
#     return df_spec
    
# def df_AFC(dict_synth, liste_motifs, minsup_percent, execution_time):
#     dict_AFC_out = {}
#     mins=minsup_percent
#     lexic_int_str = formate_patterns.make_dict_int_to_str()
#     liste_fichier=[]
#     for fichier in dict_synth:
#         liste_fichier.append(fichier)
#     for motif in liste_motifs:
#         # dict_spec_out[str(motif)]=[motif,
#         #                     formate_patterns.from_int_to_str(motif, lexic_int_str)]
#         dict_AFC_out[str(motif)]=[motif,
#                             formate_patterns.from_int_to_str(motif, lexic_int_str)]
#         for fichier in liste_fichier:
#             # dict_spec_out[str(motif)] += dict_synth[fichier][str(motif)][2:]
#             dict_AFC_out[str(motif)] += [dict_synth[fichier][str(motif)][2]]
#     file_out_AFC = "./Patterns_results/Specifs_noZero/{}_AFC_R_df_{}.pk".format(mins, execution_time)
#     tools.save_pickles_results(dict_AFC_out, file_out_AFC)
#     columns_base = ["motifs_int", "motifs_str"]
#     liste_columns_AFC=[]
#     for fichier in liste_fichier:
#         # items = ["k", "M", "f", "t", "T", "indice"]
#         liste_columns_AFC.append(f"{fichier}")
#     columns_AFC=columns_base+liste_columns_AFC
#     df_AFC= pd.DataFrame.from_dict(dict_AFC_out, orient="index", columns=columns_AFC)
#     df_AFC.to_csv(file_out_AFC.replace("pk", "tsv"), sep="\t", encoding="utf-8")
    
#     file_out_AFC_for_calc = "./Patterns_results/Specifs_noZero/{}_AFC_R_df.tsv".format(mins)
#     df_AFC.to_csv(file_out_AFC_for_calc, sep="\t", encoding="utf-8")
   
#     subprocess.call(["Rscript", "./src/AFC.r"]) #(moved here by analogy)
    
#     return dict_AFC_out

def clean_last_AFC():
    liste = os.listdir("./Patterns_results/Specifs_noZero")
    for fichier in liste:
        if fichier.endswith("_AFC_R_df.tsv"):
            os.remove(f"./Patterns_results/Specifs_noZero/{fichier}")

def main(types_textes, shortcut_specifs, shortcut_association, minsup_percent):
    execution_time = datetime.datetime.now()
    DMT4_clos_corpus = f"./Patterns_results/Closed/{minsup_percent}_00_DMT4_merged_files_sorted_closed.pk"
    liste_motifs_clos_corpus = tools.from_pk_corpus_to_list(DMT4_clos_corpus)
    cwb.main()
    # if shortcut_association==False:
    #     dict_synth_add_association, columns = add_association_vocab(dict_synth, types_textes, columns)
    clean_last_AFC()
    df_k = compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, minsup_percent)
    compute_specifs(df_k, minsup_percent, execution_time)
    
    
    