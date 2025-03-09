#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar  1 22:04:04 2025

@author: hugodumoulin
"""

from collections import Counter
import pandas as pd
import grew
import formate_patterns
import tools
from grewpy import Corpus
from tools import load_pickles

# dmt4_corpus = "/Users/hugodumoulin/Desktop/ArchivU/Travail/motifs/MSE_stanza_specifs_rapports_noSpecifs/Patterns_results/Closed/25_00_DMT4_ARSCAN_files_sorted_closed.pk"

def from_pk_corpus_to_list(dmt4_corpus):
    pk_dmt4_corpus = tools.load_pickles(dmt4_corpus)
    liste_motifs_clos_corpus = [] 
    for clef in pk_dmt4_corpus.keys():
        motif=[]
        mots = clef.split(" ")
        for mot in mots:
            mot = mot.strip("{}")
            mot = (set(map(int,mot.split(","))))
            motif.append(mot)
        liste_motifs_clos_corpus.append(motif)
    return liste_motifs_clos_corpus


def from_pk_file_to_list(dmt4_file):
    pk_dmt4_file = tools.load_pickles(dmt4_file)
    file_as_list = []
    for phrase in pk_dmt4_file.keys():
        phrase_as_list = []
        for mot in pk_dmt4_file[phrase].keys():
            phrase_as_list.append(pk_dmt4_file[phrase][mot])
        file_as_list.append(phrase_as_list)
    return file_as_list


def count_motif(file_path, liste_motifs_clos_corpus):
    lexic_int_str = tools.load_pickles("./Data/Lexiques/dico_int_to_str_all_items.pk")
    corpus_grew = Corpus(file_path)
    dict_file_motif={}
    for motif in liste_motifs_clos_corpus:
        print(motif)
        print(formate_patterns.from_int_to_str(motif, lexic_int_str))
        req = grew.read_req(formate_patterns.from_int_to_str(motif, lexic_int_str))
        indexx = grew.index(corpus_grew, req, "form")
        freq = len(indexx)
        dict_file_motif[motif]=freq
    return dict_file_motif
    
    
# dmt4_file = "/Users/hugodumoulin/Desktop/ArchivU/Travail/motifs/MSE_stanza_specifs_rapports_noSpecifs/Data/DMT4_files/DMT4_ARSCAN_dict_sorted.pk"
# liste_motifs_clos_corpus = from_pk_corpus_to_list(dmt4_corpus)
# file_as_list = from_pk_file_to_list(dmt4_file)

# file_out = "out_ARSCAN.pk"
# dict_file_motif=count_motif(file_as_list, liste_motifs_clos_corpus) 
# tools.save_pickles_results(dict_file_motif,file_out)
# df = pd.DataFrame.from_dict(dict_file_motif, orient="index", columns=["freq"])
# df.to_csv(file_out.replace("pk", "tsv"), sep="\t", encoding="utf-8")

# for phrase in pk_dmt4_file.keys():
#     for mot in pk_dmt4_file[phrase]:
#         for feat in pk_dmt4_file[phrase][mot]:
            
            
