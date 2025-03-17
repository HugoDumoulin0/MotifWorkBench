#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar  8 23:19:09 2025

@author: hugodumoulin
"""

import count_motifs_orig
import formate_patterns
import time
import tools
import os
import pandas as pd
import stats_vocab
import re


def count_tokens_in_conll(corpus_path):
    token_count = 0
    # Ouvrir le fichier CoNLL et lire ligne par ligne
    with open(corpus_path, 'r') as file:
        for line in file:
            # Ignore les lignes vides et les lignes de commentaire (en général, les lignes commencent par '#')
            if line.strip() and not line.startswith("#"):
                # Compte chaque token (chaque mot dans une ligne)
                token_count += 1
    return token_count

def compute_k_specifs(types_textes, liste_motifs_clos_corpus, T, dictionnaire_t):
    dictionnaire_k = {}
    total_textes=len(types_textes)
    texte_count = 0
    occ_count = 0
    formate_patterns.make_dict_int_to_str()
    for type_texte in types_textes:
        start_time = time.time()
        dictionnaire_k[type_texte]={}
        taille_texte = dictionnaire_t[type_texte] 
        print(type_texte)
        file_path = f"./Data/Textes_tagged_stanza/{type_texte}/{type_texte}"
        dict_file_motif = count_motifs_orig.count_motif(file_path, liste_motifs_clos_corpus, type_texte)
        dictionnaire_k[type_texte]=dict_file_motif
        end_time = time.time()
        texte_count += 1
        occ_count += taille_texte
        iteration_time = end_time - start_time
        remaining_textes = total_textes - texte_count
        remaining_occ = T - occ_count
        estimated_time_remaining = (iteration_time * remaining_occ)/taille_texte
        print(f"Compte des fréquences par texte : temps estimé restant pour {remaining_textes} texte(s) : {estimated_time_remaining/60:.2f} minutes")
    return dictionnaire_k

def compute_f_specifs(dictionnaire_k, liste_motifs_clos_corpus):
    dictionnaire_f = {}
    for motif in liste_motifs_clos_corpus:
        f = 0
        for type_texte in dictionnaire_k.keys():
                f += dictionnaire_k[type_texte][str(motif)]
        dictionnaire_f[str(motif)]=f
    return dictionnaire_f

def compute_t_specifs(types_textes):
    dictionnaire_t = {}
    for type_texte in types_textes:
        corpus_path = f"./Data/Textes_tagged_stanza/{type_texte}/{type_texte}"
        dictionnaire_t[type_texte] = count_tokens_in_conll(corpus_path)
    return dictionnaire_t
    
def compute_T_specifs(dictionnaire_t):
    T = 0
    for type_texte in dictionnaire_t.keys():
        T += dictionnaire_t[type_texte]
    return T

def fichier_synth(dictionnaire_f, dictionnaire_k, dictionnaire_t, T, liste_motifs_clos_corpus, shortcut_specifs):
    lexic_int_str = formate_patterns.make_dict_int_to_str()
    dict_synth = {}
    for fichier in dictionnaire_k:
        dict_synth[fichier]={}
        total_motifs = len(dictionnaire_k[fichier])
        motif_count = 0
        # for motif in dictionnaire_k[fichier]:
        for motif in liste_motifs_clos_corpus:
            motif_count += 1
            start_time_iter = time.time()
            f = dictionnaire_f[str(motif)]
            t = dictionnaire_t[fichier]
            k = dictionnaire_k[fichier][str(motif)]
            # if k==None:
            #     indice=None
            #     M=None
            # else:
            # if k==None:
            #     if motif in dictionnaire_specifs[fichier]["dict_frequents"]:
            #         k = dictionnaire_specifs[fichier]["dict_frequents"][motif]
            #     else:
            #         k=0
            if shortcut_specifs==True:
                indice = 0
                M=0
            else:
                indice = tools.indice_specificite(k,f,t,T)[0]
                M = tools.indice_specificite(k,f,t,T)[1]
            print(motif,formate_patterns.from_int_to_str(motif, lexic_int_str), k, M,f, t, T, indice)
            print("\n")
            dict_synth[fichier][str(motif)]=[motif,
                                formate_patterns.from_int_to_str(motif, lexic_int_str),
                                k,
                                M,
                                f,
                                t,
                                T, 
                                indice]
            end_time_iter = time.time()
            iteration_time = end_time_iter - start_time_iter
            remaining_motifs = total_motifs - motif_count
            estimated_time_remaining = iteration_time * remaining_motifs
            print(f"Dans {fichier}, temps estimé restant pour {remaining_motifs} motif(s) : {estimated_time_remaining/60:.2f} minutes")
    columns = ["motifs_int","motifs_str", "k", "M", "f", "t", "T", "indice"] 
    return dict_synth, columns

def add_association_vocab(dict_synth, liste_fichiers, columns):
    index_filtered, T = stats_vocab.build_index_filtered(liste_fichiers)
    for fichier in liste_fichiers:
        print(fichier)
        count_total = 0
        for motif in dict_synth[fichier]:
            if dict_synth[fichier][str(motif)][7]==None or dict_synth[fichier][str(motif)][7]=="inf" or dict_synth[fichier][str(motif)][7]>2:
                count_total += 1
        total_motifs=count_total
        motif_count = 0
        for motif in dict_synth[fichier]:                
            if dict_synth[fichier][str(motif)][7]==None or dict_synth[fichier][str(motif)][7]=="inf" or dict_synth[fichier][str(motif)][7]>2:
                print(motif)
                forme = dict_synth[fichier][str(motif)][1]
                start_time_iter = time.time()
                motif_count += 1
                if re.search("wp_", forme):
                    indice_association=""
                else:
                    req=stats_vocab.read_req(forme)
                    print(req)
                    indice_association = stats_vocab.association_req_vocab_specific(req, index_filtered, fichier, T)
                    print(indice_association)
                end_time_iter = time.time()
                iteration_time = end_time_iter - start_time_iter
                remaining_motifs = total_motifs - motif_count
                estimated_time_remaining = iteration_time * remaining_motifs
                print(f"Dans {fichier}, temps estimé restant pour {remaining_motifs} fichier(s) : {estimated_time_remaining/60:.2f} minutes")
            else:
                indice_association=""
            dict_synth[fichier][str(motif)].append(indice_association)
        dict_synth_add_association = dict_synth
        columns.append("association_vocab")
    return dict_synth_add_association, columns

def tsv_out(dict_synth, columns, minsup_percent):
    mins=minsup_percent
    for fichier in dict_synth:
        if not os.path.exists("./Patterns_results/Specifs_noZero"):
            os.makedirs("./Patterns_results/Specifs_noZero")
        file_out = "./Patterns_results/Specifs_noZero/{}_00_{}.pk".format(mins,
                                                                           fichier)
        tools.save_pickles_results(dict_synth[fichier], file_out)
        df = pd.DataFrame.from_dict(dict_synth[fichier], orient="index", columns=columns)
        df_sort = df.sort_values(by="indice", ascending=False)
        df_sort.to_csv(file_out.replace("pk", "tsv"), sep="\t", encoding="utf-8")
        
def all_synth_tsv_out(dict_synth, liste_motifs, minsup_percent):
    dict_out = {}
    mins=minsup_percent
    lexic_int_str = formate_patterns.make_dict_int_to_str()
    liste_fichier = []
    for fichier in dict_synth:
        liste_fichier.append(fichier)
    for motif in liste_motifs:
        dict_out[str(motif)]=[motif,
                                formate_patterns.from_int_to_str(motif, lexic_int_str)]
        for fichier in liste_fichier:
    # for fichier in liste_fichier:
        # for motif in dict_synth[fichier]:
            dict_out[str(motif)].append(dict_synth[fichier][str(motif)][7])
                # else:
                #     dict_out[motif].append("None")
    file_out = "./Patterns_results/Specifs_noZero/{}_synthèse.pk".format(mins)
    tools.save_pickles_results(dict_out, file_out)
    columns = ["motifs_int", "motifs_str"]
    columns=columns+liste_fichier
    df = pd.DataFrame.from_dict(dict_out, orient="index", columns=columns)
    df.to_csv(file_out.replace("pk", "tsv"), sep="\t", encoding="utf-8")
    return dict_out
    
def df_mouture_R_dict_synth(dict_synth, liste_motifs, minsup_percent):
    dict_spec_out = {}
    dict_AFC_out = {}
    mins=minsup_percent
    lexic_int_str = formate_patterns.make_dict_int_to_str()
    liste_fichier=[]
    for fichier in dict_synth:
        liste_fichier.append(fichier)
    for motif in liste_motifs:
        dict_spec_out[str(motif)]=[motif,
                            formate_patterns.from_int_to_str(motif, lexic_int_str)]
        dict_AFC_out[str(motif)]=[motif,
                            formate_patterns.from_int_to_str(motif, lexic_int_str)]
        for fichier in liste_fichier:
            dict_spec_out[str(motif)] += dict_synth[fichier][str(motif)][2:]
            dict_AFC_out[str(motif)] += [dict_synth[fichier][str(motif)][2]]
    file_out_spec = "./Patterns_results/Specifs_noZero/{}_specR_df.pk".format(mins)
    file_out_AFC = "./Patterns_results/Specifs_noZero/{}_AFC_R_df.pk".format(mins)
    tools.save_pickles_results(dict_spec_out, file_out_spec)
    tools.save_pickles_results(dict_AFC_out, file_out_AFC)
    columns_base = ["motifs_int", "motifs_str"]
    liste_columns_spec=[]
    liste_columns_AFC=[]
    for fichier in liste_fichier:
        items = ["k", "M", "f", "t", "T", "indice"]
        liste_columns_AFC.append(f"{fichier}")
        for item in items:
            liste_columns_spec.append(f'{fichier}_{item}')
    columns_spec=columns_base+liste_columns_spec
    columns_AFC=columns_base+liste_columns_AFC
    df_spec = pd.DataFrame.from_dict(dict_spec_out, orient="index", columns=columns_spec)
    df_AFC= pd.DataFrame.from_dict(dict_AFC_out, orient="index", columns=columns_AFC)
    df_spec.to_csv(file_out_spec.replace("pk", "tsv"), sep="\t", encoding="utf-8")
    df_AFC.to_csv(file_out_AFC.replace("pk", "tsv"), sep="\t", encoding="utf-8")
    return dict_spec_out, dict_AFC_out

def main(types_textes, shortcut_specifs, shortcut_association, minsup_percent):
    DMT4_clos_corpus = f"./Patterns_results/Closed/{minsup_percent}_00_DMT4_merged_files_sorted_closed.pk"
    liste_motifs_clos_corpus = count_motifs_orig.from_pk_corpus_to_list(DMT4_clos_corpus)
    dictionnaire_t = compute_t_specifs(types_textes)
    T = compute_T_specifs(dictionnaire_t)
    dictionnaire_k = compute_k_specifs(types_textes, liste_motifs_clos_corpus, T, dictionnaire_t)
    dictionnaire_f = compute_f_specifs(dictionnaire_k, liste_motifs_clos_corpus)
    dict_synth, columns = fichier_synth(dictionnaire_f, dictionnaire_k, dictionnaire_t, T, liste_motifs_clos_corpus, shortcut_specifs)
    if shortcut_association==False:
        dict_synth_add_association, columns = add_association_vocab(dict_synth, types_textes, columns)
    tsv_out(dict_synth, columns, minsup_percent)
    all_synth_tsv_out(dict_synth, liste_motifs_clos_corpus, minsup_percent)
    df_mouture_R_dict_synth(dict_synth, liste_motifs_clos_corpus, minsup_percent)
    tools.save_pickles_results(dictionnaire_t,"Patterns_results/Specifs_noZero/dictionnaire_t.pk")
    tools.save_pickles_results(dictionnaire_f,"Patterns_results/Specifs_noZero/dictionnaire_f.pk")
    tools.save_pickles_results(dictionnaire_k,"Patterns_results/Specifs_noZero/dictionnaire_k.pk")

# types_textes = os.listdir("./Data/Textes_tagged_stanza/")
# if ".DS_Store" in types_textes:
#     types_textes.remove(".DS_Store")
# shortcut_specifs = True
# shortcut_association = True
# main(types_textes, shortcut_specifs, shortcut_association)
    