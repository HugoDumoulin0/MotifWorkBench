"""
@author: Mekki 2022
"""
import os
import re
import pandas as pd
import pickle as pk
import formate_patterns

def load_df(path_df, sep="\t", encoding="utf-8"):
    return pd.read_csv(path_df, sep=sep, encoding=encoding)

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

def from_txt_to_dict(file_results):
    dict_results = dict()
    with open(file_results, "r+") as file :
        line = file.readline().strip()
        while line :
            elements_line = line.split(":")
            if len(elements_line[0].strip().split(" ")) >= 1:
                dict_results[elements_line[0].strip()] = int(elements_line[1].replace(" ",""))
            line = file.readline().strip()
    save_pickles_results(dict_results, file_results.replace("txt", "pk"))
    return True

def from_dict_to_df(path_emergent_dict):
    emergent_patt = load_pickles(path_emergent_dict)
    df = pd.DataFrame.from_dict(emergent_patt, orient="index", columns=["motifs_int", "motifs_str", "GR", "freq_1", "freq_2"])
    df_sort = df.sort_values(by="GR", ascending=False)
    df_sort.to_csv(path_emergent_dict.replace("pk", "tsv"), sep="\t", encoding="utf-8")
    return True
