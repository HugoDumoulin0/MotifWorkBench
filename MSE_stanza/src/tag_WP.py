import os
import re
import sys
import pandas as pd
from transformers import CamembertTokenizer

tokenizer = CamembertTokenizer.from_pretrained("jplu/tf-camembert-base")

def parse_conll(path_file, type_texte):
    file = os.path.basename(path_file)
    with open(path_file, "r", encoding="utf-8") as input:
        with open("./Data/Textes_tagged_WP/{}_{}".format(type_texte, file), "w+", encoding="utf-8") as output:
            conll = input.readlines()
            for line in conll:
                if len(line) == 1: 
                    output.write("\n")
                else:
                    if not line.startswith("#"):  # Ignore lines that start with #            
                        tokens = line.strip().split("\t")
                        WP = tokenizer.tokenize(tokens[1])
                        for wp in WP:
                            if wp != "▁":
                                tokens.append("wp_{}".format(wp))
                        output.write("\t".join(tokens)+"\n")
    return True

if __name__ == "__main__":
    
    type_texte = sys.argv[1]
    rep = "./Data/Textes_tagged_stanza/{}".format(type_texte)
    for file in os.listdir(rep)[:3]:
        if file[0] == ".": continue
        parse_conll(os.path.join(rep,file), type_texte)




