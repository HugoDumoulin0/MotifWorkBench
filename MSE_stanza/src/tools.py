#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 14:44:41 2025

@author: hugodumoulin
"""

import numpy as np
from scipy.stats import hypergeom
import pickle as pk


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