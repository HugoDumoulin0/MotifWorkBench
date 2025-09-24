#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 19 20:41:36 2025

@author: hugodumoulin
"""

import subprocess

def cqp_freq_textes(pattern):
    ligne_de_table = {}
    query = f'pattern = {pattern}'
    cmd = ['perl', './src/cqp_freq_textes.pl', query]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output=result.stdout
    output_lines = output.splitlines()
    for line in output_lines[5:(len(output_lines)-3)]:
        #est -ce que 5 est bien ok ici ??##
        print(line)
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

def cqp_index_property(property):
    script = f"./src/cqp_index_{property}.pl"
    cmd = ['perl', script]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output=result.stdout
    output_lines = output.splitlines()
    # dictionnaire_lemma={}
    liste_property=[]
    # print(T)
    for line in output_lines[4:(len(output_lines)-3)]:
        part = line.split("\t")
        # print(line)
        # freq = part[0].strip()
        res = part[1].strip()
        res = res.split("  ")[0]
        # dictionnaire_lemma[lemma]=freq
        liste_property.append(res)
    # print(dictionnaire_t)
    return liste_property

def cqp_index_lemma():
    cmd = ['perl', './src/cqp_index_lemma.pl']
    result = subprocess.run(cmd, capture_output=True, text=True)
    output=result.stdout
    output_lines = output.splitlines()
    # dictionnaire_lemma={}
    liste_lemma=[]
    # print(T)
    for line in output_lines[4:(len(output_lines)-3)]:
        part = line.split("\t")
        # print(line)
        # freq = part[0].strip()
        lemma = part[1].strip()
        lemma = lemma.split("  ")[0]
        # dictionnaire_lemma[lemma]=freq
        liste_lemma.append(lemma)
    # print(dictionnaire_t)
    return  liste_lemma

def cqp_index_pos():
    cmd = ['perl', './src/cqp_index_pos.pl']
    result = subprocess.run(cmd, capture_output=True, text=True)
    output=result.stdout
    output_lines = output.splitlines()
    # dictionnaire_pos={}
    liste_pos=[]
    # print(T)
    for line in output_lines[4:(len(output_lines)-3)]:
        part = line.split("\t")
        # print(line)
        freq = part[0].strip()
        pos = part[1].strip()
        pos = pos.split("  ")[0]

        # dictionnaire_pos[pos]=freq
        liste_pos.append(pos)
    # print(dictionnaire_t)
    return liste_pos