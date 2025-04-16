#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 19:10:29 2025

@author: hugodumoulin
"""

from collections import Counter
from grewpy import Corpus, Request
import grew
import re
import os
import pandas as pd
import tools 


def merge_dicts(list_dict):
    resultat = Counter()
    for dico in list_dict:
        for cle, valeur in dico.items():
            resultat[cle] += valeur
    return resultat

def index_frequence_lemmes(liste_fichiers):
    index = {}
    for fichier in liste_fichiers:
        index[fichier] = Counter()
        path = f'./Data/Textes_tagged_stanza/{fichier}/{fichier}'
        with open(path, 'r', encoding='utf-8') as file:
            for ligne in file:
                # Ignorer les lignes vides et celles qui commencent par un #
                if ligne.strip() == '' or ligne.startswith('#'):
                    continue
                # Découper la ligne par tabulation (colonnes)
                colonnes = ligne.split('\t')
                if len(colonnes) > 1:
                    lemme = colonnes[2]
                    # print(lemme)
                    index[fichier][lemme] += 1
                    index[fichier]["taille_index_fichier"] += 1
    index["index_général"] = merge_dicts([dico for dico in index.values()])
    return index

def specif_index(index, liste_fichiers):
    index_specificite = Counter()
    for fichier in liste_fichiers:
        index_specificite[fichier] = Counter()
        for lemme in index[fichier]:
            k = index[fichier][lemme]
            f = index["index_général"][lemme]
            t = index[fichier]["taille_index_fichier"]
            T = index["index_général"]["taille_index_fichier"]
            indice, M = tools.indice_specificite(k, f, t, T)
            index_specificite[fichier][lemme] = indice
            print(fichier, lemme, indice)
    return index_specificite, T

def filter_vocab_specific(index, index_specificite):
    index_specificites_filtered = Counter()
    index_filtered = Counter()
    for fichier in index_specificite:
        index_specificites_filtered[fichier] = {key: value for key, value in index_specificite[fichier].items() if value > 2}
        index_filtered[fichier] = {key: index[fichier][key] for key, value in index_specificite[fichier].items() if value > 2}
    return index_filtered, index_specificites_filtered

def build_index_filtered(liste_fichiers):
    index = index_frequence_lemmes(liste_fichiers)
    index_specificite, T = specif_index(index, liste_fichiers)
    index_filtered = filter_vocab_specific(index, index_specificite)[0]
    return index_filtered, T

def dump_vocab_specific(index_specificities_filtered):
    if not os.path.exists("./Patterns_results/Specifs"):
        os.makedirs("./Patterns_results/Specifs")
    for fichier in index_specificities_filtered:
        file_out = "./Patterns_results/Specifs/_vocab_specifique_{}.pk".format(fichier)
        tools.save_pickles_results(index_specificities_filtered[fichier], file_out)
        df = pd.DataFrame.from_dict(index_specificities_filtered, orient="index", columns=["lemma", "indice"])
        df.to_csv(file_out.replace("pk", "tsv"), sep="\t", encoding="utf-8")

def association_req_vocab_specific(req, index_filtered, cible, T):
    treebank_path=f"./Data/Textes_tagged_stanza/{cible}/{cible}.conllu"
    index_req = grew.index(treebank_path, req, "lemma")
    f = sum(index_filtered[cible].values())
    k = 0
    t = 0
    for occ in index_req:
        for lemme in occ:
            if lemme in index_filtered[cible].keys():
                k += 1
            t += 1
    indice_association, M = tools.indice_specificite(k, f, t, T)
    return indice_association


    

# path = "/Users/hugodumoulin/Desktop/ArchivU/Travail/motifs/MSE_stanza_specifs_rapports_Specifs/Data/Textes_tagged_stanza/CDPC/CDPC.conllu"
# req = "{feats_Gender=Masc} {feats_Gender=Masc} {feats_Gender=Fem}"
# sortie = grew.read_req(req)
# indexx = grew.index(path, sortie, "form")
# for i in indexx:
#     print(i)
    
# liste_fichiers = ["MODYCO", "ISP"]
# cible = "ISP"


# # req = Request('pattern { X1 [upos=DET]; X2 [upos=ADJ]; X3 [upos=NOUN]; X1 < X2; X2 < X3}')
# req = Request('pattern { X1 [upos=PRON, Person="3", PronType=Prs] ; X2 [Person="3"]; X1 < X2}')

# print(indice)

# for fichier in liste_fichiers:
#     compteur = extraire_frequence_lemmes(fichier)

# Afficher les lemmes et leurs fréquences
# for lemme, freq in frequences.most_common():
#     print(f"{lemme}: {freq}")
