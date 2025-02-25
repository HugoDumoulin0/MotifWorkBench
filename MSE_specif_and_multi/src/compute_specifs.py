#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 14:59:51 2025

@author: hugodumoulin
"""

import pickle as pk
import formate_patterns
import numpy as np
from scipy.stats import hypergeom
import pandas as pd
import time
import os

def save_pickles_results(to_save, title_file):
    """
    input: file
    ouput: bool
    do: save the object locally
    """
    try:
        with open(title_file, "wb") as p:
            pk.dump(to_save, p)
        print("\tResults : saved")
        return True
    except:
        return False

def load_pickles(title_file):
    with open(title_file, "rb") as p:
        return pk.load(p)

def get_nbr_seq(dmt4_files):
    with open("{}".format(dmt4_files), 'r', encoding="utf-8") as dmt4 :
        return len([line for line in dmt4.readlines() if "seqId" in line])

def from_dict_to_df(path_emergent_dict):
    emergent_patt = load_pickles(path_emergent_dict)
    df = pd.DataFrame.from_dict(emergent_patt, orient="index", columns=["motifs_int", "motifs_str", "k","M", "f", "t", "T", "indice"])
    df_sort = df.sort_values(by="indice", ascending=False)
    df_sort.to_csv(path_emergent_dict.replace("pk", "tsv"), sep="\t", encoding="utf-8")
    return True


def data_for_specifs(liste_fichiers):
    dictionnaire_specifs = {}
    mins = "25"
    for fichier in liste_fichiers:
        dictionnaire_specifs[fichier]={}
        dictionnaire_specifs[fichier]["dict_clos"] = load_pickles("./Patterns_results/Closed/{}_00_DMT4_{}_files_sorted_closed.pk".format(mins, fichier))
        dictionnaire_specifs[fichier]["dict_frequents"] = load_pickles("./Patterns_results/Freq/{}_00_DMT4_{}_files_sorted_freq.pk".format(mins, fichier))
        dictionnaire_specifs[fichier]["t"]=get_nbr_seq("./Data/DMT4_files/DMT4_{}_files_sorted.txt".format(fichier))
        # dictionnaire_specifs[fichier]["t"]=get_nbr_seq("./DMT4_{}_files_sorted.txt".format(fichier))
    return dictionnaire_specifs

def compute_T_in_specifs(dictionnaire_specifs):
    T = 0
    for fichier in dictionnaire_specifs:
        T = T + dictionnaire_specifs[fichier]["t"]
    return T

def compute_k_specifs(dictionnaire_specifs):
    dictionnaire_k = {}
    for fichier in dictionnaire_specifs:
        print(fichier)
        dictionnaire_k[fichier]={}
        for motif in dictionnaire_specifs[fichier]["dict_clos"]:
            dictionnaire_k[fichier][motif] = {}
            k = dictionnaire_specifs[fichier]["dict_clos"][motif]
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
     return dictionnaire_f


def indice_specificite(k,f,t,T):
    rv = hypergeom(T, f, t)
    x = np.arange(0, f+1)
    M = np.argmax(rv.pmf(x)) #valeur modale
    if k > np.argmax(rv.pmf(x)):
        indice = -np.log10(1-rv.cdf(k))
    else:
        indice = np.log10(rv.cdf(k))
    return indice, M

def tsv_sortie(dictionnaire_f, dictionnaire_k, dictionnaire_specifs, T):
    mins="25"
    lexic_int_str = formate_patterns.make_dict_int_to_str()
    dict_synth = {}
    for fichier in dictionnaire_k:
        dict_synth[fichier]={}
        total_motifs = len(dictionnaire_k[fichier])
        motif_count = 0
        for motif in dictionnaire_k[fichier]:
            motif_count += 1
            start_time_iter = time.time()
            f = dictionnaire_f[motif]
            k = dictionnaire_k[fichier][motif]
            t = dictionnaire_specifs[fichier]["t"]
            indice = indice_specificite(k,f,t,T)[0]
            M = indice_specificite(k,f,t,T)[1]
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
    if not os.path.exists("./Patterns_results/Specifs"):
        os.makedirs("./Patterns_results/Specifs")
    file_out = "./Patterns_results/Specifs/{}_00_{}.pk".format(mins,
                                                                       fichier)
    save_pickles_results(dict_synth[fichier], file_out)
    from_dict_to_df(file_out)
    return dict_synth

def synth_out(dict_synth):
    dict_out = {}
    mins="25"
    lexic_int_str = formate_patterns.make_dict_int_to_str()
    liste_fichier = []
    for fichier in dict_synth:
        liste_fichier.append(fichier)
    for fichier in liste_fichier:
        for motif in dict_synth[fichier]:
            dict_out[motif]=[formate_patterns.from_str_to_list(motif),
                                formate_patterns.from_int_to_str(motif, lexic_int_str)]
            for fichier in dict_synth:
                if motif in dict_synth[fichier]:
                    dict_out[motif].append(dict_synth[fichier][motif][7])
                else:
                    dict_out[motif].append("-inf")
    file_out = "./Patterns_results/Specifs/{}_synth.pk".format(mins)
    save_pickles_results(dict_out, file_out)
    columns = ["motifs_int", "motifs_str"]
    columns=columns+liste_fichier
    df = pd.DataFrame.from_dict(dict_out, orient="index", columns=columns)
    df.to_csv(file_out.replace("pk", "tsv"), sep="\t", encoding="utf-8")


def main(liste_fichiers):
    dictionnaire_specifs = data_for_specifs(liste_fichiers)
    T = compute_T_in_specifs(dictionnaire_specifs)
    print(T)
    dictionnaire_f = compute_f_specifs(dictionnaire_specifs)
    dictionnaire_k = compute_k_specifs(dictionnaire_specifs)
    dict_synth = tsv_sortie(dictionnaire_f, dictionnaire_k, dictionnaire_specifs, T)
    synth_out(dict_synth)
    save_pickles_results(dictionnaire_specifs,"Patterns_results/Specifs/dictionnaire_specifs.pk")
    save_pickles_results(dictionnaire_f,"Patterns_results/Specifs/dictionnaire_f.pk")
    save_pickles_results(dictionnaire_k,"Patterns_results/Specifs/dictionnaire_k.pk")


liste_fichiers = ["MODYCO", "ISP"]
main(liste_fichiers)
