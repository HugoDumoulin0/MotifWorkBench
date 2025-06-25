#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 19 13:50:43 2025

@author: hugodumoulin
"""
import formate_patterns
import time
import tools
import os
import pandas as pd
import re
# import compute_am_r
import datetime
import subprocess
import enslave_perl


         

def compute_k_specifs_CQP(liste_motifs_clos_corpus, minsup_percent):
    total_motifs=len(liste_motifs_clos_corpus)
    motif_count = 0
    lexic_int_str = formate_patterns.make_dict_int_to_str()
    noms_lignes = []
    for motif in liste_motifs_clos_corpus:
        noms_lignes.append(formate_patterns.from_int_to_str(motif, lexic_int_str))
    registry_path = "./Data/cwb-corpus/registry"
    lignes_table = [] 
    for motif in noms_lignes:
        trad_motif = str(tools.read_req_CQP(motif))
        print(trad_motif)
        ligne_de_table = enslave_perl.cqp_freq_motifs(trad_motif)
        lignes_table.append(ligne_de_table)
    df = pd.DataFrame(lignes_table, index=noms_lignes)
    df.to_csv(f"./Patterns_results/Specifs_noZero/{minsup_percent}_AFC_R_df.tsv", sep="\t")
    subprocess.call(["Rscript", "./src/AFC.r"]) #(moved here by analogy)
    return df
    
# minsup_percent = 25

# DMT4_clos_corpus = f"./Patterns_results/Closed/{minsup_percent}_00_DMT4_merged_files_sorted_closed.pk"
# liste_motifs_clos_corpus = tools.from_pk_corpus_to_list(DMT4_clos_corpus)   
# compute_k_specifs_CQP(liste_motifs_clos_corpus, minsup_percent)
    
    