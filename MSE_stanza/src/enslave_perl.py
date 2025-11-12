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
        if not line.startswith("#"):
            part = line.split("\t")
            texte = part[0][30:].strip()
            freq = int(part[1].strip())
            ligne_de_table[texte]=freq
    return ligne_de_table

def cqp_general():
    cmd = ['perl', './src/cqp_general.pl']
    result = subprocess.run(cmd, capture_output=True, text=True)
    output=result.stdout
    output_lines = output.splitlines()
    T = output_lines[4].strip()
    dictionnaire_t={}
    for line in output_lines[8:(len(output_lines)-3)]:
        part = line.split("\t")
        texte = part[0][30:].strip()
        t = int(part[1].strip())
        dictionnaire_t[texte]=t
    return T, dictionnaire_t

def cqp_index_property(property):
    script = f"./src/cqp_index_{property}.pl"
    cmd = ['perl', script]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output=result.stdout
    output_lines = output.splitlines()
    liste_property=[]
    for line in output_lines[4:(len(output_lines)-3)]:
        part = line.split("\t")
        res = part[1].strip()
        res = res.split("  ")[0]
        liste_property.append(res)
    return liste_property

def cqp_index_lemma(pos):
    query = f'A = [lemma=".*" & pos="{pos}"]'
    cmd = ['perl', './src/cqp_index_lemma.pl', query]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output=result.stdout
    output_lines = output.splitlines()
    liste_lemma=[]
    for line in output_lines[4:(len(output_lines)-3)]:
        part = line.split("\t")
        lemma = part[1].strip()
        lemma = lemma.split("  ")[0]
        liste_lemma.append(lemma)
    return  liste_lemma

def cqp_index_pos():
    cmd = ['perl', './src/cqp_index_pos.pl']
    result = subprocess.run(cmd, capture_output=True, text=True)
    output=result.stdout
    output_lines = output.splitlines()
    liste_pos=[]
    for line in output_lines[4:(len(output_lines)-3)]:
        part = line.split("\t")
        freq = part[0].strip()
        pos = part[1].strip()
        pos = pos.split("  ")[0]
        liste_pos.append(pos)
    return liste_pos