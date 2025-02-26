#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 12:05:05 2025

@author: hugodumoulin
"""

import grewpy
from grewpy import Corpus, Request
import os


def dump_graphique(match, liste_match, corpus, path):
    sent_id = match["sent_id"]
    print(sent_id)
    deco1 = liste_match[1]["deco"]
    graph = corpus[sent_id]
    os.makedirs(f"{path}/images", exist_ok = True)
    with open(f"{path}/images/{sent_id}.svg", 'w') as f:
            f.write (graph.to_svg(deco=deco1)) 

def index(treebank_path, req, param):
    grewpy.set_config("sud")
    corpus = Corpus(treebank_path)
    request = Request(req)
    liste_match=corpus.search(request)
    index=[]
    for match in liste_match:
        sent_id = match["sent_id"]
        liste_node=[]
        for node_number in match["matching"]["nodes"].values():
            liste_node.append(int(node_number))
        liste_node.sort()
        liste_forms = []
        for node_number in liste_node:
            liste_forms.append(corpus[sent_id].features[str(node_number)][param])
        index.append(liste_forms)
    return index


grewpy.set_config("sud") # ud or basic 

# path="/Users/hugodumoulin/Desktop/ArchivU/Travail/motifs/grewpy-tutorial/SUD_English-PUD/"
# treebank_path="/Users/hugodumoulin/Desktop/ArchivU/Travail/motifs/grewpy-tutorial/SUD_English-PUD/en_pud-sud-test.conllu"

# path="/Users/hugodumoulin/Desktop/ArchivU/Travail/motifs/out_s/MSE_stanza/Data/Textes_tagged_stanza/ISP"
conllu="./Data/Textes_tagged_stanza/ARSCAN/ARSCAN.conllu"

# corpus = Corpus(treebank_path)
# print(type(corpus))


# req1 = Request("pattern { X1 [upos=NOUN, Gender=Masc] ; X2 [Number=Sing, upos=ADJ] ; X1<X2}")
# req1 = Request('pattern { X1 [Number=Sing,upos=DET,lemma="le",Definite=Def,PronType=Art] ; X2 [Number=Sing] ; X1<X2}')
req1 = Request('pattern { X1 [upos=DET]; X2 [upos=ADJ]; X3 [upos=NOUN]; X1 < X2; X2 < X3}')
# req1 = Request('pattern { X1 [upos=PRON, Person="3", PronType=Prs] ; X2 [Person="3"]; X1 < X2}')

index(conllu, req1, param="lemma")
print(index)
# liste_match = corpus.search(req1, deco=True)

# for i in index(treebank_path, req1, "lemma"):
#     print(i)




