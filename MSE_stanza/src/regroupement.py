#!/usr/bin/env python
# coding: utf-8
# input : registre_1, registre_2


import os
import sys
import time
import pprint
import pickle as pk
from multiprocessing import Pool 
from multiprocessing.dummy import Pool as ThreadPool 
from mesure_S2MP import *


####################################################################
# CLUSTERING 1
####################################################################


def open_coded_emergent_patt(registre_1, registre_2):
    """
    input : str(registre_1), str(registre_2) 
    ouput : [list(motif_codes1),
             list(motif_codes2),
             list(motif_codes3),
            ...]
    do : open emergent patterns in their coded forms (ex : [[1, 2, 3], [5, 33]])
    """
    with open("./data/index/index_emergent_patt_{}_{}.pk".format(registre_1, registre_2), 'rb') as f1:
        index_motifs = pk.load(f1)
    return index_motifs


def regroupement_1(index_motifs):
    """
    input: [list(motif_codes1),
            list(motif_codes2),
            list(motif_codes3),
            ...]
    ouput: dict{index_groupe1 : [index_patt1, 
                                 index_patt2,
                                 index_patt3,
                                ...],
                index_groupe2 : [index_patt4, 
                                 index_patt7,
                                 index_patt9,
                                ...],
                ...}
    do : groups the patterns according to their similarity calculated by S2MP
    """
    processed_data = set()
    RG = dict()
    for i, patt_1 in enumerate(index_motifs):
        if i in processed_data: continue
        rg = set()
        rg.add(i)
        for ii, patt_2 in enumerate(index_motifs):
            if i == ii : continue
            if ii in processed_data: continue
            score_sim = main_simDegree(patt_1, patt_2)
            # print("Exemple motif 1 :", patt_1)
            # print("Exemple motif 2 :", patt_2)
            # print(f"Sim({i}, {ii}) = {score_sim:.4f}")  # Affiche le score avec 4 décimales
            if score_sim > 0.50:
                rg.add(ii)
                processed_data.add(ii)
        RG[i] = rg
        processed_data.add(i)
        if i % 1000 == 0:
            print("\t", i, "{}%".format(round(len(processed_data)*100/len(index_motifs), 2)) ) # print de test
    return RG


def from_index_to_motifcodes(RG, index_motifs):
    """
    input: dict{index_groupe1 : [index_patt1, 
                                 index_patt2,
                                 index_patt3,
                                ...],
                index_groupe2 : [index_patt4, 
                                 index_patt7,
                                 index_patt9,
                                ...],
                ...}
    ouput: dict{index_groupe1 : [motif_codes1, 
                                 motif_codes2,
                                 motif_codes3,
                                ...],
                index_groupe2 : [motif_codes4, 
                                 motif_codes7,
                                 motif_codes9,
                                ...],
                ...}
    do : transforms pattern indexes into coded patterns
    """
    RG_to_write = dict()
    for i, rg in enumerate(RG):
        rg_to_write = list()
        for patt in RG.get(rg):
            rg_to_write.append(index_motifs[patt])
        RG_to_write[i] = rg_to_write
    return RG_to_write


def save_pickles_results(to_save, title_file):
    """
    input: file
    ouput: bool 
    do: save the object locally
    """
    try:
        with open(title_file, "wb") as p:
            pk.dump(to_save, p)
        print("\t Results : saved")
        return True
    except:
        return False



####################################################################
# FIND CENTROIDS
####################################################################


def load_pickles(title_file):
    with open(title_file, "rb") as p:
        return pk.load(p)


def compute_mean_distance(p1, cluster):
    """
    input: 1. list(point)
           2. list(list(cluster))
    ouput: int(mean_distance)
    do: for a point p compute the mean distance 
        with all the others points in the same cluster c1
    """
    return p1, sum([1-main_simDegree(p1, p2) for p2 in cluster if p1 != p2])/len(cluster)


def compute_all_centroids(c1):
    """
    input: 1. cluster c1 for which we are looking for the centroid 
              list(list(cluster))
           2. nbr of threads for the //
              int(nbr_pool)
    ouput: list of points with their average distances 
           list(tuple(p, mean))
    do: for each point calculates the average distance 
        to all other points in c1  
    """
    # liste_centres = []
    # pool = ThreadPool(nbr_pool)
    # score_centre = pool.starmap(compute_mean_distance, [[p, c1]  for p in c1])
    # liste_centres += score_centre
    return [compute_mean_distance(p, c1)  for p in c1]



def select_centroid(liste_centres):
    """
    input: list(tuple(p, mean_distance))
    ouput: the closest point to the centroid and its score
    do: find the point of c1 with the minimum average distance 
        to the other points of c1
    """
    min_score = 1.0 
    min_p = []
    for p in liste_centres:
        p_score = p[1]
        if p_score < min_score:
            min_p = p[0]
            min_score = p_score
    return min_p, min_score


def main_centroid(i, cluster):
    """
    input: 1. index_cluster --> int(i)
           2. cluster --> list(list())
           3. nbr de pool --> int(nbr_pool)
    ouput:
    do: 
    """
    if i % 100 == 0:
        print("\t Cluster id :", i)
    return i, select_centroid(compute_all_centroids(cluster))


def get_all_centroids(title_clusters_file, nbr_pool=1):
    """
    input:
    ouput:
    do:
    """
    info_centroids = []
    loaded_clusters = load_pickles(title_clusters_file)
    # pool = ThreadPool(nbr_pool)
    with Pool(nbr_pool) as pool:
        score_centre = pool.starmap(main_centroid, 
                                    [[c, loaded_clusters.get(c)] 
                                    for c in loaded_clusters])
        info_centroids += score_centre
        return info_centroids

def main_find_centroids(c1, nbr_pools):
    """
    """
    all_distances = []
    with Pool(nbr_pools) as pool:
        score_centre = pool.starmap(compute_mean_distance, 
                                    [[p, c1] 
                                     for p in c1])
        all_distances += score_centre
        
    scores = [d[1] for d in all_distances]

    return all_distances[scores.index(min(scores))]


def split_cluster(c1):
    """
    """
    taille_c1 = len(c1)
    slice_total = 0
    slices = list()
    if taille_c1 > 500:
        while slice_total < taille_c1:
            slice_next = slice_total + 500
            slices.append(c1[slice_total:slice_next])
            slice_total = slice_next
        return slices
    else:
        return c1

def main_compute_medoids(title_clusters_file, nbr_pools):
    """
    """
    clusters = load_pickles(title_clusters_file)
    dict_out = dict()
    for id_cluster in clusters:
        print("-" * 70)
        print("\t Cluster n°", id_cluster, "/", len(clusters))
        cluster = clusters.get(id_cluster)
        # dict_out = load_pickles("./data/centroids/{}_{}_centroids_1.pk".format(registre_1, registre_2))

        if len(cluster) > 500:
            split_c = split_cluster(cluster)
            len_split_c = len(split_c)
            sub_c = []
            print("-"*15)
            print("\t Nbr de sub_c", len_split_c)
            for i, c in enumerate(split_c):
                sub_c.append(main_find_centroids(c, nbr_pools)[0])
                print("\t ",i, len_split_c)
            print("-"*15)
            print("\t Calcul du centroid final")
            centroid = main_find_centroids(sub_c, nbr_pools)
            dict_out[id_cluster] = centroid
        elif len(cluster) <= 500:
            print("-"*15)
            print("\t Calcul du centroid final")
            centroid = main_find_centroids(cluster, nbr_pools)
            dict_out[id_cluster] = centroid
    return dict_out


def save_results_centroids(all_info_centroids, title_file_centroids):
    """
    input:
    ouput:
    do:
    """
    dict_info = {f[0]:f[1] for f in all_info_centroids}
    try:
        save_pickles_results(dict_info, title_file_centroids)
        # print("Results centroids : saved")
    except:
        print("\t Results centroids : failed")
    return dict_info


####################################################################
# CLUSTERING 2
####################################################################


def sim_pt_centroids(p, index_clusters, centroids_files):
    """
    input:
    ouput:
    do:
    """
    sims = [main_simDegree(p, centroids_files.get(id_cluster)[0])
                               for id_cluster in index_clusters]
    return (p, sims.index(max(sims)))
        

def get_closest_centroid(c2, c1, index_clusters, centroids_files):
    """
    input:
    ouput:
    do:
    """
    # pool = ThreadPool(1)
    # sim_p_centroids = pool.starmap(sim_pt_centroids, 
    #                                 [[p, index_clusters, centroids_files] 
    #                                 for p in c1])
    sim_p_centroids = [sim_pt_centroids(p, index_clusters, centroids_files) 
                                        for p in c1]
    for p in sim_p_centroids:
        id_c_sim_max = p[1]
        c2[id_c_sim_max] = c2.get(id_c_sim_max, list()) + [p[0]]
    if len(c2)%25 == 0:
        print("\t Clusters : ", len(c2))
    return c2


def clustering_2(index_clusters, clusters_1, centroids_files, nbr_pool=1):
    """
    input:
    ouput:
    do:
    """
    c2 = dict()
    pool = ThreadPool(nbr_pool)
    index_c_max_sim = pool.starmap(get_closest_centroid, 
                                        [[c2,
                                            clusters_1.get(id_c), 
                                            index_clusters,
                                            centroids_files] 
                                        for id_c in index_clusters])
    return c2
    



if __name__ == "__main__":


    # title_clusters_file = "./data/results_clustering/courant_soutenu_clustering_1.pk"
    # nbr_pool = 3
    # title_file_out_centroids = "./data/centroids/{}_{}_centroids_1.pk".format(registre_1, registre_2)
    # all_info_centroids = get_all_centroids(title_clusters_file, nbr_pool)
    # save_results_centroids(all_info_centroids, title_file_out_centroids)
    # pprint.pprint(load_pickles(title_file_out_centroids))

    clusters_1 = load_pickles("./data/results_clustering/courant_soutenu_clustering_1.pk")
    centroids_files = load_pickles("./data/centroids/courant_soutenu_centroids_1.pk")
    index_clusters = list(clusters_1.keys())[:10]
    clusters_2 = clustering_2(index_clusters, clusters_1, centroids_files, 2)
    pprint.pprint(clusters_1.get(1))
    pprint.pprint(clusters_2.get(1))

    # clusters_2 = load_pickles("./data/results_clustering/courant_soutenu_clustering_2.pk")
    # pprint.pprint(clusters_2)











