#!/usr/bin/env python
# coding: utf-8

"""
@author: Mekki 2022
"""


import os
import re
import sys
import time
import pprint
import pickle as pk
import numpy as np
import pandas as pd
from mesure_S2MP import *
from regroupement import *
from multiprocessing import Pool

import formate_patterns



def compute_index_freq(c1, obj):
    """
    input: 1. list(list(cluster)
           2. str(obj) : "itemset"|"item"
    ouput: dict({str(obj):float(freqObj_c1)})
    do: compute the obj's freq in c1
    """
    index_freq = {}
    for seq in c1:
        for itemsets in seq:
            if obj == "itemset":
                key_seq = str(itemsets)
                index_freq[key_seq] = index_freq.get(key_seq, 0) + 1 / len(c1)
            if obj == "item":
                for item in itemsets:
                    key_seq = str(item)
                    index_freq[key_seq] = index_freq.get(key_seq, 0) + 1 / len(c1)
    return index_freq
   

def match_patt(patt_to_find, seq):
    """
    """
    matchs_patt = list()
    set_patt = list()
    
    itemsets = list(seq.values())
    len_patt = len(patt_to_find)
    
    for n in range(len(seq)):
        slide = itemsets[n:n+len_patt]
        if len(slide) < len_patt: continue
        elif sum([patt_to_find[p].issubset(slide[p]) 
                for p in range(len_patt)]) == len_patt:
            matchs_patt.append(list(range(n+1, n+1+len_patt)))
            set_patt+=list(range(n+1, n+1+len_patt))
    return set(set_patt)

def ponderation_recouvrement(patt_to_find, corpus_dmt4):
    cp = 0
    for id_seq in corpus_dmt4:
        seq = corpus_dmt4.get(id_seq)
        matches = match_patt(patt_to_find, seq)
        if len(matches) != 0:
            cp += 1
    return cp

def elect_rep_c(c1, obj, ponderation, emergent_patterns, corpus_dmt4):
    """
    input: 1. list(list(cluster)
           2. str(obj) : "itemset"|"item"
           3. bool(ponderation) : 0 | 1
           4. df(emergent_patterns)
    output: representant pattern for cluster 
            ex : [{263681, 27, 263692, 263758}, {43}]

    do: elect representant pattern for the cluster c1
    """
    index_frequences = compute_index_freq(c1, obj)
    compute_score_itemset = lambda index_frequences, seq : sum([index_frequences.get(str(itemset)) 
                                                                for itemset 
                                                                in seq])/len(seq)
    
    compute_score_item = lambda index_frequences, seq : sum([sum([index_frequences.get(str(item)) 
                                                                 for item 
                                                                 in itemset]) 
                                                             for itemset in seq])/len(seq)
    
    if obj == "itemset":
        
        if ponderation == False:
            all_score_itemset = [compute_score_itemset(index_frequences, seq) for seq in c1]
            p = c1[all_score_itemset.index(max(all_score_itemset))]
            return p, get_GR(p,emergent_patterns)
        
        if ponderation == True :
            all_score_itemset_GR = list()
            all_gr = list()
            for patt in c1:
                score = compute_score_itemset(index_frequences, patt)
                gr = get_GR(patt, emergent_patterns)
                all_score_itemset_GR.append(score*gr)
                all_gr.append(gr)
            max_score = max(all_score_itemset_GR)
            index_rep_c1 = all_score_itemset_GR.index(max_score)
            rep_c1 = c1[index_rep_c1]
            print("Represensant : ", rep_c1, "\tScore : ", max_score)
            return rep_c1, all_gr[index_rep_c1]
        
        if ponderation =="recouvrement":
            all_score_itemset_recouvrement = list()
            all_gr = list()
            for patt in c1:
                score = compute_score_itemset(index_frequences, patt)
                gr = get_GR(patt, emergent_patterns)
                recouvrement = ponderation_recouvrement(patt, corpus_dmt4)
                all_score_itemset_recouvrement.append(score*recouvrement)
                all_gr.append(gr)
            max_score = max(all_score_itemset_recouvrement)
            index_rep_c1 = all_score_itemset_recouvrement.index(max_score)
            rep_c1 = c1[index_rep_c1]
            print("Represensant : ", rep_c1, "\tScore : ", max_score)
            return rep_c1, all_gr[index_rep_c1]
        
    if obj == "item":
        
        if ponderation == False:
            all_score_items = [compute_score_item(index_frequences, seq) 
                                 for seq 
                                 in c1]
            p = c1[all_score_items.index(max(all_score_items))]
            return p, get_GR(p,emergent_patterns)
        
        if ponderation == True:
            all_score_items_GR = list()
            all_gr = list()
            for patt in c1:
                score = compute_score_item(index_frequences, patt)
                gr = get_GR(patt, emergent_patterns)
                all_score_items_GR.append(score*gr)
                all_gr.append(gr)
            max_score = max(all_score_items_GR)
            index_rep_c1 = all_score_items_GR.index(max_score)
            rep_c1 = c1[index_rep_c1]
            print("Represensant : ", rep_c1, "\tScore : ", max_score)
            return rep_c1, all_gr[index_rep_c1]

        if ponderation =="recouvrement":
            all_score_item_recouvrement = list()
            all_gr = list()
            for patt in c1:
                score = compute_score_item(index_frequences, patt)
                gr = get_GR(patt, emergent_patterns)
                recouvrement = ponderation_recouvrement(patt, corpus_dmt4)
                all_score_item_recouvrement.append(score*recouvrement)
                all_gr.append(gr)
            max_score = max(all_score_item_recouvrement)
            index_rep_c1 = all_score_item_recouvrement.index(max_score)
            rep_c1 = c1[index_rep_c1]
            print("Represensant : ", rep_c1, "\tScore : ", max_score)
            return rep_c1, all_gr[index_rep_c1]


def main_representant(clusters, obj, ponderation, emergent_patterns, corpus_dmt4, nbr_pool):
    """
    input: 1. list(list(cluster)
           2. str(obj) : "itemset"|"item"
           3. bool(ponderation) : 0 | 1
           4. df(emergent_patterns)
           5. int(nbr_pool)
    ouput: list(list(representant patterns)) : [[{13}, {54, 55}], [{54, 55}, {13}]]
    do: compute // representant patterns for all clusters
    """
    all_representants = []
    with Pool(nbr_pool) as pool:
        representants_clusters = pool.starmap(elect_rep_c, 
                                            [[clusters.get(c1),
                                              obj, 
                                              ponderation, 
                                              emergent_patterns,
                                              corpus_dmt4] 
                                            for c1 in clusters])
        all_representants += representants_clusters
    return all_representants




def main_extract_all_representant(type_1,
                                type_2,
                                clusters, 
                                centroids, 
                                emergent_patterns,
                                corpus_dmt4, 
                                nbr_pool=4):
    """
    input: 1. list(list(cluster)
           2. dict({int(index_cluster):tuple(centroids, score)})
           3. df(emergent_patterns)
           4. int(nbr_pool)
    output: df
    do: save and write results for all different kind of representant
    """

    save_df = lambda df_to_save, title_file : df_to_save.to_csv(title_file,
                                                                  sep="\t",
                                                                  encoding="utf-8")
    title_out = "./Representants_results/{}_{}_representants.tsv".format(type_1,
                                                                 type_2)
    df_motifs = pd.DataFrame()

    lexique = formate_patterns.load_lexique()

    print("\nRepresentants from medoids ---------------------- \n")
    all_medoids = [centroids.get(seq)[0] for seq in centroids]
    centroid_lexicalised = [formate_patterns.from_int_to_str(seq, lexique) for seq in all_medoids]
    df_motifs["medoids"] = centroid_lexicalised
    df_motifs["medoids_index"] = all_medoids
    df_motifs["medoids_GR"] = [get_GR(seq, emergent_patterns) for seq in all_medoids]
    print(df_motifs["medoids"][-3:])
    save_df(df_motifs, title_out)

    print("\nRepresentants compute on itemset ---------------------- \n")
    reps_itemset = main_representant(clusters, "itemset", 0, emergent_patterns, corpus_dmt4, nbr_pool)
    reps_itemset_lexicalised = [formate_patterns.from_int_to_str(rep[0], lexique) for rep in reps_itemset ]
    df_motifs["itemset"] = reps_itemset_lexicalised
    df_motifs["itemset_index"] = [p[0] for p in reps_itemset]
    df_motifs["itemset_GR"] = [p[1] for p in reps_itemset]
    print(df_motifs["itemset"][-3:])
    save_df(df_motifs, title_out)

    print("\nRepresentants compute on item ---------------------- \n")
    reps_item = main_representant(clusters, "item", 0, emergent_patterns, corpus_dmt4, nbr_pool)
    reps_item_lexicalised = [formate_patterns.from_int_to_str(rep[0], lexique) for rep in reps_item ]
    df_motifs["item"] = reps_item_lexicalised
    df_motifs["item_index"] = [p[0] for p in reps_item]
    df_motifs["item_GR"] = [p[1] for p in reps_item]
    print(df_motifs["item"][-3:])
    save_df(df_motifs, title_out)

    print("\nRepresentants compute on itemset * GR ---------------------- \n")
    reps_itemset_GR = main_representant(clusters, "itemset", 1, emergent_patterns, corpus_dmt4, nbr_pool)
    reps_itemset_GR_lexicalised = [formate_patterns.from_int_to_str(rep[0], lexique) for rep in reps_itemset_GR ]
    df_motifs["itemset*GR"] = reps_itemset_GR_lexicalised
    df_motifs["itemset*GR_index"] = [p[0] for p in reps_itemset_GR]
    df_motifs["itemset*GR_GR"] = [p[1] for p in reps_itemset_GR]
    print(df_motifs["itemset*GR"][-3:])
    save_df(df_motifs, title_out)

    print("\nRepresentants compute on item * GR ---------------------- \n")
    reps_item_GR = main_representant(clusters, "item", 1, emergent_patterns, corpus_dmt4, nbr_pool)
    reps_item_GR_lexicalised = [formate_patterns.from_int_to_str(rep[0], lexique) for rep in reps_item_GR ]
    df_motifs["item*GR"] = reps_item_GR_lexicalised
    df_motifs["item*GR_index"] = [p[0] for p in reps_item_GR]
    df_motifs["item*GR_GR"] = [p[1] for p in reps_item_GR]
    print(df_motifs["item*GR"][-3:])
    save_df(df_motifs, title_out)

    print("\nRepresentants compute on itemset * recouvrement ---------------------- \n")
    reps_itemset_recouvrement = main_representant(clusters, "itemset", "recouvrement", emergent_patterns, corpus_dmt4, nbr_pool)
    reps_itemset_GR_lexicalised = [formate_patterns.from_int_to_str(rep[0], lexique) for rep in reps_itemset_recouvrement ]
    df_motifs["itemset*recouvrement"] = reps_itemset_GR_lexicalised
    df_motifs["itemset*recouvrement_index"] = [p[0] for p in reps_itemset_recouvrement]
    df_motifs["itemset*recouvrement_GR"] = [p[1] for p in reps_itemset_recouvrement]
    print(df_motifs["itemset*recouvrement"][-3:])
    save_df(df_motifs, title_out)

    print("\nRepresentants compute on item * recouvrement ---------------------- \n")
    reps_item_recouvrement = main_representant(clusters, "item", "recouvrement", emergent_patterns, corpus_dmt4, nbr_pool)
    reps_item_GR_lexicalised = [formate_patterns.from_int_to_str(rep[0], lexique) for rep in reps_item_recouvrement ]
    df_motifs["item*recouvrement"] = reps_item_GR_lexicalised
    df_motifs["item*recouvrement_index"] = [p[0] for p in reps_item_recouvrement]
    df_motifs["item*recouvrement_GR"] = [p[1] for p in reps_item_recouvrement]
    print(df_motifs["item*recouvrement"][-3:])
    save_df(df_motifs, title_out)

    formate_patterns.dump_pk(df_motifs, title_out.replace("tsv", "pk"))
 
    return df_motifs

def extract_n_representants(rep_type, representants):

    nbr_final_patt = 19

    file_rep = representants.sort_values(by="{}_GR".format(rep_type), ascending=False)
    all_patt_lexic = list(file_rep["{}".format(rep_type)])
    all_patt_index = list(file_rep["{}_index".format(rep_type)])
    all_GR = list(file_rep["{}_GR".format(rep_type)])
    total_patt = len(all_patt_index)
    nbr_slice = int(str(total_patt/nbr_final_patt).split(".")[0])

    cp = 0
    final_patt = dict()

    for i in range(len(all_patt_index)):
        if cp >= total_patt: break
        final_patt["{}".format(rep_type)] = final_patt.get("{}".format(rep_type), list()) + [all_patt_lexic[cp]]
        final_patt["{}_index".format(rep_type)] = final_patt.get("{}_index".format(rep_type), list()) + [all_patt_index[cp]]
        final_patt["{}_GR".format(rep_type)] = final_patt.get("{}_GR".format(rep_type), list()) + [all_GR[cp]]
        cp += nbr_slice

    return final_patt

def main_select_representants(representants_pk_path):
    representants = formate_patterns.load_pk(representants_pk_path)
    list_representants = ["medoids",
                        "itemset",
                        "item", 
                        "itemset*GR",
                        "item*GR",
                        "itemset*recouvrement", 
                        "item*recouvrement"]
    # list_representants = ["itemset*GR",
    #                     "item*GR",
    #                     "itemset*recouvrement", 
    #                     "item*recouvrement"]
    dict_all_finalsRep = dict()

    for type_represenant in list_representants:
        dict_all_finalsRep.update(extract_n_representants(type_represenant, representants))

    df_out = pd.DataFrame.from_dict(dict_all_finalsRep)
    df_out.to_csv("./Representants_results/Representants_finaux/20_{}".format(os.path.basename(representants_pk_path).replace("pk", "tsv")),
                sep="\t", 
                encoding="utf-8")
    formate_patterns.dump_pk(df_out, "./Representants_results/Representants_finaux/20_{}".format(os.path.basename(representants_pk_path)))
    return df_out





