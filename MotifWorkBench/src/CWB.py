# -*- coding: utf-8 -*-
"""
Created on Sat Apr 19 20:41:36 2025

@author: hugodumoulin
"""


import os


def main():

    if not os.path.exists("./Data/cwb-corpus/registry"):
        os.mkdir("./Data/cwb-corpus/registry")
    
    if not os.path.exists("./Data/cwb-corpus/data"):
        os.mkdir("./Data/cwb-corpus/data")
    
    if not os.path.exists(f"./Data/cwb-corpus/data/merged"):
        	os.mkdir(f"./Data/cwb-corpus/data/merged")
    
    print("CWB encoding of corpus...")
    os.system(f"cwb-encode -f ./Data/textesVRT/merged.vrt \
      -d ./Data/cwb-corpus/data/merged/ \
      -R ./Data/cwb-corpus/registry/merged \
      -c utf8 -xsB  \
      -N id \
      -P lemma -P pos -P xpos -P feats -P head -P dep -P deps -P misc \
      -P Gender -P Tense -P Number -P Case -P ner -P Person -P PronType -P Reflex -P VerbForm -P Definite -P Polarity \
      -S text:0+id -S s:0+id")
    
    print("CWB indexing of corpus...")
    os.system(f"cwb-makeall -r ./Data/cwb-corpus/registry -V MERGED")

#attention ! dans le registre les chemins vers les fichiers de données 
#seront notés avec un relative path ./Data/cwb-corpus/data/merged
#donc il faudra toujours lancer cqp depuis le même point de départ:
#exemple:
# cqp
# set Registry "./Data/cwb-corpus/registry";
# MERGED;

##requirements:
#brew install cwb
#et SURTOUT
#cpan
#install CWB::CQP
 