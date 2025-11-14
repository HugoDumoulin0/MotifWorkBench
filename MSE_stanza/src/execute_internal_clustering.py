#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Mekki 2022
"""

import formate_patterns
import tools
import regroupement

def main(nbr_pool, minsup_percent, nb_itemset_min, gap_min, gap_max):     
         print("-"*75)
         print("4.4 Internal clustering of closed patterns")

         ###
     
         closed_patt = formate_patterns.load_pk(f"./Patterns_results/Closed/{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}_DMT4_merged_files_sorted_closed.pk")
         liste_motifs = list(closed_patt.keys())
         index_motifs = tools.parse_liste_motifs(liste_motifs)
         

         print("\t Nbr closed patterns : ", len(index_motifs))
     
         print("Clustering 1 : 1/6")
              
         clustering_index_1 = regroupement.regroupement_1(index_motifs)
         print("\t Nbr clusters : ", len(clustering_index_1))
         
         title_file_results_1 = f"./Clustering_results/Clusters/{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}_clustering_1.pk"
         # if not os.path.exists(title_file_results_1):
         clustering_motifcodes_1 = regroupement.from_index_to_motifcodes(clustering_index_1, index_motifs)
         regroupement.save_pickles_results(clustering_motifcodes_1, title_file_results_1)
         # regroupement.save_pickles_results(clustering_motifcodes_1, title_file_results_1.replace(".pk", ".txt"))
         tools.save_as_txt(clustering_motifcodes_1, title_file_results_1.replace(".pk", ".txt"))
     
         print("Centroids 1 : 2/6")
     
         title_file_out_centroids_1 = f"./Clustering_results/Medoids/{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}_medoids_1.pk"
        # if not os.path.exists(title_file_out_centroids_1):
         compute_all_centroids = regroupement.main_compute_medoids(title_file_results_1, nbr_pool)
         regroupement.save_pickles_results(compute_all_centroids, title_file_out_centroids_1)
         # regroupement.save_pickles_results(compute_all_centroids, title_file_out_centroids_1.replace(".pk", ".txt"))
         tools.save_as_txt(compute_all_centroids, title_file_out_centroids_1.replace(".pk", ".txt"))

         print("Clustering 2 : 3/6")
     
         clusters_1 = regroupement.load_pickles(title_file_results_1)
         centroids_files = regroupement.load_pickles(title_file_out_centroids_1)
         print("\t Nbr clusters : ", len(centroids_files))
     
         index_clusters = list(clusters_1.keys())
         
         title_file_results_2 = f"./Clustering_results/Clusters/{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}_clustering_2.pk"
         # if not os.path.exists(title_file_results_2):
         clusters_2 = regroupement.clustering_2(index_clusters, clusters_1, centroids_files, nbr_pool)
         regroupement.save_pickles_results(clusters_2, title_file_results_2)
         # regroupement.save_pickles_results(clusters_2, title_file_results_2.replace(".pk", ".txt"))
         tools.save_as_txt(clusters_2, title_file_results_2.replace(".pk", ".txt"))

     
         print("Centroids 2 : 4/6")
     
         title_file_out_centroids_2 = f"./Clustering_results/Medoids/{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}_medoids_2.pk"
         # if not os.path.exists(title_file_out_centroids_2):
         compute_all_centroids_2 = regroupement.main_compute_medoids(title_file_results_2, nbr_pool)
         regroupement.save_pickles_results(compute_all_centroids_2, title_file_out_centroids_2)
         # regroupement.save_pickles_results(compute_all_centroids_2, title_file_out_centroids_2.replace(".pk", ".txt"))
         tools.save_as_txt(compute_all_centroids_2, title_file_out_centroids_2.replace(".pk", ".txt"))


         print("Clustering 3 : 5/6")
     
         clusters_2 = regroupement.load_pickles(title_file_results_2)
         centroids_files_2 = regroupement.load_pickles(title_file_out_centroids_2)
     
         print("\t Nbr clusters : ", len(centroids_files_2))
     
         title_file_results_3 = f"./Clustering_results/Clusters/{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}_clustering_3.pk"
         # if not os.path.exists(title_file_results_3):
         index_clusters = list(clusters_2.keys())
         clusters_3 = regroupement.clustering_2(index_clusters, clusters_2, centroids_files_2, nbr_pool)
         regroupement.save_pickles_results(clusters_3, title_file_results_3)
         # regroupement.save_pickles_results(clusters_3, title_file_results_3.replace(".pk",".txt"))
         tools.save_as_txt(clusters_3, title_file_results_3.replace(".pk",".txt"))

     
         print("Centroids 3 : 6/6")
         
         title_file_out_centroids_3 = f"./Clustering_results/Medoids/{nb_itemset_min}_{minsup_percent}_{gap_min}{gap_max}_medoids_3.pk"
         # if not os.path.exists(title_file_out_centroids_3):
         compute_all_centroids_3 = regroupement.main_compute_medoids(title_file_results_3, nbr_pool)
         regroupement.save_pickles_results(compute_all_centroids_3, title_file_out_centroids_3)
         # regroupement.save_pickles_results(compute_all_centroids_3, title_file_out_centroids_3.replace(".pk", ".txt"))
         tools.save_as_txt(compute_all_centroids_3, title_file_out_centroids_3.replace(".pk", ".txt"))
