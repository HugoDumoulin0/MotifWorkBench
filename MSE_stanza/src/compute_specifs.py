#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 14:59:51 2025

@author: hugodumoulin
"""

import formate_patterns
import pandas as pd
import time
import os
import tools
import re
# import stats_vocab

def data_for_specifs(liste_fichiers):
    dictionnaire_specifs = {}
    mins = "25"
    for fichier in liste_fichiers:
        dictionnaire_specifs[fichier]={}
        dictionnaire_specifs[fichier]["dict_clos"] = tools.load_pickles("./Patterns_results/Closed/{}_00_DMT4_{}_files_sorted_closed.pk".format(mins, fichier))
        dictionnaire_specifs[fichier]["dict_frequents"] = tools.load_pickles("./Patterns_results/Freq/{}_00_DMT4_{}_files_sorted_freq.pk".format(mins, fichier))
        dictionnaire_specifs[fichier]["t"]=tools.get_nbr_seq("./Data/DMT4_files/DMT4_{}_files_sorted.txt".format(fichier))
        # dictionnaire_specifs[fichier]["t"]=get_nbr_seq("./DMT4_{}_files_sorted.txt".format(fichier))
    return dictionnaire_specifs
    
def compute_T_in_specifs(dictionnaire_specifs):
    T = 0
    for fichier in dictionnaire_specifs:
        T = T + dictionnaire_specifs[fichier]["t"]
    return T

def compute_k_specifs(dictionnaire_specifs, liste_motifs):
    dictionnaire_k = {}
    for fichier in dictionnaire_specifs:
        print(fichier)
        dictionnaire_k[fichier]={}
        for motif in liste_motifs:
            dictionnaire_k[fichier][motif] = {}
            if motif in dictionnaire_specifs[fichier]["dict_clos"]:
                k = dictionnaire_specifs[fichier]["dict_clos"][motif]
            else: #quand motif n'est pas clos dans fichier (n'est pas présent dans dictionnaire_specifs[fichier]["dict_clos"])
                k=None
            # if motif in dictionnaire_specifs[fichier]["dict_frequents"]:
            #     k = dictionnaire_specifs[fichier]["dict_frequents"][motif]
            # else: 
            #     k=0
            dictionnaire_k[fichier][motif] = k
    return dictionnaire_k
 
    
def compute_f_specifs(dictionnaire_specifs):
     dictionnaire_f = {}
     liste_motifs = []
     for fichier in dictionnaire_specifs:
         for motif in dictionnaire_specifs[fichier]["dict_clos"]:
             if motif not in liste_motifs:
                 liste_motifs.append(motif)
     for motif in liste_motifs:
         f = 0
         for fichier in dictionnaire_specifs:
             if motif in dictionnaire_specifs[fichier]["dict_frequents"]:
                 f = f + dictionnaire_specifs[fichier]["dict_frequents"][motif]
             dictionnaire_f[motif] = f
     return dictionnaire_f, liste_motifs
    
def fichier_synth(dictionnaire_f, dictionnaire_k, dictionnaire_specifs, T, liste_motifs, shortcut_specifs):
    lexic_int_str = formate_patterns.make_dict_int_to_str()
    dict_synth = {}
    for fichier in dictionnaire_k:
        dict_synth[fichier]={}
        total_motifs = len(dictionnaire_k[fichier])
        motif_count = 0
        # for motif in dictionnaire_k[fichier]:
        for motif in liste_motifs:
            motif_count += 1
            start_time_iter = time.time()
            f = dictionnaire_f[motif]
            t = dictionnaire_specifs[fichier]["t"]
            k = dictionnaire_k[fichier][motif]
            # if k==None:
            #     indice=None
            #     M=None
            # else:
            if k==None:
                if motif in dictionnaire_specifs[fichier]["dict_frequents"]:
                    k = dictionnaire_specifs[fichier]["dict_frequents"][motif]
                else:
                    k=0
            if shortcut_specifs==True:
                indice = 0
                M=0
            else:
                indice = tools.indice_specificite(k,f,t,T)[0]
                M = tools.indice_specificite(k,f,t,T)[1]
            print(formate_patterns.from_str_to_list(motif),formate_patterns.from_int_to_str(motif, lexic_int_str), k, M,f, t, T, indice)
            print("\n")
            dict_synth[fichier][motif]=[formate_patterns.from_str_to_list(motif),
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
            print(f"Dans {fichier}, temps estimé restant pour {remaining_motifs} fichier(s) : {estimated_time_remaining/60:.2f} minutes")
            columns = ["motifs_int","motifs_str", "k", "M", "f", "t", "T", "indice"] 
    return dict_synth, columns

def add_association_vocab(dict_synth, liste_fichiers, columns):
    index_filtered, T = stats_vocab.build_index_filtered(liste_fichiers)
    for fichier in liste_fichiers:
        print(fichier)
        count_total = 0
        for motif in dict_synth[fichier]:
            if dict_synth[fichier][motif][7]==None or dict_synth[fichier][motif][7]=="inf" or dict_synth[fichier][motif][7]>2:
                count_total += 1
        total_motifs=count_total
        motif_count = 0
        for motif in dict_synth[fichier]:                
            if dict_synth[fichier][motif][7]==None or dict_synth[fichier][motif][7]=="inf" or dict_synth[fichier][motif][7]>2:
                print(motif)
                forme = dict_synth[fichier][motif][1]
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
            dict_synth[fichier][motif].append(indice_association)
        dict_synth_add_association = dict_synth
        columns.append("association_vocab")
    return dict_synth_add_association, columns

def tsv_out(dict_synth, columns):
    mins="25"
    for fichier in dict_synth:
        if not os.path.exists("./Patterns_results/Specifs"):
            os.makedirs("./Patterns_results/Specifs")
        file_out = "./Patterns_results/Specifs/{}_00_{}.pk".format(mins,
                                                                           fichier)
        tools.save_pickles_results(dict_synth[fichier], file_out)
        df = pd.DataFrame.from_dict(dict_synth[fichier], orient="index", columns=columns)
        df_sort = df.sort_values(by="indice", ascending=False)
        df_sort.to_csv(file_out.replace("pk", "tsv"), sep="\t", encoding="utf-8")
        
def all_synth_tsv_out(dict_synth, liste_motifs):
    dict_out = {}
    mins="25"
    lexic_int_str = formate_patterns.make_dict_int_to_str()
    liste_fichier = []
    for fichier in dict_synth:
        liste_fichier.append(fichier)
    for motif in liste_motifs:
        dict_out[motif]=[formate_patterns.from_str_to_list(motif),
                                formate_patterns.from_int_to_str(motif, lexic_int_str)]
        for fichier in liste_fichier:
    # for fichier in liste_fichier:
        # for motif in dict_synth[fichier]:
            dict_out[motif].append(dict_synth[fichier][motif][7])
                # else:
                #     dict_out[motif].append("None")
    file_out = "./Patterns_results/Specifs/{}_synthèse.pk".format(mins)
    tools.save_pickles_results(dict_out, file_out)
    columns = ["motifs_int", "motifs_str"]
    columns=columns+liste_fichier
    df = pd.DataFrame.from_dict(dict_out, orient="index", columns=columns)
    df.to_csv(file_out.replace("pk", "tsv"), sep="\t", encoding="utf-8")
    return dict_out
    
def df_mouture_R_dict_synth(dict_synth, liste_motifs):
    dict_spec_out = {}
    dict_AFC_out = {}
    mins="25"
    lexic_int_str = formate_patterns.make_dict_int_to_str()
    liste_fichier=[]
    for fichier in dict_synth:
        liste_fichier.append(fichier)
    for motif in liste_motifs:
        dict_spec_out[motif]=[formate_patterns.from_str_to_list(motif),
                            formate_patterns.from_int_to_str(motif, lexic_int_str)]
        dict_AFC_out[motif]=[formate_patterns.from_str_to_list(motif),
                            formate_patterns.from_int_to_str(motif, lexic_int_str)]
        for fichier in liste_fichier:
            dict_spec_out[motif] += dict_synth[fichier][motif][2:]
            dict_AFC_out[motif] += [dict_synth[fichier][motif][2]]
    file_out_spec = "./Patterns_results/Specifs/{}_specR_df.pk".format(mins)
    file_out_AFC = "./Patterns_results/Specifs/{}_AFC_R_df.pk".format(mins)
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
    df = pd.DataFrame.from_dict(dict_spec_out, orient="index", columns=columns_spec)
    df = pd.DataFrame.from_dict(dict_AFC_out, orient="index", columns=columns_AFC)
    df.to_csv(file_out_spec.replace("pk", "tsv"), sep="\t", encoding="utf-8")
    df.to_csv(file_out_AFC.replace("pk", "tsv"), sep="\t", encoding="utf-8")
    return dict_spec_out, dict_AFC_out

def main(liste_fichiers, shortcut_specifs, shortcut_association):
    dictionnaire_specifs = data_for_specifs(liste_fichiers)
    T = compute_T_in_specifs(dictionnaire_specifs)
    dictionnaire_f, liste_motifs = compute_f_specifs(dictionnaire_specifs)
    dictionnaire_k = compute_k_specifs(dictionnaire_specifs, liste_motifs)
    dict_synth, columns = fichier_synth(dictionnaire_f, dictionnaire_k, dictionnaire_specifs, T, liste_motifs, shortcut_specifs)
    if shortcut_association==False:
        dict_synth_add_association, columns = add_association_vocab(dict_synth, liste_fichiers, columns)
    tsv_out(dict_synth, columns)
    all_synth_tsv_out(dict_synth, liste_motifs)
    df_mouture_R_dict_synth(dict_synth, liste_motifs)
    tools.save_pickles_results(dictionnaire_specifs,"Patterns_results/Specifs/dictionnaire_specifs.pk")
    tools.save_pickles_results(dictionnaire_f,"Patterns_results/Specifs/dictionnaire_f.pk")
    tools.save_pickles_results(dictionnaire_k,"Patterns_results/Specifs/dictionnaire_k.pk")

# liste_fichiers = os.listdir("./Data/Textes_tagged_stanza")
# if ".DS_Store" in liste_fichiers:
#     liste_fichiers.remove(".DS_Store")
# shortcut_specifs = True
# shortcut_association = True
# main(liste_fichiers)
