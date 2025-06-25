#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 19 15:30:39 2025

@author: hugodumoulin
"""
import subprocess
import os


path_registry = "./Data/cwb-corpus/registry"
trad_motif = '[pos="DET"] [pos="NOUN"] [pos="ADJ"]'

os.system(f"cqp -c")
os.system(f"set Registry {path_registry};")
os.system(f"MERGED;")

resultat = subprocess.run(f'{trad_motif}', shell=True, capture_output=True, text=True)
print(resultat.stdout)
# cqp_query = f"""
# MERGED;
# [pos="DET"] [pos="NOUN"] [pos="ADJ"];
# """
# process=subprocess.run(
#     ["cqp", "-r", registry_path],
#     input=cqp_query.encode("utf-8"),
#     stdout=subprocess.PIPE,
#     stderr=subprocess.PIPE,
#     )
# output=process.stdout.decode("utf-8")

# print(output)



# A = {trad_motif};
# group A match text_id;