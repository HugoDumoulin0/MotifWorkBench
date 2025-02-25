import os 
import re
import pandas as pd
import pickle as pk
import numpy as np
import formate_patterns

def match_patt(patt_to_find, seq):
    """
    """
    matchs_patt = list()
    
    itemsets = list(seq.values())
    len_patt = len(patt_to_find)
    
    for n in range(len(seq)):
        slide = itemsets[n:n+len_patt]
        if len(slide) < len_patt: continue
        elif sum([patt_to_find[p].issubset(slide[p]) 
                for p in range(len_patt)]) == len_patt:
            matchs_patt.append(list(range(n+1, n+1+len_patt)))
    return matchs_patt


def select_data(type_1, type_2, representant):
    motifs_rep_1 = formate_patterns.load_pk("./Representants_results/{}_{}_representants.pk".format(type_1, type_2))
    patt_search_1 = motifs_rep_1["{}_index".format(representant)].values.tolist()

    motifs_rep_2 = formate_patterns.load_pk("./Representants_results/{}_{}_representants.pk".format(type_2, type_1))
    patt_search_2 = motifs_rep_2["{}_index".format(representant)].values.tolist()

    patt_search = patt_search_1 + patt_search_2

    DMT4_1 = formate_patterns.load_pk("./Data/DMT4_files/DMT4_{}_dict_sorted.pk".format(type_1))
    texts_1 = formate_patterns.load_pk("./Data/TextToKids_corpus/{}.pk".format(type_1))

    DMT4_2 = formate_patterns.load_pk("./Data/DMT4_files/DMT4_{}_dict_sorted.pk".format(type_2))
    texts_2 = formate_patterns.load_pk("./Data/TextToKids_corpus/{}.pk".format(type_2))

    all_texts = list(texts_1.values())+list(texts_2.values())
    type_tag = [1] * len(DMT4_1) + [0] * len(DMT4_2)

    return patt_search, type_tag, DMT4_1, DMT4_2, all_texts


def main_extract_features(patt_search, type_tag, DMT4_1, DMT4_2, all_texts):

    matrice_features = dict()

    for i in range(len(patt_search[:30])):
        patt_find = patt_search[i]
        print("Motif : ", i, "/",(len(patt_search)), "\t", patt_find)
        matrice_features[i] =  [len(match_patt(patt_find, DMT4_1.get(id_seq))) for id_seq in DMT4_1] + [len(match_patt(patt_find, DMT4_2.get(id_seq))) for id_seq in DMT4_2]

    df = pd.DataFrame.from_dict(matrice_features)
    df.columns = [str(p) for p in patt_search[:30]]
    df.insert(0, "Texts", all_texts)
    df.insert(1, "Etiquette", type_tag)
    return df

def save_matrice_features(matrice_features, title_out):
    formate_patterns.dump_pk(matrice_features, "{}.pk".format(title_out))
    matrice_features.to_csv("{}.tsv".format(title_out), sep="\t", encoding="utf-8")
    return "\t DataFrame : saved"


if __name__ == "__main__":
    print()