#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 19 20:41:36 2025

@author: hugodumoulin
"""

import subprocess

def cqp_motifs(motif):
    ligne_de_table = {}
    query = f'motif = {motif}'
    cmd = ['perl', './src/cqp_freq_motifs.pl', query]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output=result.stdout
    output_lines = output.splitlines()
    for line in output_lines[5:(len(output_lines)-3)]:
        # print(line)
        if not line.startswith("#"):
            part = line.split("\t")

            texte = part[0][30:].strip()
            # print(texte)
            freq = int(part[1].strip())
            # print(freq)
            ligne_de_table[texte]=freq
        
    return ligne_de_table

def cqp_general():
    cmd = ['perl', './src/cqp_general.pl']
    result = subprocess.run(cmd, capture_output=True, text=True)
    output=result.stdout
    output_lines = output.splitlines()
    T = output_lines[4].strip()
    dictionnaire_t={}
    # print(T)
    for line in output_lines[8:(len(output_lines)-3)]:
        part = line.split("\t")
        texte = part[0][30:].strip()
        t = int(part[1].strip())
        dictionnaire_t[texte]=t
    # print(dictionnaire_t)
    return T, dictionnaire_t

