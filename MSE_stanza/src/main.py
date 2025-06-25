#!/usr/bin/python3
# -*- coding:utf-8 -*-
import os
import re
import sys
from pprint import pprint
import numpy as np
import formate_patterns
import tag_WP
import conll_dmt4
import compute_emergent_sequential_patterns
# import compute_specifs_noZero
import compute_CQP

import regroupement
import representants
import extract_features
import stanza
from stanza.utils.conll import CoNLL
import time
import shutil
from config import *
import subprocess
import tools
import conllu2vrt
import classifiers
import enslave_perl


def get_nbr_seq(dmt4_files):
    with open("{}".format(dmt4_files), 'r', encoding="utf-8") as dmt4 :
        return len([line for line in dmt4.readlines() if "seqId" in line])

def get_minsup(minsup, dmt4_files):
    return round((get_nbr_seq(dmt4_files) / 100) * minsup)


if __name__ == "__main__":
    python = "python3.7"
    
    
    types_textes = os.listdir("./Data/Textes_raw")
    if ".DS_Store" in types_textes:
        types_textes.remove(".DS_Store")
        
        
        
    if only_clustering==False:
    #-------------------------------------------------------------------------------------------------------------------
    # Annotation des données
    #-------------------------------------------------------------------------------------------------------------------
        print("-"*75)
        print("1. Tagging data")

        print("1.1. Tagging data with Stanza: POS, lemma, UD")
            #Set language model for stanza and download models on first run only
        from stanza.pipeline.core import DownloadMethod

        #----- RUN STANZA ON FILES -----

        from replace_underscore import replace_underscore_in_conllu #Import function to replace underscores

        #Check if tagged files exists to speed up process
        start_time = time.time()
            
        if download:
                print("Téléchargement du modèle français Stanza...")
                stanza.download('fr')
        else:
            print("Modèle français Stanza déjà présent, pas de téléchargement.")
        nlp = stanza.Pipeline('fr', download_method=DownloadMethod.REUSE_RESOURCES, use_gpu=False)
        for type_texte in types_textes:
            print("\t Stanza: checking if tagged files already exists")
            output_folder = "./Data/Textes_tagged_stanza/{}".format(type_texte)
            # print(output_folder)
    
            if os.path.exists(output_folder):  # Check if the file exists
                print(f"\t Stanza: file {output_folder} already exists. Delete it to perform tagging again.")
            else:
                print(f"\t Stanza: file {output_folder} does not exist. Proceeds with tagging.")
            # for type_texte in types_textes: 
                output_folder = "./Data/Textes_tagged_stanza/{}".format(type_texte)
                rep = "./Data/Textes_raw/{}".format(type_texte)
                os.makedirs(output_folder, exist_ok=True)  # Create output folder if it doesn't exist
    
                for file in os.listdir(rep):                        #loop for each file in dir
                    if file[0] == ".": continue                     #ignore hidden UNIX files
                    file_path = os.path.join(rep, file)             #get the full path of each file
    
                    with open(file_path, "r", encoding="utf-8") as f:
                            text = f.read()
                            output = nlp(text)                          #Define output as the object created by stanza
                            # output_file = os.path.join(output_folder, "{}.conllu".format(type_texte, file.split('.')[0])) #Define export path from variables
                            output_file = os.path.join(output_folder, "{}".format(type_texte, file.split('.')[0])) #Define export path from variables
                            CoNLL.write_doc2conll(output, output_file)  #Make stanza export each text in conllu format
                            print("\t", type_texte, "has been tagged and saved:", output_file)
        end_time=time.time()
        time_tag = end_time - start_time 
        
        # if shortcut_underscore_fix==False:
        ##underscore fix 
        if  not os.path.exists("./Data/underscore_fix"):
            os.mkdir("./Data/underscore_fix")
        for type_texte in types_textes:
            output_folder = "./Data/underscore_fix/{}".format(type_texte)
            if  os.path.exists(output_folder):
                # shutil.rmtree("./Data/underscore_fix")
                print(f"\t Underscore_fix file already exists. Delete it to perform underscore_fixing again.")
            else:
                os.mkdir(f"./Data/underscore_fix/{type_texte}")
                source = f"./Data/Textes_tagged_stanza/{type_texte}/{type_texte}"
                destination = f"./Data/underscore_fix/{type_texte}/{type_texte}"
                shutil.copy(source,destination)
                print(f"Underscore fix : {type_texte}")
                filename = f'{type_texte}'
                underscore_folder =f"./Data/underscore_fix/{type_texte}"
                file_path = os.path.join(underscore_folder, filename)
                output_file = os.path.join(underscore_folder, f"{type_texte}") #Define export path from variables
                replace_underscore_in_conllu(output_file)   #Replace '_' in .conllu by randomint
                    

        if wordpieces == True:
            for type_texte in types_textes:
                print("\t CamamBERT/WP: Checking if tagged files already exists")
                # output_file = "./Data/Textes_tagged_WP/{0}_{0}.conllu".format(type_texte) #For some reason, files have twice type_text in name (Jade's script). I keep it.
                output_file = "./Data/Textes_tagged_WP/{0}_{0}".format(type_texte) #For some reason, files have twice type_text in name (Jade's script). I keep it.
                # print(output_file)
    
                if os.path.exists(output_file):  # Check if the file exists
                    print(f"\t CamamBERT/WP: file {output_folder} already exists. Delete it to perform WP tokenization again.")
                else:
                    print(f"\t CamamBERT/WP: file {output_folder} does not exist. Proceeds with WP tokenization.")
                    rep = "./Data/Textes_tagged_stanza/{}".format(type_texte)
                    output_file = os.path.join(output_folder, "{}.conllu".format(type_texte)) #Define export path from variables; only used for printing.
                    # output_file = os.path.join(output_folder, "{}.conllu".format(type_texte)) #Define export path from variables; only used for printing.
                    for file in os.listdir(rep):
                        if file[0] == ".": continue
                        tag_WP.parse_conll(os.path.join(rep,file), type_texte)
                        print("\t", type_texte, "has been WP-tokenized and saved:", output_file)

 
        #-------------------------------------------------------------------------------------------------------------------
        # DMT4 files
        #-------------------------------------------------------------------------------------------------------------------
        print("-"*75)
        print("2. Creating DMT4 files")
        # if shortcut_DMT4==False: #automatisé
            

            # # types_textes = ["1984ca", "2008ca"]
            
            #Avoid generating sorted_sorted file names and file not found error.
        if méthode=="corpus":
                
            if  os.path.exists("./Data/DMT4_files/"):
                    # shutil.rmtree("./Data/DMT4_files/")
                    print(f"\t DMT4_file already exists. Delete it to perform DMT4_transform again.")
                    # os.mkdir("./Data/DMT4_files/")
            else:
                os.mkdir("./Data/DMT4_files/")
                print("\t DMT4: Previous DMT4 files with same corpus have been deleted.")
                # for type_texte in types_textes:
                #     print("\t Checking if DMT4 files already exists")
                #     target = "./Data/DMT4_files/DMT4_{0}_files_sorted.txt".format(type_texte) #For some reason, files have type_text twice in name (Jade's script). I kept it (did I?).
                #     print(target)
                #     if os.path.exists(target):  # Check if the file exists
                #         os.remove(target)       # delete existing files
                #         print("\t DMT4: Previous DMT4 files with same corpus have been deleted.")
                    
            if wordpieces==True:
                conll_dmt4.instancier_dict("./Data/Textes_tagged_WP/")
                for type_texte in types_textes:
                        conll_dmt4.transform_data("./Data/Textes_tagged_WP/", type_texte, Form, Lemma, Pos, Dep, Feats)
                conll_dmt4.sort_dmtfiles()
            
                for type_texte in types_textes:
                    conll_dmt4.make_DMT4_file(type_texte)
                #This creates the missing dict_sorted.pk files. For some reason,
                #the function wasn't called in the original script.
                
        if wordpieces==False:
                if  os.path.exists("./Data/Textes_tagged_stanza_for_dmt4/"):
                    print(f"\t DMT4: textes_fixed files already exists. Delete it to perform DMT4-underscore_fix again.")
                else:
                    print(f"\t DMT4: file does not exist. Proceeds with transform.")
                    os.mkdir("./Data/Textes_tagged_stanza_for_dmt4/")
                    for type_texte in types_textes:
                        destination = "./Data/Textes_tagged_stanza_for_dmt4/"
                        # source = f"./Data/Textes_tagged_stanza/{type_texte}/{type_texte}"
                        source = f"./Data/underscore_fix/{type_texte}/{type_texte}"
                        if os.path.exists(source):
                            shutil.copy(source,destination)
                        else:
                            source = f"./Data/underscore_fix/{type_texte}/{type_texte}"
                            shutil.copy(source,destination)
                    
                ### opérations spécifiques à faire dans le cas d'une méthode de partitionnement
                if méthode=="partition":
                    liste_textes = ["merged"]
                    print("\t DMT4: checking if DMT4 file already exists")
                    if  os.path.exists("./Data/DMT4_files/"):
                        print(f"\t DMT4: file already exists. Delete it to perform DMT4-transform again.")
                    else:
                        os.mkdir("./Data/DMT4_files/")
                        print("\t DMT4: creating DMT4_file.")
    
                    # for type_texte in liste_textes:
                    #     print("\t Checking if DMT4 files already exists")
                    #     target = "./Data/DMT4_files/DMT4_{}_files_sorted.txt".format(type_texte) #For some reason, files have type_text twice in name (Jade's script). I kept it (did I?).
                    #     print(target)
                    #     if os.path.exists(target):  # Check if the file exists
                    #         os.remove(target)       # delete existing files
                        conll_dmt4.instancier_dict("./Data/Textes_tagged_stanza_for_dmt4/")
                        file_list = os.listdir("./Data/Textes_tagged_stanza_for_dmt4/")
                        # print(file_list)
                        path = "./Data/Textes_tagged_stanza_for_dmt4/"
                        tools.concat_multiple_conll(path, file_list, "merged")
                        # print(f'liste dir dans ttaggedfordmt4 : {os.listdir("./Data/Textes_tagged_stanza_for_dmt4/")}')
                        for type_texte in liste_textes:
                            # print("transform data début")
                            conll_dmt4.transform_data("./Data/Textes_tagged_stanza_for_dmt4/", type_texte, Form, Lemma, Pos, Dep, Feats)
                            # print(f"transform_data done : {type_texte}")
                        conll_dmt4.sort_dmtfiles()
                        for type_texte in liste_textes:
                            conll_dmt4.make_DMT4_file(type_texte)
                        
                else:
                    conll_dmt4.instancier_dict("./Data/Textes_tagged_stanza_for_dmt4/")
                    for type_texte in types_textes:
                        conll_dmt4.transform_data("./Data/Textes_tagged_stanza_for_dmt4/", type_texte, Form, Lemma, Pos, Dep, Feats)
                    conll_dmt4.sort_dmtfiles()
                    for type_texte in types_textes:
                        conll_dmt4.make_DMT4_file(type_texte)
                #This creates the missing dict_sorted.pk files. For some reason,
                #the function wasn't called in the original script.
        path_stanza="./Data/Textes_tagged_stanza/"
        path_vrt="./Data/textesVRT/"
        conllu2vrt.transform(path_stanza, path_vrt)
        if not os.path.exists("./Data/cwb-corpus"):
            os.mkdir("./Data/cwb-corpus")
            cwb.main()
    
        # #-------------------------------------------------------------------------------------------------------------------
        # # Mining Pattern
        # #-------------------------------------------------------------------------------------------------------------------
        print("-"*75)
        print("3. Extracting freq & closed patterns")
        start_time=time.time()
        # # types_textes = ["1984ca", "2008ca"]

        # if shortcut_extract==False:
        path_results = "./Patterns_results"
        if not os.path.exists(path_results):
                os.mkdir(path_results)
                
        path_file_closed = "./Patterns_results/Closed"
        if not os.path.exists(path_file_closed):
                os.mkdir(path_file_closed)
            
        path_file_freq = "./Patterns_results/Freq"
        if not os.path.exists(path_file_freq):
                os.mkdir(path_file_freq)
            
        if méthode=="partition":
            liste = ["merged"]
                
        else:
            liste=types_textes

                
        for minsup_percent in list_minsup_percent:
                threads = 30
                for type_texte in liste:
                    print("\t Type_texte:", type_texte)
                    if os.path.exists(f"./Patterns_results/Freq/{minsup_percent}_{gap_min}{gap_max}_DMT4_{type_texte}_files_sorted_freq.txt"):
                        print(f"\t Closed patterns file already exists. Delete it to perform extraction again.")
                    if os.path.exists(f"./Patterns_results/Closed/{minsup_percent}_{gap_min}{gap_max}_DMT4_{type_texte}_files_sorted_closed.txt"):
                        print(f"\t Closed patterns file already exists. Delete it to perform extraction again.")
                    else:
                        print("non existent previous extracted patterns files")
                        dmt4_files = "./Data/DMT4_files/DMT4_{}_files_sorted.txt".format(type_texte) #sys.argv[1]
                        minsup = get_minsup(float(minsup_percent), dmt4_files)
                        print(f"\t Minsup {minsup_percent}% ")

                
                        print("\t\t Extracting freq patterns")
                
                        file_out = "{}_{}{}_{}_freq.txt".format(minsup_percent, gap_min, gap_max,dmt4_files.split("/")[-1][:-4])
                
                        with open("Prefixscontraint/config/Load.ini", "w", encoding="utf8") as set_up:
                            set_up.write("MINSUP={}\n".format(minsup))
                            set_up.write("CORPUS=../../{}\n".format(dmt4_files))
                            set_up.write("THREAD={}\n".format(threads))
                            set_up.write("GAPMIN={}\n".format(gap_min))
                            set_up.write("GAPMAX={}\n".format(gap_max))
                            set_up.write("NB_ITEMSET_MIN=={}\n".format(nb_itemset_min))
                
                        os.system("bash src/execute_freq_pattern.sh {}".format(file_out))
                
                        print("\t\t Extracting closed patterns")
                
                        with open("BideSpanTree/bin/Load.ini", "w", encoding="utf8") as set_up:
                            set_up.write("MINSUP={}\n".format(minsup))
                            set_up.write("CORPUS=../../{}\n".format(dmt4_files))
                            set_up.write("THREAD=1\n")
                            set_up.write("GAPMIN={}\n".format(0))
                            set_up.write("GAPMAX={}\n".format(0))
                            set_up.write("NB_ITEMSET_MIN=={}\n".format(nb_itemset_min))
                
                        os.system("bash src/execute_closed_pattern.sh {}".format(file_out.replace("freq", "closed")))
        
        end_time=time.time()
        time_DMT4 = end_time - start_time
        #-------------------------------------------------------------------------------------------------------------------
        # Compute Patterns
        #-------------------------------------------------------------------------------------------------------------------
        
        print("-"*75)
        print("4. Extracting caracteristic patterns")
        
        rep_freq = "./Patterns_results/Freq/"
        rep_clos = "./Patterns_results/Closed/"
        
        print("4.1. Transform freq patterns")
        for f_freq in os.listdir(rep_freq):
            if "txt" not in f_freq: continue
            compute_emergent_sequential_patterns.from_txt_to_dict(os.path.join(rep_freq,f_freq))
        
        print("4.2. Transform closed patterns")
        for f_clos in os.listdir(rep_clos):
            if "txt" not in f_clos: continue
            compute_emergent_sequential_patterns.from_txt_to_dict(os.path.join(rep_clos,f_clos))
                
        if méthode=="corpus":
            print("4.3. Computing sequentiel emergent patterns")
            for type_1 in types_textes:
                for type_2 in types_textes:
                    if type_1 == type_2: continue
                    print("\t{} x {} ".format(type_1, type_2))
                    compute_emergent_sequential_patterns.compute_GR(type_1, type_2)
    
        #ajout d'une étape qui lance le calcul de spécificité des supports des motifs dans une partition par rapport au reste ( script compute_specifs.py )
        if méthode=="partition":
                start_time = time.time()
                if not os.path.exists("./Patterns_results/Specifs_noZero/"):
                    os.mkdir("./Patterns_results/Specifs_noZero/")
                print("-"*75)
                print("4.3 Extracting patterns in partition")
                
                #Tim, 2025-06-04
                # path_stanza="./Data/Textes_tagged_stanza/"
                if os.path.exists("./Data/underscore_fix/"): 
                    print("Using underscore_fix folder as source for VRT files")
                    path_stanza="./Data/underscore_fix/" 
                else:
                    print("Using Textes_tagged_stanza folder as source for VRT files")
                    path_stanza="./Data/Textes_tagged_stanza/"
                
                path_vrt="./Data/textesVRT/"
                conllu2vrt.transform(path_stanza, path_vrt)

                for minsup_percent in list_minsup_percent:
                    print(f"Minsup: {minsup_percent}")
                    # compute_specifs_noZero.main(types_textes,shortcut_association, shortcut_specifs,minsup_percent)
                    # if not os.path.exists(f"./Patterns_results/R/{minsup_percent}"):
                    results = compute_CQP.main(types_textes,shortcut_association, shortcut_specifs,minsup_percent, gap_min, gap_max, specifs)

                    for property in ["motifs", "lemma", "pos"]:
                        if not os.path.exists(f"./Patterns_results/Classifieurs/{minsup_percent}/{property}/"):
                            path=f"./Patterns_results/R/{minsup_percent}/{property}/"
                            if os.path.exists(path):
                                fichiers = sorted(os.listdir(path), key=lambda f: os.path.getmtime(os.path.join(path, f)),reverse=True)
                                for f in fichiers: 
                                    if f"{property}Texte" in f:
                                        results[f"{property}"]=path+f
                                        break
                    if classification:
                        for property_gen in ["20000lemma", "10000bigramslemma"]:
                            if not os.path.exists(f"./Patterns_results/Classifieurs/{property_gen}/"):
                                path=f"./Patterns_results/R/{property_gen}/"
                                if os.path.exists(path):
                                    fichiers = sorted(os.listdir(path), key=lambda f: os.path.getmtime(os.path.join(path, f)),reverse=True)
                                    for f in fichiers: 
                                        if f"{property_gen}" in f:
                                            results[f"{property_gen}"]=path+f
                                            break

                        classifiers.main(minsup_percent,results,path_target, sampling)
                # Use R to perform AFC automatically
                end_time = time.time()
                time_grew = end_time - start_time
                # subprocess.call(["Rscript", "./src/AFC.r"])

    