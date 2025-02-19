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
import regroupement
import representants
import extract_features
import stanza
from stanza.utils.conll import CoNLL


def get_nbr_seq(dmt4_files):
    with open("{}".format(dmt4_files), 'r', encoding="utf-8") as dmt4 :
        return len([line for line in dmt4.readlines() if "seqId" in line])

def get_minsup(minsup, dmt4_files):
    return round((get_nbr_seq(dmt4_files) / 100) * minsup)

if __name__ == "__main__":
    python = "python3.7"
    types_textes = [sys.argv[1], sys.argv[2]]

    #-------------------------------------------------------------------------------------------------------------------
    # Annotation des données
    #-------------------------------------------------------------------------------------------------------------------
    print("-"*75)
    print("1. Tagging data")

    print("1.1. Tagging data with Stanza: POS, lemma, UD")
    from stanza.pipeline.core import DownloadMethod
    nlp = stanza.Pipeline('fr', download_method=DownloadMethod.REUSE_RESOURCES)
        #Set language model for stanza and download models on first run only

    #----- MERGING FILES -----
    #Unlike what Talismane seems to do, Stanza does not merge the files for each corpus. We first need to do that.
    from merge_corpus import merge_texts

    input_folder = "./Data/Textes_raw"  # Folder containing text files
    output_folder = "./Data/Textes_merged"  # Folder to store merged files

    merge_texts(input_folder, output_folder, types_textes)  # Call the function

    #----- RUN STANZA ON MERGED FILES -----

    for type_texte in types_textes:                         #loop for each corpus
        print("\t Type_texte:", type_texte, "(tagging is ongoing, please wait)")#print corpus name

        rep = "./Data/Textes_merged/{}".format(type_texte)  #create path to dir based on arg
                                                                #change path to Textes_raw for non-merged files

        output_folder = "./Data/Textes_tagged_stanza/{}".format(type_texte)  # Output folder
        os.makedirs(output_folder, exist_ok=True)  # Create output folder if it doesn't exist

        for file in os.listdir(rep):                        #loop for each file in dir
            if file[0] == ".": continue                     #ignore hidden UNIX files
            file_path = os.path.join(rep, file)             #get the full path of each file

            with open(file_path, "r", encoding="utf-8") as f:                           
                text = f.read()
                output = nlp(text)                                                      #Define output as the object created by stanza

                output_file = os.path.join(output_folder, "{}.conllu".format(type_texte, file.split('.')[0]))
                                                                                        #Define export path from variables
                CoNLL.write_doc2conll(output, output_file)                              #Make stanza export each text in conllu format


    print("All texts saved in CoNLL-U format.")

    print("1.2. Tagging data with camamBERT : word pieces")

    for type_texte in types_textes:
        print("\t Type_texte:", type_texte)
        rep = "./Data/Textes_tagged_stanza/{}".format(type_texte)
        for file in os.listdir(rep):
            if file[0] == ".": continue
            tag_WP.parse_conll(os.path.join(rep,file), type_texte)

    print("Tagging with camamBERT has been performed.")

    #-------------------------------------------------------------------------------------------------------------------
    # DMT4 files
    #-------------------------------------------------------------------------------------------------------------------
    print("-"*75)
    print("2. Creating DMT4 files")

    # # types_textes = ["1984ca", "2008ca"]

    conll_dmt4.instancier_dict("./Data/Textes_tagged_WP/")
    for type_texte in types_textes:
            conll_dmt4.transform_data("./Data/Textes_tagged_WP/", type_texte)
    conll_dmt4.sort_dmtfiles()
    
    
    ##ajout au script de Jade - réunion Timothée Hugo 30-01-25 ##
    for type_texte in types_textes:
        conll_dmt4.make_DMT4_file(type_texte)
        


    # #-------------------------------------------------------------------------------------------------------------------
    # # Mining Pattern
    # #-------------------------------------------------------------------------------------------------------------------
    print("-"*75)
    print("3. Extracting freq & closed patterns")

    # # types_textes = ["1984ca", "2008ca"]

    for type_texte in types_textes:
        print("\t Type_texte:", type_texte)

        dmt4_files = "./Data/DMT4_files/DMT4_{}_files_sorted.txt".format(type_texte) #sys.argv[1]
        minsup_percent = 25
        minsup = get_minsup(float(minsup_percent), dmt4_files)
        print(f"\t Minsup {minsup_percent}% ")
        gap_min = 0
        gap_max = 0
        threads = 30

        print("\t\t Extracting freq patterns")

        file_out = "{}_{}{}_{}_freq.txt".format(minsup_percent, gap_min, gap_max,dmt4_files.split("/")[-1][:-4])

        with open("Prefixscontraint/config/Load.ini", "w", encoding="utf8") as set_up:
            set_up.write("MINSUP={}\n".format(minsup))
            set_up.write("CORPUS=../../{}\n".format(dmt4_files))
            set_up.write("THREAD={}\n".format(threads))
            set_up.write("GAPMIN={}\n".format(gap_min))
            set_up.write("GAPMAX={}\n".format(gap_max))

        os.system("bash src/execute_freq_pattern.sh {}".format(file_out))

        print("\t\t Extracting closed patterns")

        with open("BideSpanTree/bin/Load.ini", "w", encoding="utf8") as set_up:
            set_up.write("MINSUP={}\n".format(minsup))
            set_up.write("CORPUS=../../{}\n".format(dmt4_files))
            set_up.write("THREAD=1\n")
            set_up.write("GAPMIN={}\n".format(0))
            set_up.write("GAPMAX={}\n".format(0))

        os.system("bash src/execute_closed_pattern.sh {}".format(file_out.replace("freq", "closed")))

    #-------------------------------------------------------------------------------------------------------------------
    # Compute Emergent Pattern
    #-------------------------------------------------------------------------------------------------------------------
    print("-"*75)
    print("4. Extracting emergent patterns")

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

    print("4.3. Computing sequentiel emergent patterns")
    for type_1 in types_textes:
        for type_2 in types_textes:
            if type_1 == type_2: continue
            print("\t{} x {} ".format(type_1, type_2))
            compute_emergent_sequential_patterns.compute_GR(type_1, type_2)


    # #-------------------------------------------------------------------------------------------------------------------
    # # Clustering Emergent Pattern
    # #-------------------------------------------------------------------------------------------------------------------

    # print("-"*75)
    # print("5. Clustering emergent patterns")

    # ###adaptation du script de Jade

    # # type_1, type_2, nbr_pool = sys.argv[1], sys.argv[2], int(sys.argv[3])
    # type_1 = types_textes[0]
    # type_2 = types_textes[1]
    # nbr_pool=2

    # ###

    # emergent_patt = formate_patterns.load_pk("./Patterns_results/Emergent/1_00_{}_{}.pk".format(type_1, type_2))
    # index_motifs = [patt_info[0] for patt_info in list(emergent_patt.values()) if patt_info[2] >=1]

    # print("\t Type texte 1 :", type_1)
    # print("\t Type texte 2 :", type_2)
    # print("\t Nbr emergent patterns : ", len(index_motifs))

    # print("5.1. Clustering 1 : 1/6")

    # clustering_index_1 = regroupement.regroupement_1(index_motifs)
    # print("\t Nbr clusters : ", len(clustering_index_1))

    # clustering_motifcodes_1 = regroupement.from_index_to_motifcodes(clustering_index_1, index_motifs)
    # title_file_results_1 = "./Clustering_results/Clusters/{}_{}_clustering_1.pk".format(type_1, type_2)

    # regroupement.save_pickles_results(clustering_motifcodes_1, title_file_results_1)

    # print("5.2. Centroids 1 : 2/6")

    # compute_all_centroids = regroupement.main_compute_medoids(title_file_results_1, nbr_pool)
    # title_file_out_centroids_1 = "./Clustering_results/Medoids/{}_{}_medoids_1.pk".format(type_1, type_2)
    # regroupement.save_pickles_results(compute_all_centroids, title_file_out_centroids_1)

    # print("5.3. Clustering 2 : 3/6")

    # clusters_1 = regroupement.load_pickles(title_file_results_1)
    # centroids_files = regroupement.load_pickles(title_file_out_centroids_1)
    # print("\t Nbr clusters : ", len(centroids_files))

    # index_clusters = list(clusters_1.keys())
    # clusters_2 = regroupement.clustering_2(index_clusters, clusters_1, centroids_files, nbr_pool)

    # title_file_results_2 = "./Clustering_results/Clusters/{}_{}_clustering_2.pk".format(type_1, type_2)
    # regroupement.save_pickles_results(clusters_2, title_file_results_2)

    # print("5.4. Centroids 2 : 4/6")

    # compute_all_centroids_2 = regroupement.main_compute_medoids(title_file_results_2, nbr_pool)
    # title_file_out_centroids_2 = "./Clustering_results/Medoids/{}_{}_medoids_2.pk".format(type_1, type_2)
    # regroupement.save_pickles_results(compute_all_centroids_2, title_file_out_centroids_2)

    # print("5.5. Clustering 3 : 5/6")

    # clusters_2 = regroupement.load_pickles(title_file_results_2)
    # centroids_files_2 = regroupement.load_pickles(title_file_out_centroids_2)

    # print("\t Nbr clusters : ", len(centroids_files_2))

    # index_clusters = list(clusters_2.keys())
    # clusters_3 = regroupement.clustering_2(index_clusters, clusters_2, centroids_files_2, nbr_pool)

    # title_file_results_3 = "./Clustering_results/Clusters/{}_{}_clustering_3.pk".format(type_1, type_2)
    # regroupement.save_pickles_results(clusters_3, title_file_results_3)

    # print("5.6. Centroids 3 : 6/6")

    # compute_all_centroids_3 = regroupement.main_compute_medoids(title_file_results_3, nbr_pool)

    # title_file_out_centroids_3 = "./Clustering_results/Medoids/{}_{}_medoids_3.pk".format(type_1, type_2)
    # regroupement.save_pickles_results(compute_all_centroids_3, title_file_out_centroids_3)

    # #-------------------------------------------------------------------------------------------------------------------
    # # Extracting Representant Patterns
    # #-------------------------------------------------------------------------------------------------------------------

    # print("-"*75)
    # print("6. Extracting Representant Patterns")

    # print("6.1. Computing Representant Patterns")


    # ###adaptation du script de Jade

    # # type_1, type_2, nbr_pool = sys.argv[1], sys.argv[2], int(sys.argv[3])
    # type_1 = types_textes[0]
    # type_2 = types_textes[1]
    # nbr_pool=2

    # ###


    # title_file_clusters = "./Clustering_results/Clusters/{}_{}_clustering_3.pk".format(type_1, type_2)
    # title_file_centroids = "./Clustering_results/Medoids/{}_{}_medoids_3.pk".format(type_1, type_2)

    # clusters = formate_patterns.load_pk(title_file_clusters)
    # centroids = formate_patterns.load_pk(title_file_centroids)

    # emergent_patterns = [p
    #                     for p
    #                     in list(formate_patterns.load_pk("./Patterns_results/Emergent/1_00_{}_{}.pk".format(type_1,type_2)).values())
    #                     if p[2] >= 1]

    # dict_emergent_patt = dict()
    # for p in emergent_patterns:
    #     dict_emergent_patt[str(sorted(p[0]))] = p[3]

    # corpus_dmt4 = formate_patterns.load_pk("./Data/DMT4_files/DMT4_{}_dict_sorted.pk".format(type_1))

    # lexique = formate_patterns.load_lexique()

    # df_all_rep = representants.main_extract_all_representant(type_1,
    #                             type_2,
    #                             clusters,
    #                             centroids,
    #                             dict_emergent_patt,
    #                             corpus_dmt4,
    #                             nbr_pool)

    # print("6.2. Selecting Representant Patterns")

    # representants.main_select_representants("./Representants_results/{}_{}_representants.pk".format(type_1,type_2))

    # #-------------------------------------------------------------------------------------------------------------------
    # # Random Forest
    # #-------------------------------------------------------------------------------------------------------------------

    # # print("-"*75)
    # # print("7. RandomForest : evaluate pattern quality as features as learning descriptors")



    # # type_1, type_2 = sys.argv[1], sys.argv[2]

    # # types_paires = [("journalistique", "encyclopedique"),
    # #                 ("fiction", "journalistique"),
    # #                 ("encyclopedique", "fiction")]

    # # list_representants = ["medoids",
    # #                     "itemset",
    # #                     "item",
    # #                     "itemset*GR",
    # #                     "item*GR",
    # #                     "itemset*recouvrement",
    # #                     "item*recouvrement"]

    # # print("7.1 : Extracting features from Representant Patterns")

    # # for ip, paire in enumerate(types_paires):
    # #     type_1, type_2 = paire[0], paire[1]
    # #     if type_1 != "fiction":continue
    # #     if type_2 != "journalistique": continue
    # #     print("7.1.{} : {} vs. {}".format(ip, type_1, type_2))
    # #     for i, representant in enumerate(list_representants):
    # #         print("\t Representant : {}".format(representant))
    # #         patt_search, GR, type_tag, DMT4_1, DMT4_2, all_texts = extract_features.select_data(type_1, type_2, representant)
    # #         matrice_features = extract_features.main_extract_features(patt_search, GR, type_tag, DMT4_1, DMT4_2, all_texts)
    # #         extract_features.save_matrice_features(matrice_features, "./Data/Features/{}_{}_{}/features_{}_{}_{}".format(type_1,
    # #                                                                                                                     type_2,
    # #                                                                                                                     representant,
    # #                                                                                                                     type_1,
    # #                                                                                                                     type_2,
    # #                                                                                                                     representant))

    # # print("7.2 : RandomForest all features from Representant Patterns")
