#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 14:44:41 2025

@author: jademekki + hugodumoulin
"""

import numpy as np
from scipy.stats import hypergeom
import pickle as pk
import os
from conllu import parse_incr
import re
import pprint


def get_minsup(minsup, dmt4_files):
    return round((get_nbr_seq(dmt4_files) / 100) * minsup)

def indice_specificite(k,f,t,T):
    rv = hypergeom(T, f, t)
    x = np.arange(0, f+1)
    M = np.argmax(rv.pmf(x)) #valeur modale
    if k > np.argmax(rv.pmf(x)):  
        indice = -np.log10(1-rv.cdf(k))
    else:
        indice = np.log10(rv.cdf(k))
    return indice, M

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

                    
def concat_multiple_conll(path, files_list, output_file):
    with open(f'{path}{output_file}', 'w', encoding='utf-8') as out:
        for file in files_list:
            with open(f'{path}{file}', 'r', encoding='utf-8') as f:
                out.write(f.read())
                out.write('\n')
                os.remove(f'{path}{file}')
  
def unique_sentences_from_stanza(folder_path):
    all_sentences = []
    for filename in sorted(os.listdir(folder_path)):
        if filename!=".DS_Store":
            filepath = os.path.join(folder_path+"/"+filename, filename)
            prefix = os.path.splitext(filename)[0]  # nom du fichier comme préfixe
            with open(filepath, "r", encoding="utf-8") as f:
                for i, sentence in enumerate(parse_incr(f), 1):
                    sentence.metadata["sent_id"] = f"{prefix}_{i}"
                    all_sentences.append(sentence)
    return all_sentences

def concat_preserve_ids(path_input, output_file):
    sentences = unique_sentences_from_stanza(path_input)
    with open(output_file, "w", encoding="utf-8") as out_f:
        for sentence in sentences:
            out_f.write(sentence.serialize())
            out_f.write("\n")
    print("Merging done")
    
def count_tokens_in_conll(corpus_path):
    token_count = 0
    # Ouvrir le fichier CoNLL et lire ligne par ligne
    with open(corpus_path, 'r') as file:
        for line in file:
            # Ignore les lignes vides et les lignes de commentaire (en général, les lignes commencent par '#')
            if line.strip() and not line.startswith("#"):
                # Compte chaque token (chaque mot dans une ligne)
                token_count += 1
    return token_count
    
def from_pk_corpus_to_list(dmt4_corpus):
    pk_dmt4_corpus = load_pickles(dmt4_corpus)
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

def read_req_CQP(expr):
    # Remplacer les paires clé_"valeur" ou clé="valeur" dans les accolades par les conditions CQP correspondantes
    expr = re.sub(r'\{([^}]+)\}', lambda match: convert_to_cqp_condition(match.group(1)), expr)
    return expr

def convert_to_cqp_condition(group):
    conditions = []
    items = re.split(r'(?<!_)' r',(?=(?:[^"]*"[^"]*")*[^"]*$)', group)
    for condition in items:
        # Cas avec underscore : lemma_"monsieur" ou pos_"NOUN"
        if "_" in condition and "=" not in condition:
            key, value = condition.split("_", 1)
            value = value.strip('"')
        else:
            key, value = condition.split("=", 1)
            value = value.strip('"')
        
        conditions.append(f'{key}="{value}"')
    
    return "[" + " & ".join(conditions) + "]"

def save_as_txt(data, filename):
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(pprint.pformat(data, indent=4, width=120))
                print(f"\t Results : saved as {filename}")
                return True
            except Exception as e:
                print(f"\t Error saving {filename}: {e}")
                return False
            
def parse_motif_sequence(seq_str):
            import re
            motifs = re.findall(r'\{[^}]+\}', seq_str)
            return [set(map(int, motif.strip('{}').split(','))) for motif in motifs]
        
def parse_liste_motifs(liste):
            return [parse_motif_sequence(seq) for seq in liste]

