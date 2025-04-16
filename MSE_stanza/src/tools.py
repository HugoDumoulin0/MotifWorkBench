#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 14:44:41 2025

@author: hugodumoulin
"""

import numpy as np
from scipy.stats import hypergeom
import pickle as pk
import os
from conllu import parse_incr

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
    with open(f'{output_file}', 'w', encoding='utf-8') as out:
        for file in files_list:
            if file!=".DS_Store": 
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