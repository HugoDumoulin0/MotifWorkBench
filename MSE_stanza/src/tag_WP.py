import os
import re
import sys
import pandas as pd
from transformers import CamembertTokenizer

tokenizer = CamembertTokenizer.from_pretrained("jplu/tf-camembert-base")

#Test function aiming to compare WP according to span. Over-generates WP files, commented for now.
#Over-generation: files with "1" and "2" in name to compare for Jade's and Hugo's methods.
# def parse_conll(path_file, type_texte):
#     file = os.path.basename(path_file)
#     with open(path_file, "r", encoding="utf-8") as input:
#         with open("./Data/Textes_tagged_WP/{}_1_{}".format(type_texte, file), "w+", encoding="utf-8") as output1:
#             with open("./Data/Textes_tagged_WP/{}_2_{}".format(type_texte, file), "w+", encoding="utf-8") as output2:
#                 conll = input.readlines()
#                 phrase = ""
#                 for line in conll:
#                     if len(line) == 1: 
#                         output2.write("\n")
#                     else:
#                         if not line.startswith("#"):  # Ignore lines that start with #            
#                             tokens = line.strip().split("\t")
#                             phrase += f"{tokens[1]} "
#                             WP2 = tokenizer.tokenize(tokens[1])
#                             for wp in WP2:
#                                 if wp != "▁":
#                                         tokens.append("wp_{}".format(wp))
#                                 output2.write("\t".join(tokens)+"\n")
#                 WP = tokenizer.tokenize(phrase)
#                 # print(WP)
#             string = ""
#             for wp in WP:
#                 string += f"{wp} "
#             output1.write(string)
    
#     return True

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

# This is not the right way to feed Camambert! It needs a list of word, not a word by word file.
# This writes WP at the end of the line in the conll. But it should have a string in input, not the conll itself.
# So: use string after # in conll-u files, match with sentence number, and split par words, and write at the end of the right lines.
# Or... We don't care.

