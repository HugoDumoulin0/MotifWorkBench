#!/usr/bin/python
# coding: utf8
"""
input : 1. nbr_items [1-9]
            ex : 4 pour token, lemme, pos, syntaxe
        2. len_slice
            ex : 1000 pour le nbr de seq que lon veut par dmtfile
do : transforme un fichier conll en fichier dmt4
     fait plusieurs tirages avec une permutation à chaque fois
ouput : des fichiers dmt4 ecrits en local et leur samples dans les deux reps :
            1. 1_data/3_dmt4_files/
            2. 1_data/3_dmt4_files_samples/
"""
import os
import re
import sys
import pandas as pd
import pickle
import formate_patterns


def save_dict(dict):
    """
    input : dict(mot:int)
            ex : {'foulard': 3692, 'simple': 3693, 'intégral': 3694}
    do : save dict local in pickle format and txt format
    ouput : bool (ok|ko)
    """
    if not os.path.exists("./Data/Lexiques"):
        os.mkdir("./Data/Lexiques")
    try:
        pickle.dump(dict, open("Data/Lexiques/dico_str_to_int_all_items.pk", "wb"))
        df = pd.DataFrame.from_dict(dict, orient="index")
        df.to_csv("Data/Lexiques/dico_str_to_int_all_items.tsv", sep="\t", encoding="utf-8")
        return df
    except:
        return False


def instancier_dict(rep="1_data/0_tagged_annotated_corpus/"):
    """
    input: dir where are all the parsed files
    do : 1. make a dict ex : {'foulard': 3692, 'simple': 3693, 'intégral': 3694}
         2. save dict local in pickle format and txt format
            ex : data/Lexiques/dico_str_to_int_all_items.p
    ouput : bool (ok|ko)
    """
    dico_str_to_int = dict()
    i = 1
    for file_conll in os.listdir(rep):
        if file_conll[0]==".": continue
        # print(file_conll)
        with open(os.path.join(rep,file_conll), "r+", encoding="utf-8", errors='ignore') as conll_in :
            conll_f = conll_in.read()
            conll = [el for el in conll_f.split("\n") if el != '']
            for line in conll:
                if not line.startswith('#'):
                    tokens = line.split("\t")[1:]
                    form = 'form_"{}"'.format(tokens[0])
                    lemma = 'lemma_"{}"'.format(tokens[1])
                    pos = 'pos_"{}"'.format(tokens[2])
                    dep = 'dep_"{}"'.format(tokens[6])
                    all_feats = tokens[4].split("|")
                    formate_feats = list()
                    for f in all_feats:
                        if f != "":
                            formate_feats.append("feats_{}".format(f))
                    tags = [form, lemma, pos] + formate_feats + [dep] + tokens[9:]
                    for tag in tags:
                        if tag not in dico_str_to_int:
                            dico_str_to_int[tag] = i
                            i = i+1
    return save_dict(dico_str_to_int)


def sort_itemset_in_sequence_DMT4_file(DMT4_file):
    """
    input : dmt file
    ouput : dmt file sorted
    """
    DMT4_file_opened = open(DMT4_file).read()
    liste_sequences = [el for el in re.split("seqId [0-9]+\n", DMT4_file_opened) if el != ""]
    liste_itemsets = [sequence.split("\n") for sequence in liste_sequences]
    with open('{}_sorted.txt'.format(DMT4_file[:-4]), "w+", encoding="utf-8") as file_out :
        index_seq = 1
        for sequence in liste_itemsets :
            file_out.write("seqId {}\n".format(index_seq))
            liste_ephemere = []
            dico_ephemere = {}
            i = 1
            for el in sequence :
                if el == "" : continue
                element = el.split(" ")
                item = int(element[1])
                index = int(element[0])
                if index not in dico_ephemere :
                    dico_ephemere[index] = [item]
                else :
                    dico_ephemere.get(index).append(item)
                    dico_ephemere[index] = sorted(dico_ephemere.get(index))
            for itemset in dico_ephemere :
                file = [file_out.write(str(itemset)+" "+str(el)+"\n") for el in dico_ephemere.get(itemset)]
            index_seq += 1
    return "{} : Sorted".format(DMT4_file[:-4])


def transform_data(rep, type_texte, Form, Lemma, Pos, Dep, Feats):
    """
    input : 1. nbr d'items par itemset,
                ex : 4
            2. repertoire ou sont les fichiers parses format conll
                ex : "1_data/0_tagged_annotated_corpus/"
    do : transforme les fichiers conll en fichiers dmt4 avec le lexic tranforme en entiers
    output : bool (ok|ko)
    """
    dict_lexic = pickle.load(open("Data/Lexiques/dico_str_to_int_all_items.pk","rb"))
    index_seq = 1
    # print(os.listdir(rep))
    for i, file_conll in enumerate(os.listdir(rep)):
        # print(i, file_conll)
        if type_texte not in file_conll: continue
        # print(i) # print de test
        with open(os.path.join(rep,file_conll), "r+", encoding="utf-8", errors='ignore') as conll :
            with open("Data/DMT4_files/DMT4_{}_files.txt".format(file_conll.split("_")[0]), "a", encoding="utf-8") as file_dmt4 :
                conll = [el for el in conll.read().split("\n") if el != '']
                # print(conll.readlines())
                for token in conll:
                    if not token.startswith("#"):
                        seg_token_parsed = token.split("\t")
                        # print(seg_token_parsed)
                        nbr_token = seg_token_parsed[0]
                        if nbr_token == "1":
                            file_dmt4.write("seqId {}\n".format(index_seq))
                            index_seq += 1
                            index_itemset = 1
    
                        list_token = list()
                        if Form==True:
                            form = 'form_"{}"'.format(seg_token_parsed[1])
                            form=[form]
                        else:
                            form=[]
                        if Lemma==True:
                            lemma = 'lemma_"{}"'.format(seg_token_parsed[2])
                            lemma=[lemma]
                        else:
                            lemma=[]
                        if Pos==True:
                            pos = 'pos_"{}"'.format(seg_token_parsed[3])
                            pos=[pos]
                        else:
                            pos=[]
                        if Dep==True:
                            dep = 'dep_"{}"'.format(seg_token_parsed[7])
                            dep=[dep]
                        else:
                            dep=[]
                        if Feats==True:
                            all_feats = seg_token_parsed[5].split("|")
                            formate_feats = list()
                            for f in all_feats:
                                if f != "":
                                    formate_feats.append("feats_{}".format(f))
                        else:
                            formate_feats=[]
                        list_token = form + lemma + pos + formate_feats + dep + seg_token_parsed[10:]
                        for tag in list_token:
                            index_item = dict_lexic.get(tag)
                            file_dmt4.write("{} {}\n".format(index_itemset,index_item))
                        index_itemset += 1
        # print(f"dmt4 done : {type_texte}")
    return True


def sort_dmtfiles(rep_dmtfiles="Data/DMT4_files/"):
    """
    input : repertoire ou se trouvent les fichiers dmtfiles
    do : trie les items dans l'ordre croissant
    ouput : bool (ok|ko)
    """
    for file in os.listdir(rep_dmtfiles):
        # print(f'listdir(rep_dmtfiles) : {file}')
        if file[0]==".":continue
         # print de test
        try:
            sort_itemset_in_sequence_DMT4_file(os.path.join(rep_dmtfiles, file))
        except:
            print(file)
        os.remove(os.path.join(rep_dmtfiles, file))
            
    return True

def corpus_form_dict(rep, type_texte):
    """
    """
    dict_out = dict()
    index_seq = 0
    list_form = list()
    for i, file_conll in enumerate(os.listdir(rep)):
        if type_texte not in file_conll: continue
        print(i) # print de test
        with open(os.path.join(rep,file_conll), "r+", encoding="utf-8", errors='ignore') as conll :
            conll = [el for el in conll.read().split("\n") if el != '']
            for token in conll:
                seg_token_parsed = token.split("\t")
                nbr_token = seg_token_parsed[0]
                if nbr_token == "1":
                    index_seq += 1
                    index_itemset = 1
                    list_form = list()

                list_form.append(seg_token_parsed[1])

                index_itemset += 1
                dict_out[index_seq] = " ".join(list_form)
    return dict_out

def make_DMT4_file(type_texte):
    """
    input:
    ouput:
    do:
    """
    dmt4_txt =  re.split(r'seqId [0-9]*', open("./Data/DMT4_files/DMT4_{}_files_sorted.txt".format(type_texte)).read())
    dict_dmt4 = dict()
    for i, seq in enumerate(dmt4_txt):
        if seq == "": continue
        split_seq = seq.split("\n")
        dict_seq = dict()
        for itemset in split_seq:
            if itemset == '': continue
            split_itemset = itemset.split(" ")
            id_itemset, item = int(split_itemset[0]), int(split_itemset[1])
            dict_seq[id_itemset] = dict_seq.get(id_itemset, []) + [item]
        dict_dmt4[i] = {v:set(dict_seq.get(v)) for v in dict_seq}
    formate_patterns.dump_pk(dict_dmt4, "./Data/DMT4_files/DMT4_{}_dict_sorted.pk".format(type_texte))
    return dict_dmt4


