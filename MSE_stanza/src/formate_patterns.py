import os 
import re
import pandas as pd
import pickle as pk

def load_pk(path_pk):
    with open(path_pk, "rb") as input:
        return pk.load(input)

def dump_pk(obj_to_save, path_pk):
    with open(path_pk, "wb") as ouput:
        return pk.dump(obj_to_save, ouput)

def load_lexique(path_f="./Data/Lexiques/dico_int_to_str_all_items.pk"):
    return load_pk(path_f)


# def make_dict_int_to_str(path_input): #### Modification du script de Jade qui présente un problème ici ###
def make_dict_int_to_str(path_input="./Data/Lexiques/dico_str_to_int_all_items.pk"):
    dict_1 = load_pk(path_input)
    dict_2 = {dict_1.get(k):k for k in dict_1}
    ouput_path = "./Data/Lexiques/dico_int_to_str_all_items.pk"
    dump_pk(dict_2, ouput_path)
    return load_pk(ouput_path)

def from_int_to_str(patt, lexic_int_str):
    if type(patt) is str:
        if "[" in patt and "]" in patt:
            split_seq = patt.split("}, {")
            seq_str = ""
            for itemset in split_seq:
                split_itemset = itemset.replace("[{", "").replace("}]","").split(",")
                itemset_str = "{"+",".join([lexic_int_str.get(int(item)) for item in split_itemset])+"} "
                seq_str+=itemset_str
            return seq_str.strip()
        else:
            split_seq = patt.split("} {")
            seq_str = ""
            for itemset in split_seq:
                split_itemset = itemset.replace("{", "").replace("}","").split(",")
                itemset_str = "{"+",".join([lexic_int_str.get(int(item)) for item in split_itemset])+"} "
                seq_str+=itemset_str
            return seq_str.strip()
    if type(patt) is list:
        seq_str = ""
        for itemset in patt:
            itemset_str = "{"+",".join([lexic_int_str.get(int(item)) for item in itemset])+"} "
            seq_str+=itemset_str
        return seq_str.strip()
   
    

def from_str_to_list(patt):
    return [{int(item) 
            for item 
            in itemset.replace("{", "").replace("}","").split(",")} 
            for itemset 
            in patt.split("} {")]
 

if __name__ == "__main__":

    lexic_int_str = load_lexique()
    # print(from_int_to_str("{20,1095} {20} {11}", lexic_int_str))
    # print(from_str_to_list("{20,1095} {20} {11}"))