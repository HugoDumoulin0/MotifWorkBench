#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 20:10:06 2025

@author: hugodumoulin
"""

from conllu import parse_incr
import sys
import os

def format_value(value):
    # Si c'est un dict (ex: misc), on le formate comme "key1=val1|key2=val2"
    if isinstance(value, dict):
        return "|".join(f"{k}={v}" for k, v in value.items())
    return str(value).replace(" ", "_") 

def transform(path_stanza, path_vrt):
    if not os.path.exists(path_vrt):
        os.mkdir(path_vrt)
        print("Transforming Conllu to VRT...")
        output_file = f"{path_vrt}merged.vrt"
        with open(output_file, "w", encoding="utf-8") as f_out:
            for file in os.listdir(path_stanza):
                print(f"Transforming Conllu to VRT : {file}")
                if file==".DS_Store": continue
                f_out.write(f'<text id="{file}">\n')
                input_file=f"{path_stanza}{file}"
                with open(input_file, "r", encoding="utf-8") as f_in:
                    sentence_id = 0            
                    for tokenlist in parse_incr(f_in):
                        sentence_id += 1
                        f_out.write(f'<s id="{sentence_id}">\n')
                        for token in tokenlist:
                            # On ignore les multi-word tokens (ID de type tuple)
                            if isinstance(token.get("id", None), tuple):
                                continue
                            values = [
                            token.get("id", "_"),
                            token.get("form", "_"),
                            token.get("lemma", "_"),
                            token.get("upostag", "_"),
                            token.get("xpostag", "_"),
                            token.get("feats", "_"),
                            token.get("head", "_"),
                            token.get("deprel", "_"),
                            token.get("deps", "_"),
                            token.get("misc", "_")
                            ]
                            formatted = [format_value(v) for v in values]
                            f_out.write("\t".join(formatted) + "\n")
                        f_out.write("</s>\n")
                f_out.write("</text>\n")
    else:
        print("VRT file already exists")


