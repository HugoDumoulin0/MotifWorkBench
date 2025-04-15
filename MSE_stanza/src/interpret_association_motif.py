#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 15:17:28 2025

@author: hugodumoulin
"""
import os 
import pandas as pd
import time
from collections import Counter
from grewpy import Corpus, Request
from stats_vocab import index_frequence_lemmes
from grew import read_req, index
from tools import indice_specificite

def make_dict_motifs(path_motifs):
    dict_motifs = {}
    liste_clusters = os.listdir(path_motifs)
    # nb_clusters = len(liste_clusters)
    for cluster in liste_clusters:
        if cluster!=".DS_Store":
            dict_motifs[cluster] = []
            df = pd.read_csv(path_motifs+cluster, skiprows=1, names=["motifs", "score"])
            for motif in df["motifs"]:
                dict_motifs[cluster].append(motif)
    return dict_motifs
            
def build_index_motif(file, motif):
    corpus_grew = Corpus(file)
    request = read_req(motif)
    param_viz="lemma"
    index_motif= index(corpus_grew,request,param_viz)
    # print(index)
    return index_motif

def construire_dict_contenu_motif(path_corpus, liste_fichiers, motif):
    dict_k_contenu_motifs = Counter()
    taille_t_fenetre = 0
    for file in liste_fichiers:
        if file!=".DS_Store":
            index_motif = build_index_motif(path_corpus+file+"/"+file, motif)
            for occurrence in index_motif:
                print(motif + ":" + str(occurrence))
                for lemma_occ in occurrence:
                    dict_k_contenu_motifs[lemma_occ]+=1
                    taille_t_fenetre +=1 
    return dict_k_contenu_motifs, taille_t_fenetre
    
def indice_out(dict_k_contenu_motifs, taille_t_fenetre, index_corpus):
    dict_indice = {}
    for lemma in dict_k_contenu_motifs.keys():
        dict_indice[lemma] = {}
        k = dict_k_contenu_motifs[lemma]
        t = taille_t_fenetre
        f = index_corpus["index_général"][lemma]
        T = index_corpus["index_général"]["taille_index_fichier"]
        indice = indice_specificite(k,f,t,T)[0]
        M = indice_specificite(k,f,t,T)[1]
        dict_indice[lemma]["indice"] = indice
        dict_indice[lemma]["M"] = M
    return dict_indice

def sorties(dict_indice, cluster, motif): 
    df = pd.DataFrame.from_dict(dict_indice, orient='index').reset_index()
    df.columns = ["lemma", "indice", "M"]
    df_sorted = df.sort_values(by="indice", ascending=False)
    df.to_csv(f"{path_motifs}${cluster[:-4]}_{motif}_specific_lemmas.tsv", sep="\t")

def main(path_corpus, path_motifs):
    liste_fichiers = os.listdir(path_corpus)
    index_corpus = index_frequence_lemmes(liste_fichiers)
    print("Index_corpus done !")
    dict_motifs=make_dict_motifs(path_motifs)

    total_it = sum(len(cluster) for cluster in dict_motifs.keys())
    iteration_actuelle=0
    start_it=time.time()
    
    for cluster in dict_motifs.keys():
        print(cluster)
        for motif in dict_motifs[cluster]:
            print(motif)
            dict_k_contenu_motifs, taille_t_fenetre = construire_dict_contenu_motif(path_corpus, liste_fichiers, motif)
            dict_indice = indice_out(dict_k_contenu_motifs, taille_t_fenetre, index_corpus)
            sorties(dict_indice, cluster, motif)
            
            elapsed = time.time()-start_it
            iteration_actuelle+=1
            avg_time = elapsed / iteration_actuelle
            temps_restant=(total_it-iteration_actuelle)*avg_time
            print(f"  ⏱ Temps estimé restant : {temps_restant/60:.1f} minutes ({temps_restant:.1f} s)")


path_corpus="./Data/Textes_tagged_stanza/" 
# motif = '{pos_"ADJ"} {pos_"ADP"} {pos_"DET"} {pos_"NOUN"}'

path_motifs = "./Patterns_results/R_05/motifs_cluster/"
main(path_corpus, path_motifs)
    