#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 20:10:06 2025

@author: hugodumoulin
Modified by @JcharlesDS
"""

from conllu import Token, parse_sentences
from conllu.parser import DEFAULT_FIELDS, DEFAULT_FIELD_PARSERS, parse_line
import os


def iter_tokenlists(input_file):
    fields = DEFAULT_FIELDS
    parsers = DEFAULT_FIELD_PARSERS.copy()
    xpos_parser = parsers.get("xpos") or parsers["xpostag"]
    parsers.update(xpos=xpos_parser, xpostag=xpos_parser)
    for sentence in parse_sentences(input_file):
        tokens = []
        for line in sentence.split("\n"):
            line = line.lstrip()
            if line.startswith("# global.columns = "):
                fields = line.split("=", 1)[1].lower().split() or DEFAULT_FIELDS
            elif not line or line.startswith("#"):
                continue
            elif "\t" not in line:
                tokens.append(parse_line(line.rstrip(), fields, parsers))
            else:
                columns = line.split("\t")
                token = Token(zip(fields, columns))
                for index, field in enumerate(token):
                    if field in parsers:
                        token[field] = parsers[field](columns, index)
                tokens.append(token)
        yield tokens


def format_value(value):
    # Si c'est un dict (ex: misc), on le formate comme "key1=val1|key2=val2"
    if isinstance(value, dict):
        return "|".join(f"{k}={v}" for k, v in value.items())
    return str(value).replace(" ", "_") 

def transform(path_stanza, path_vrt):
    if not os.path.exists(path_vrt):
        os.mkdir(path_vrt)
    
    output_file = f"{path_vrt}merged.vrt"
    if os.path.exists(output_file):
        print(f"VRT file already exists: {output_file}")
        return
        
    print("Transforming Conllu to VRT...")
    with open(output_file, "w", encoding="utf-8") as f_out:
        for file in os.listdir(path_stanza):
            print(f"Transforming Conllu to VRT : {file}")
            if file==".DS_Store": continue
            f_out.write(f'<text id="{file[:-7]}">\n')
            input_file=f"{path_stanza}{file}"
            with open(input_file, "r", encoding="utf-8") as f_in:
                sentence_id = 0            
                for tokenlist in iter_tokenlists(f_in):
                    sentence_id += 1
                    f_out.write(f'<s id="{sentence_id}">\n')
                    for token in tokenlist:
                        # On ignore les multi-word tokens (ID de type tuple)
                        if isinstance(token.get("id", None), tuple):
                            continue
                        values = [token.get(field, "_") for field in DEFAULT_FIELDS]
                        formatted = [format_value(v) for v in values]
                        f_out.write("\t".join(formatted) + "\n")
                    f_out.write("</s>\n")
            f_out.write("</text>\n")


