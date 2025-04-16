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
# from tools import indice_specificite
import tools




#------notes du log de travail 16/04/25-------#
#j'ai essayé :
# – déléguer à R le calcul de l'indice de spécificité avec specificite_py == False
# – changer build_index_motif par build_index-motif_faster qui utilise corput.count()
# – merger tous les fichiers stanza pour économiser du temps d'ouverture de corpus avec tools.concat_preserve_ids()
#...et cela reste extrêmement lent : 5 heures pour faire les 12 séries de motifs contenus dans 6 clusters, sur un corpus de 5 millions de mots certes...





def make_dict_motifs(path_motifs):
    dict_motifs = {}
    liste_clusters = os.listdir(path_motifs)
    # nb_clusters = len(liste_clusters)
    for fichier in liste_clusters:
        if fichier!=".DS_Store" and fichier!="merged_temp":
            print(fichier)
            dict_motifs[fichier] = []
            df = pd.read_csv(path_motifs+fichier, skiprows=1, names=["motifs", "score"])
            for motif in df["motifs"]:
                dict_motifs[fichier].append(motif)
    return dict_motifs
            
# def build_index_motif(file, motif):
#     corpus_grew = Corpus(file)
#     request = read_req(motif)
#     param_viz="lemma"
#     index_motif= index(corpus_grew,request,param_viz)
#     # print(index)
#     return index_motif

def build_dict_index_motif_faster(file,motif):
    corpus_grew=Corpus(file)
    dict_index_motif = Counter()
    req=read_req(motif)
    request = Request(req)
    for i in range(motif.count('{')):
        dict_index_motif += Counter(corpus_grew.count(request, clustering_parameter=[f"X{i+1}.lemma"]))
    return dict_index_motif

# def construire_dict_contenu_motif(path_corpus, liste_fichiers, motif):
#     dict_k_contenu_motifs = Counter()
#     taille_t_fenetre = 0
#     for file in liste_fichiers:
#         if file!=".DS_Store":
#             index_motif = build_index_motif(path_corpus+file+"/"+file, motif)
#             for occurrence in index_motif:
#                 print(motif + ":" + str(occurrence))
#                 for lemma_occ in occurrence:
#                     dict_k_contenu_motifs[lemma_occ]+=1
#                     taille_t_fenetre +=1 
#     return dict_k_contenu_motifs, taille_t_fenetre

def construire_dict_contenu_motif_faster(path_corpus, motif):
    dict_k_contenu_motifs=Counter()
    taille_t_fenetre = 0
    for file in os.listdir(path_corpus):
        if file!=".DS_Store":
            dict_index_motif = build_dict_index_motif_faster(path_corpus+file, motif)
            taille_t_fenetre += sum(dict_index_motif.values())
            for lemma in dict_index_motif.keys():
                dict_k_contenu_motifs[lemma]+= dict_index_motif[lemma]
    return dict_k_contenu_motifs, taille_t_fenetre
    
def indice_out(dict_k_contenu_motifs, taille_t_fenetre, index_corpus,specificite_py):
    dict_indice = {}
    for lemma in dict_k_contenu_motifs.keys():
        dict_indice[lemma] = {}
        k = dict_k_contenu_motifs[lemma]
        t = taille_t_fenetre
        f = index_corpus["index_général"][lemma]
        T = index_corpus["index_général"]["taille_index_fichier"]
        dict_indice[lemma]["k"]=k
        dict_indice[lemma]["f"]=f
        dict_indice[lemma]["t"]=t
        dict_indice[lemma]["T"]=T
        if specificite_py==True:
            indice = tools.indice_specificite(k,f,t,T)[0]
            M = tools.indice_specificite(k,f,t,T)[1]
            dict_indice[lemma]["indice"] = indice
            dict_indice[lemma]["M"] = M
    return dict_indice

def sorties(dict_indice, cluster, motif): 
    df = pd.DataFrame.from_dict(dict_indice, orient='index').reset_index()
    df.columns = ["lemma", "k", "f", "t", "T"]
    if specificites_py==True:
        df_sorted = df.sort_values(by="indice", ascending=False)
        df.columns = ["lemma", "k", "f", "t", "T", "indice", "M"]
    df.to_csv(f"{path_motifs}${cluster[:-4]}_{motif}_specific_lemmas.tsv", sep="\t")

def main(path_corpus, path_motifs):
    liste_fichiers = os.listdir(path_corpus)
    path_merged = "./Patterns_results/R/25_AFC/motifs_cluster/merged_temp/"
    output_file = "./Patterns_results/R/25_AFC/motifs_cluster/merged_temp/merged"
    if not os.path.isdir("./Patterns_results/R/25_AFC/motifs_cluster/merged_temp"):
        os.mkdir("./Patterns_results/R/25_AFC/motifs_cluster/merged_temp")
        tools.concat_preserve_ids(path_corpus, output_file)
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
            # dict_k_contenu_motifs, taille_t_fenetre = construire_dict_contenu_motif(path_corpus, liste_fichiers, motif)
            dict_k_contenu_motifs, taille_t_fenetre = construire_dict_contenu_motif_faster(path_merged, motif)
            dict_indice = indice_out(dict_k_contenu_motifs, taille_t_fenetre, index_corpus, specificites_py)
            sorties(dict_indice, cluster, motif)
            
            elapsed = time.time()-start_it
            iteration_actuelle+=1
            avg_time = elapsed / iteration_actuelle
            temps_restant=(total_it-iteration_actuelle)*avg_time
            print(f"  ⏱ Temps estimé restant : {temps_restant/60:.1f} minutes ({temps_restant:.1f} s)")

specificites_py = False

path_corpus="./Data/Textes_tagged_stanza/" 
# motif = '{pos_"ADJ"} {pos_"ADP"} {pos_"DET"} {pos_"NOUN"}'

path_motifs = "./Patterns_results/R/25_AFC/motifs_cluster/"
main(path_corpus, path_motifs)
    