#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 12:05:05 2025

@author: hugodumoulin
"""

import grewpy
from grewpy import Corpus, Request
import os
import re


def dump_graphique(match, liste_match, corpus, path):
    sent_id = match["sent_id"]
    print(sent_id)
    deco1 = liste_match[1]["deco"]
    graph = corpus[sent_id]
    os.makedirs(f"{path}/images", exist_ok = True)
    with open(f"{path}/images/{sent_id}.svg", 'w') as f:
            f.write (graph.to_svg(deco=deco1)) 

def index(corpus, req, param):
    grewpy.set_config("sud")
    request = Request(req)
    print(request)
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

def read_req(motif):
    # Expression régulière pour diviser le trigramme en n'importe quel nombre de parties
    pattern = r'\{([^}]*)\}' 
    # Trouver tous les groupes dans le trigramme
    match = re.findall(pattern, motif)
    # Si le trigramme n'a pas de nœuds, on lève une exception
    if not match:
        raise ValueError("Le ngramme n'a pas de nœuds valides.")
    # Construire la requête Grew pour chaque nœud
    req = "pattern {\n"
    # Parcourir chaque nœud et construire les nœuds avec les relations
    for i, node in enumerate(match, 1):
        # Diviser chaque nœud en ses conditions séparées par des virgules
        node_conditions = node.split(',')
        # Traiter chaque condition pour ajuster les noms et valeurs
        conditions = []
        for item in node_conditions:
            # Si la condition contient feats_, on la modifie
            if not "__" in item:
                if 'feats_' in item:
                    item = item.replace('feats_', '')
                if "_" in item:
                    item=item.replace("_", "=")
                # Si la condition concerne pos, on la transforme en upos
                if item.startswith('pos='):
                    item = 'upos=' + item.split('=')[1]
            # Ajouter à la liste des conditions modifiées
                conditions.append(item)
        # Joindre toutes les conditions modifiées pour ce nœud
        conditions_str = ", ".join(conditions)
        # Ajouter au match Grew avec un nom de nœud dynamique (X1, X2, ...)
        req += f"    X{i} [{conditions_str}];\n"
    # Ajouter la relation entre les nœuds (par exemple, X1 < X2)
    for i in range(1, len(match)):
        req += f"    X{i} < X{i+1};\n"
    req += "}"
    return req


# grewpy.set_config("sud") # ud or basic 

# path="/Users/hugodumoulin/Desktop/ArchivU/Travail/motifs/grewpy-tutorial/SUD_English-PUD/"
# treebank_path="/Users/hugodumoulin/Desktop/ArchivU/Travail/motifs/grewpy-tutorial/SUD_English-PUD/en_pud-sud-test.conllu"

# path="/Users/hugodumoulin/Desktop/ArchivU/Travail/motifs/out_s/MSE_stanza/Data/Textes_tagged_stanza/ISP"
# treebank_path="//Users/hugodumoulin/Desktop/ArchivU/Travail/motifs/out_s/MSE_stanza/Data/Textes_tagged_stanza/ISP/ISP.conllu"

# corpus = Corpus(treebank_path)
# print(type(corpus))


# req1 = Request("pattern { X1 [upos=NOUN, Gender=Masc] ; X2 [Number=Sing, upos=ADJ] ; X1<X2}")
# req1 = Request('pattern { X1 [Number=Sing,upos=DET,lemma="le",Definite=Def,PronType=Art] ; X2 [Number=Sing] ; X1<X2}')
# req1 = Request('pattern { X1 [upos=DET]; X2 [upos=ADJ]; X3 [upos=NOUN]; X1 < X2; X2 < X3}')
# req1 = Request('pattern { X1 [upos=PRON, Person="3", PronType=Prs] ; X2 [Person="3"]; X1 < X2}')

# liste_match = corpus.search(req1, deco=True)

# for i in index(treebank_path, req1, "lemma"):
#     print(i)




