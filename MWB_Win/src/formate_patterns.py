"""
@author: Mekki 2022
Modified by JcharlesDS
"""

import pickle as pk
from pathlib import Path

def load_pk(path_pk):
    with open(path_pk, "rb") as input:
        return pk.load(input)

def dump_pk(obj_to_save, path_pk):
    with open(path_pk, "wb") as ouput:
        return pk.dump(obj_to_save, ouput)

def load_lexique(path_f=""):
    if not path_f:
        raise ValueError("path_f est requis pour load_lexique().")
    return load_pk(path_f)


 #### Modification du script de Jade qui présente un problème ici ###
def make_dict_int_to_str(path_input=""):
    if not path_input:
        raise ValueError("path_input est requis pour make_dict_int_to_str().")
    dict_1 = load_pk(path_input)
    dict_2 = {dict_1.get(k):k for k in dict_1}
    output_path = str(Path(path_input).with_name("dico_int_to_str_all_items.pk"))
    dump_pk(dict_2, output_path)
    return load_pk(output_path)

#---hdumoulin---#
def sorted_itemset_str(itemset, lexic_int_str):
        items_str = [lexic_int_str.get(item) for item in sorted(itemset)]
        return "{" + ",".join(items_str) + "}"
#---hdumoulin---#


def from_int_to_str(patt, lexic_int_str):
    if isinstance(patt, str):
        if "[" in patt and "]" in patt:
            split_seq = patt.split("}, {")
            seq_str = ""
            for itemset in split_seq:
                # Nettoyer l'itemset et récupérer les entiers
                clean = itemset.replace("[{", "").replace("}]", "")
                split_itemset = [int(x) for x in clean.split(",") if x.strip() != ""]
                seq_str += sorted_itemset_str(split_itemset, lexic_int_str) + " "
            return seq_str.strip()
        else:
            split_seq = patt.split("} {")
            seq_str = ""
            for itemset in split_seq:
                clean = itemset.replace("{", "").replace("}", "")
                split_itemset = [int(x) for x in clean.split(",") if x.strip() != ""]
                seq_str += sorted_itemset_str(split_itemset, lexic_int_str) + " "
            return seq_str.strip()
    elif isinstance(patt, list):
        seq_str = ""
        for itemset in patt:
            seq_str += sorted_itemset_str(itemset, lexic_int_str) + " "
        return seq_str.strip()
    

def from_str_to_list(patt):
    return [{int(item) 
            for item 
            in itemset.replace("{", "").replace("}","").split(",")} 
            for itemset 
            in patt.split("} {")]
 

if __name__ == "__main__":

    print("Utilisez load_lexique(path_f=...) avec un chemin explicite.")
