"""
Last updated on XXX

@author: Dumoulin, H & Premat, T.
Based on scripts by Jade Mekki 2022

"""


import os
import re
import sys
from pprint import pprint
import numpy as np
import formate_patterns
import conll_dmt4
import compute_emergent_sequential_patterns
import compute_CQP
import regroupement
import representants
import stanza
from stanza.utils.conll import CoNLL
import time
import shutil

import subprocess
import tools
import conllu2vrt
import enslave_perl
import cwb
import datetime
import early_selection
import pandas as pd
import execute_internal_clustering
import json
import sys
import types



if __name__ == "__main__":
    python = "python3.7"

        
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode=="auto":
        from config import *
    else:
        result = subprocess.run(["Rscript", "./src/config.R"],
                                capture_output=True,
                                text=True 
                                )
        errors = result.stderr
        if errors:
            print("Erreurs R :")
            print(errors)
            
        json_text = result.stdout.strip()
        data = json.loads(json_text)
        obj = types.SimpleNamespace(**data)

        
    #-------------------------------------------------------------------------------------------------------------------
    # Annotation des données
    #-------------------------------------------------------------------------------------------------------------------
    print("-"*75)
    print("1. Tagging data")

    print("1.1. Tagging data with Stanza: POS, lemma, UD")
    
    textes = os.listdir("./Data/Textes_raw")
    if ".DS_Store" in textes:
        textes.remove(".DS_Store")
    textes = [item[:-4] for item in textes]
        
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
        
    if not os.path.exists("./Data/Textes_tagged_stanza"):
        os.mkdir("./Data/Textes_tagged_stanza")
        
    tagging_list=[]
    tag=False
    for texte in textes:
        print("\t Stanza: checking if tagged files already exists")
        output_file = "./Data/Textes_tagged_stanza/{}.conllu".format(texte)
        if os.path.exists(output_file):  # Check if the file exists
            print(f"\t Stanza: file {output_file} already exists. Delete it to perform tagging again.")
        else:
            print(f"\t Stanza: file {output_file} does not exist. Proceeds with tagging.")
            file_path = "./Data/Textes_raw/{}.txt".format(texte)
            tagging_list.append(file_path)
            tag=True
    if tag==True:
        nlp = stanza.Pipeline('fr', download_method=DownloadMethod.REUSE_RESOURCES, use_gpu=use_gpu)
        for file_path in tagging_list:
            with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                        output = nlp(text)                          #Define output as the object created by stanza
                        CoNLL.write_doc2conll(output, output_file)  #Make stanza export each text in conllu format
                        print("\t", texte, "has been tagged and saved:", output_file)
    end_time=time.time()
    time_tag = end_time - start_time 
    
    ##underscore fix 
    if  not os.path.exists("./Data/underscore_fix"):
        os.mkdir("./Data/underscore_fix")
    for texte in textes:
        output_file = "./Data/underscore_fix/{}.conllu".format(texte)
        if  os.path.exists(output_file):
            print(f"\t Underscore_fix file already exists. Delete it to perform underscore_fixing again.")
        else:
            print(f"Underscore fix : {texte}")
            destination = "./Data/underscore_fix/"
            source = f"./Data/Textes_tagged_stanza/{texte}.conllu"
            shutil.copy(source,destination)
            replace_underscore_in_conllu(output_file)   #Replace '_' in .conllu by randomint



	#### Mekki 2022 ### (slightly adaptated)
    
    #-------------------------------------------------------------------------------------------------------------------
    # DMT4 files
    #-------------------------------------------------------------------------------------------------------------------
    print("-"*75)
    print("2. Creating DMT4 files")
            

    if  os.path.exists("./Data/Textes_tagged_stanza_for_dmt4/"):
        print(f"\t DMT4: textes_fixed files already exists. Delete it to perform DMT4-underscore_fix again.")
    else:
        print(f"\t DMT4: file does not exist. Proceeds with transform.")
        os.mkdir("./Data/Textes_tagged_stanza_for_dmt4/")
        for texte in textes:
            destination = "./Data/Textes_tagged_stanza_for_dmt4/"
            source = f"./Data/underscore_fix/{texte}.conllu"
            if os.path.exists(source):
                shutil.copy(source,destination)
            else:
                shutil.copy(source,destination)
                
    liste_textes = ["merged"]
    print("\t DMT4: checking if DMT4 file already exists")
    if  os.path.exists("./Data/DMT4_files/"):
        print(f"\t DMT4: file already exists. Delete it to perform DMT4-transform again.")
    else:
        os.mkdir("./Data/DMT4_files/")
        print("\t DMT4: creating DMT4_file.")
        conll_dmt4.instancier_dict("./Data/Textes_tagged_stanza_for_dmt4/")
        file_list = os.listdir("./Data/Textes_tagged_stanza_for_dmt4/")
        path = "./Data/Textes_tagged_stanza_for_dmt4/"
        tools.concat_multiple_conll(path, file_list, "merged")
        for texte in liste_textes:
            conll_dmt4.transform_data("./Data/Textes_tagged_stanza_for_dmt4/", texte, Form, Lemma, Pos, Dep, Feats)
        conll_dmt4.sort_dmtfiles()
        for texte in liste_textes:
            conll_dmt4.make_DMT4_file(texte)
            
   	#### END - Mekki 2022 ### (slightly adaptated)




    path_stanza="./Data/Textes_tagged_stanza/"
    path_vrt="./Data/textesVRT/"
    conllu2vrt.transform(path_stanza, path_vrt)
    if not os.path.exists("./Data/cwb-corpus"):
        os.mkdir("./Data/cwb-corpus")
        cwb.main()
        
    if earlySelection:
        print("-"*75)
        print("2.1 Early selection of lemma for mining")
        if user_input_list==False:
            liste_earlyselection_lemma = early_selection.main(seuil_early_selection, "", path_metadata, partition_cible, seuil_banalité, early_pos4lemma, filter_specifs)

            



   #### Mekki 2022 ### (slightly adapted)
   
    # #-------------------------------------------------------------------------------------------------------------------
    # # Mining Patterns
    # #-------------------------------------------------------------------------------------------------------------------
    print("-"*75)
    print("3. Extracting freq & closed patterns")
    start_time=time.time()

    path_results = "./Patterns_results"
    if not os.path.exists(path_results):
            os.mkdir(path_results)
            
    path_file_closed = "./Patterns_results/Closed"
    if not os.path.exists(path_file_closed):
            os.mkdir(path_file_closed)

    liste = ["merged"]
        
    for nb_itemset_min in list_itemset_min:
        for gap_min in list_gap_min:
            for gap_max in list_gap_max:
                for minsup_percent in list_minsup_percent:
                            if os.path.exists(f"./Patterns_results/Closed/{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}_DMT4_merged_files_sorted_closed.txt"):
                                print(f"\t Closed patterns file already exists. Delete it to perform extraction again.")
                            else:
                                print("non existent previous extracted patterns files")
                                dmt4_files = "./Data/DMT4_files/DMT4_merged_files_sorted.txt"
                                minsup = tools.get_minsup(float(minsup_percent), dmt4_files)
                                print(f"\t nb itemset min {nb_itemset_min} ")
                                print(f"\t gap min {gap_min} ")
                                print(f"\t gap max {gap_max} ")
                                print(f"\t Minsup {minsup_percent}% ")

                                file_out = "{}_{}_{}{}_{}_closed.txt".format(nb_itemset_min, minsup_percent, gap_min, gap_max,dmt4_files.split("/")[-1][:-4])

                                print("\t\t Extracting closed patterns")
                        
                                with open("BideSpanTree/bin/Load.ini", "w", encoding="utf8") as set_up:
                                    set_up.write("MINSUP={}\n".format(minsup))
                                    set_up.write("CORPUS=../../{}\n".format(dmt4_files))
                                    set_up.write("THREAD={}\n".format(threads))
                                    set_up.write("GAPMIN={}\n".format(gap_min))
                                    set_up.write("GAPMAX={}\n".format(gap_max))
                                    set_up.write("NB_ITEMSET_MIN=={}\n".format(nb_itemset_min))
                                    if earlySelection:
                                        set_up.write("OR={}\n".format(str(liste_earlyspecifs_lemma)[1:-1]))
                        
                                os.system("bash src/execute_closed_pattern.sh {}".format(file_out))
                                DMT4_clos_corpus = f"./Patterns_results/Closed/{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}_DMT4_merged_files_sorted_closed.txt"
                                with open(DMT4_clos_corpus, "r") as file:
                                    lines = file.readlines()
                                    print(f"{len(lines)} extracted closed patterns")
        end_time=time.time()
        time_DMT4 = end_time - start_time
        
    #-------------------------------------------------------------------------------------------------------------------
    # Compute Patterns
    #-------------------------------------------------------------------------------------------------------------------
    
    print("-"*75)
    print("4. Extracting caracteristic patterns")
    
    rep_clos = "./Patterns_results/Closed/"

    print("Transform closed patterns")
    for f_clos in os.listdir(rep_clos):
        if "txt" not in f_clos: continue
        compute_emergent_sequential_patterns.from_txt_to_dict(os.path.join(rep_clos,f_clos))
            
                
     # #-------------------------------------------------------------------------------------------------------------------
     # # Internal Clustering
     # #-------------------------------------------------------------------------------------------------------------------

    if internal_clustering==True:
        start_time=time.time()
        if not os.path.exists("./Clustering_results"):
            os.mkdir("./Clustering_results")
        if not os.path.exists("./Clustering_results/Clusters"):
            os.mkdir("./Clustering_results/Clusters")
        if not os.path.exists("./Clustering_results/Medoids"):
            os.mkdir("./Clustering_results/Medoids")
        nbr_pool = 10
        for nb_itemset_min in list_itemset_min:
                for gap_min in list_gap_min:
                    for gap_max in list_gap_max:
                        for minsup_percent in list_minsup_percent:
                            if not os.path.exists(f"./Clustering_results/Clusters/{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}_clustering_3.pk"):
                                execute_internal_clustering.main(nbr_pool, minsup_percent, nb_itemset_min, gap_min, gap_max)
                            else:
                                print("-"*75)
                                print("4.bis Internal clustering of closed patterns")
                                print("Clustering results already exists : delete it to perform internal clustering again")
        end_time=time.time()
        time_clustering = end_time - start_time                
                
        
   	#### END - Mekki 2022 ### (slightly adaptated)
       
       
       
       
       
    # #-------------------------------------------------------------------------------------------------------------------
    # # Statistical computing
    # #-------------------------------------------------------------------------------------------------------------------
    start_time = time.time()
    if not os.path.exists("./Patterns_results/Specifs/"):
        os.mkdir("./Patterns_results/Specifs/")
    print("-"*75)
    print("5. Statistical computing of patterns in partition")
    if not os.path.exists("./Patterns_results/R"):
        os.mkdir("./Patterns_results/R")
    df_metadata = pd.read_csv(path_metadata, sep="\t", index_col=0)
    results={}
 
    ##computing patterns###
    modif=""
    if earlySelection:
        modif=f"{seuil_early_selection}earlySelection_"
    if internal_clustering:
        modif= modif+"internal_clustering_"
    

    for metadata in list_metadata:
            for nb_itemset_min in list_itemset_min:
                    for gap_min in list_gap_min:
                        for gap_max in list_gap_max:
                            path_R=f"./Patterns_results/R/{metadata}/{modif}motifs/itemset_min{nb_itemset_min}/gap_min{gap_min}/gap_max{gap_max}/"
                            if not os.path.exists(path_R):
                                path="./Patterns_results/R/"
                                if not os.path.exists(path):
                                    os.mkdir(path)
                                path= f"./Patterns_results/R/{metadata}/"
                                if not os.path.exists(path):
                                    os.mkdir(path)
                                path= f"./Patterns_results/R/{metadata}/{modif}motifs/"
                                if not os.path.exists(path):
                                    os.mkdir(path)
                                path=f"./Patterns_results/R/{metadata}/{modif}motifs/itemset_min{nb_itemset_min}"
                                if not os.path.exists(path):
                                    os.mkdir(path)
                                path=f"./Patterns_results/R/{metadata}/{modif}motifs/itemset_min{nb_itemset_min}/gap_min{gap_min}/"
                                if not os.path.exists(path):
                                    os.mkdir(path)
                                path=f"./Patterns_results/R/{metadata}/{modif}motifs/itemset_min{nb_itemset_min}/gap_min{gap_min}/gap_max{gap_max}/"
                                if not os.path.exists(path):
                                    os.mkdir(path)
                            for minsup_percent in list_minsup_percent:
                                print(f"Minsup: {minsup_percent}")
                                path_out = f"{path_R}minsup{str(minsup_percent)}/"
                                if os.path.exists(path_out):
                                            for dir in os.listdir(path_out):
                                                print(path_out)
                                                print(f"already computed {dir}")
                                                fichiers = sorted(os.listdir(path_out+dir), key=lambda f: os.path.getmtime(os.path.join(path_out+dir, f)),reverse=True)
                                                for f in fichiers: 
                                                            if "motifsTexte_" in f:
                                                                if internal_clustering:
                                                                    if "_FUS" in f:
                                                                        results[f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"]=path_out+dir+"/"+f
                                                                    else:
                                                                        df_k=pd.read_csv(path_out+dir+"/"+f, sep="\t", index_col=0)
                                                                        df_k.to_csv(path_out+dir+"/"+f, sep="\t")
                                                                        results[f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"] = f
                                                                        lexic_int_str = formate_patterns.make_dict_int_to_str()
                                                                        df_k = compute_CQP.fusion_internal_clusters(df_k, lexic_int_str,nb_itemset_min, minsup_percent, gap_min, gap_max)
                                                                        f_fus = f[:-4]+"_FUS.tsv"
                                                                        df_k.to_csv(path_out+dir+"/"+f_fus, sep="\t")
                                                                        results[f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"] = f_fus
                                                                else:
                                                                    results[f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"]=path_out+dir+"/"+f
                                                                break
                                else:    
                                    print("computing statistics from scratch")
                                    results, path_out = compute_CQP.main(textes,minsup_percent,gap_min, gap_max, nb_itemset_min,specifs,df_metadata, modif,metadata, internal_clustering, results, path_out)
        
    ##comparison with other features###
    for metadata in list_metadata:
        print(metadata)
        if not os.path.exists(f"./Patterns_results/R/{metadata}"):
            os.mkdir(f"./Patterns_results/R/{metadata}")
            
        #pos#
        print("pos")
        if not os.path.exists(f"./Patterns_results/R/{metadata}/pos"):
            os.mkdir(f"./Patterns_results/R/{metadata}/pos")
            path_pos = f"./Patterns_results/R/{metadata}/"
            execution_time = datetime.datetime.now()
            if not metadata=="id":
                path_id = f"./Patterns_results/R/id/pos/"
                modif=""
                if os.path.exists(path_id):
                    file_out_pos, file_total, path_out, df_pos = compute_CQP.get_already_computed_df_id("pos", minsup_percent,gap_min, gap_max, nb_itemset_min, path_id, path_pos, modif)
                else:
                    file_out_pos, path_out, df_pos, file_total = compute_CQP.compute_freq_TextesPos_AFC(execution_time, path_pos)
                df_pos =  compute_CQP.textes2metadata(df_pos, df_metadata, metadata).T
            else:
                file_out_pos, path_out, df_pos, file_total = compute_CQP.compute_freq_TextesPos_AFC(execution_time, path_pos)
            df_pos.to_csv(file_out_pos, sep="\t")
            print(f"file_out_pos : {file_out_pos}")
            if mode=="server":
                subprocess.call(["Rscript", "./src/AFC.R", file_out_pos, path_out])
            df_pos=compute_CQP.add_total(df_pos)
            df_pos.to_csv(file_total, sep="\t")
            results[f"{metadata}_pos"] = file_out_pos
        else:
            print(f"already computed pos")
            doss =f"./Patterns_results/R/{metadata}/pos/"
            liste=[]
            for fichier in os.listdir(doss):
                if f"posTexte_" in fichier:
                    liste.append(doss+fichier)
            tri = sorted(liste, key=os.path.getmtime, reverse=True)
            results[f"{metadata}_pos"] = tri[0]
        
        #lemma#
        for seuil in liste_seuils_lemma:
            print(str(seuil) + "lemma" + downhill_pos4lemma)
            if not os.path.exists(f"./Patterns_results/R/{metadata}/{seuil}lemma{downhill_pos4lemma}"):
                os.mkdir(f"./Patterns_results/R/{metadata}/{seuil}lemma{downhill_pos4lemma}")
                path_lemma = f"./Patterns_results/R/{metadata}/"
                execution_time = datetime.datetime.now()
                if not metadata=="id":
                    path_id = f"./Patterns_results/R/id/{seuil}lemma{downhill_pos4lemma}/"
                    modif=""
                    if os.path.exists(path_id):
                        file_out_lemma, file_total, path_out, df_lemma = compute_CQP.get_already_computed_df_id(f"{seuil}lemma{downhill_pos4lemma}", minsup_percent,gap_min, gap_max, nb_itemset_min, path_id,path_lemma,modif)
                    else:
                        file_out_lemma, path_out, df_lemma, file_total = compute_CQP.compute_freq_TextesLemma_AFC(seuil, execution_time, path_lemma, downhill_pos4lemma)
                    df_lemma =  compute_CQP.textes2metadata(df_lemma, df_metadata, metadata).T
                else:
                    file_out_lemma, path_out, df_lemma, file_total = compute_CQP.compute_freq_TextesLemma_AFC(seuil, execution_time, path_lemma, downhill_pos4lemma)
                df_lemma.to_csv(file_out_lemma, sep="\t")
                if mode=="server":
                    subprocess.call(["Rscript", "./src/AFC.R", file_out_lemma, path_out]) 
                df_lemma=compute_CQP.add_total(df_lemma)
                df_lemma.to_csv(file_total, sep="\t")
                results[f"{metadata}_{seuil}lemma{downhill_pos4lemma}"] = file_out_lemma
            else:
                print(f"already computed {seuil}lemma{downhill_pos4lemma}")
                liste=[]
                doss =f"./Patterns_results/R/{metadata}/{seuil}lemma{downhill_pos4lemma}/"
                for fichier in os.listdir(doss):
                    if f"{seuil}lemma{downhill_pos4lemma}Texte_" in fichier:
                        liste.append(doss+fichier)
                tri = sorted(liste, key=os.path.getmtime, reverse=True)
                results[f"{metadata}_{seuil}lemma{downhill_pos4lemma}"] = tri[0]
              
        #bigrams#
        for seuil in liste_seuils_bigrams:
            print(str(seuil) + "bigrams")
            if not os.path.exists(f"./Patterns_results/R/{metadata}/{seuil}bigramslemma"):
                os.mkdir(f"./Patterns_results/R/{metadata}/{seuil}bigramslemma")
                path_big = f"./Patterns_results/R/{metadata}/"
                execution_time = datetime.datetime.now()
                if not metadata=="id":
                    path_id = f"./Patterns_results/R/id/{seuil}bigramslemma/"
                    modif=""
                    if os.path.exists(path_id):
                        file_out_bigrams, file_total, path_out, df_big = compute_CQP.get_already_computed_df_id(f"{seuil}bigramslemma", minsup_percent,gap_min, gap_max, nb_itemset_min, path_id, path_big,modif)
                    else:
                        file_out_bigrams, path_out, df_big = compute_CQP.compute_freq_Textes_BigramsLemma_noAFC(execution_time, path_big, seuil)
                    df_big =  compute_CQP.textes2metadata(df_big, df_metadata, metadata).T
                else:
                    file_out_bigrams, path_out, df_big  = compute_CQP.compute_freq_Textes_BigramsLemma_noAFC(execution_time, path_big, seuil)
                df_big.to_csv(file_out_bigrams, sep="\t")
                if mode=="server":
                    subprocess.call(["Rscript", "./src/AFC.R", file_out_bigrams, path_out])
                results[f"{metadata}_{seuil}bigramslemma"] = file_out_bigrams
            else:
                print(f"already computed {seuil}bigrams")
                doss =f"./Patterns_results/R/{metadata}/{seuil}bigramslemma/"
                liste=[]
                for fichier in os.listdir(doss):
                    if f"bigramslemmaTexte_" in fichier:
                        liste.append(doss+fichier)
                tri = sorted(liste, key=os.path.getmtime, reverse=True)
                results[f"{metadata}_{seuil}bigramslemma"] = tri[0]
            
    print(results)
        
    end_time = time.time()
    time_stats = end_time - start_time
            
    if mode=="server":
        print(f"Temps de tagging : {time_tag/60:.2f} minutes")
        print(f"Temps d'extraction des motifs : {time_DMT4/60:.2f} minutes")
        print(f"Temps de calcul statistique  : {time_stats/60:2f} minutes")
        if internal_clustering:
            print(f"Temps de calcul des clusters internal : {time_clustering/60:2f} minutes")
        
        execution_time = datetime.datetime.now()
        with open(f"./log_{execution_time}.txt", "w") as file:
            file.write(f"earlySelection={earlySelection}\n")
            file.write(f"internal_clustering={internal_clustering}\n")
            file.write(f"list_itemset_min={list_itemset_min}\n")
            file.write(f"list_gap_min={list_gap_min}\n")
            file.write(f"list_gap_max={list_gap_max}\n")
            file.write(f"list_minsup_percent={list_minsup_percent}\n")
            file.write(f"Patterns_param_form={Form}\n")
            file.write(f"Patterns_param_lemma={Lemma}\n")
            file.write(f"Patterns_param_pos={Pos}\n")
            file.write(f"Patterns_param_dep={Dep}\n")
            file.write(f"Patterns_param_feats={Feats}\n")
            file.write(f"List_metadata={list_metadata}\n")
            file.write(f"List_seuils_lemma={liste_seuils_lemma}\n")
            file.write(f"List_seuils_bigrams={liste_seuils_bigrams}\n")
            file.write("-"*75)
            file.write(f"Temps de tagging : {time_tag/60:.2f} minutes\n")
            file.write(f"Temps d'extraction des motifs : {time_DMT4/60:.2f} minutes\n")
            if internal_clustering:
                file.write(f"Temps de calcul des clusters  : {time_clustering/60:2f} minutes\n")
            file.write(f"Temps de calcul statistique  : {time_stats/60:2f} minutes\n")
            file.write("-"*75)
        
    if mode=="interface":
        json_results = json.dumps(results)
        json_file = "./temp_input.json"
    
        # Save JSON to a temporary file for the Shiny app to read
        with open(json_file, "w") as f:
            f.write(json_results)
    
        shiny_app = "./src/Shiny_CA.R"
    
        output_dir = "./Patterns_results/R/25/motifs"
        shiny_app = "./src/Shiny_CA.R"
    
        # Launch Shiny app as a detached process (do not wait)
        p = subprocess.Popen(
            ["Rscript", shiny_app, json_file],
            stdout=None,  # allow Shiny to print to terminal
            stderr=None,
            stdin=None
        )
        
        
        
        
        
