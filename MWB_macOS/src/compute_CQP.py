#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 20 17:28:58 2025

@author: hugodumoulin
Modified by JcharlesDS
"""



import formate_patterns
import tools
import os
import pandas as pd
import datetime
import subprocess
import enslave_perl
import re
from pathlib import Path
from config import *


def is_valid_timestamp_filename(filename):
    """
    Vérifie si le nom de fichier contient un timestamp au bon format (YYYYMMDD_HHMMSS).
    Ignore les fichiers avec des timestamps contenant espaces, tirets ou points (ancien format).
    """
    # Rejeter les fichiers avec timestamp au mauvais format (espaces, tirets, points multiples)
    if re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:', filename):
        return False
    # Accepter les fichiers avec timestamp au bon format (YYYYMMDD_HHMMSS)
    if re.search(r'\d{8}_\d{6}', filename):
        return True
    return True  # Accepter les autres fichiers par défaut


def textes2metadata(df, df_target, metadata):
    df_combined = df.T
    df_target = df_target.astype(str)
    df_combined[metadata] = df_target[metadata]
    # On groupe par target et on additionne les lemmes
    df_targetXlemmes = df_combined.groupby(metadata).sum()  
    return df_targetXlemmes


def aggregate_t_by_metadata(dictionnaire_t, df_target, metadata):
    df_target = df_target.copy()
    df_target[metadata] = df_target[metadata].astype(str)
    df_target["taille"] = df_target.index.map(dictionnaire_t).fillna(0)
    return df_target.groupby(metadata)["taille"].sum().to_dict()


def add_total(df):
    df_total = df.copy()
    df_total["total"] = df.sum(axis=1)
    df_total = df_total.sort_values(by="total", ascending=False)
    return df_total


def _run_specifs_rscript(minsup_percent, execution_time, path_out, file_out, seuil="", pos=""):
    script_path = Path(__file__).resolve().parent / "compute_specifs.r"
    cmd = [
        "Rscript",
        str(script_path),
        str(minsup_percent),
        str(execution_time),
        str(path_out),
        str(file_out),
        str(seuil),
        str(pos),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Échec du calcul R des spécificités: {details or 'Rscript a retourné un code non nul.'}")


def _uses_internal_clustering(modif):
    return "internal_clustering_" in (modif or "")


def _with_fus_suffix(path):
    if path.endswith("_FUS.tsv"):
        return path
    if path.endswith(".tsv"):
        return path[:-4] + "_FUS.tsv"
    return path + "_FUS"


def _build_specifs_output_dir(patterns_results_dir, path_out):
    r_root = os.path.join(patterns_results_dir, "R")
    spec_root = os.path.join(patterns_results_dir, "Specifs")
    rel = os.path.relpath(path_out, r_root)
    target = os.path.join(spec_root, rel)
    os.makedirs(target, exist_ok=True)
    return target if target.endswith(os.sep) else target + os.sep


def find_latest_specif_output(patterns_results_dir, path_out):
    """Retourne le dernier TSV de spécificités généré pour un dataset donné."""
    specifs_dir = _build_specifs_output_dir(patterns_results_dir, path_out)
    if not os.path.isdir(specifs_dir):
        return None

    candidates = []
    for filename in os.listdir(specifs_dir):
        if not filename.startswith("specif_") or not filename.endswith(".tsv"):
            continue
        full_path = os.path.join(specifs_dir, filename)
        if os.path.isfile(full_path):
            candidates.append(full_path)

    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)

def compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, execution_time, path_out, total_motifs, lexic_int_str, registry_path=None):
    motif_count = 0
    liste_motifs_str = []
    
    for motif in liste_motifs_clos_corpus:
        liste_motifs_str.append(formate_patterns.from_int_to_str(motif, lexic_int_str))
    lignes_table = [] 
    
    nombre = len(liste_motifs_str)
    print(f"Computing {nombre} motifs freq X texte...")
    for motif in liste_motifs_str:
        trad_motif = str(tools.read_req_CQP(motif))
        print(trad_motif)
        ligne_de_table = enslave_perl.cqp_freq_textes(trad_motif)
        lignes_table.append(ligne_de_table)
        
    df_k = pd.DataFrame(lignes_table, index=liste_motifs_str)
    df_k = df_k.fillna(0)
    df_k = df_k.apply(pd.to_numeric) 
    prefixe=f"{total_motifs}motifs/"
    path_out=path_out+prefixe
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    # Formatter le timestamp sans espaces ni caractères problématiques
    timestamp = execution_time.strftime('%Y%m%d_%H%M%S')
    file_out=f"{path_out}{total_motifs}motifsTexte_df_{timestamp}.tsv"
    file_total =f"{path_out}{total_motifs}motifsTexteOrdered_df_{timestamp}.tsv"

    return df_k, path_out, total_motifs, file_out, file_total
    
def compute_freq_TextesLemma_AFC(seuil, execution_time, path_out, downhill_pos4lemma, registry_path=None):
    lignes_table = []
    print("indexing lemma")
    liste_lemma = enslave_perl.cqp_index_lemma(downhill_pos4lemma)
    print("index done")
    nombre = len(liste_lemma[:seuil])
    print(f"Computing {nombre} lemma freq X texte...")
    print("index done")
    indice=0
    for lemma in liste_lemma[:seuil]:
        req = f'[lemma="{lemma}"]'
        indice+=1
        print(f"{indice} {lemma}")
        ligne_de_table = enslave_perl.cqp_freq_textes(req)
        lignes_table.append(ligne_de_table)
    df_lemma = pd.DataFrame(lignes_table, index=liste_lemma[:seuil])
    df_lemma = df_lemma.fillna(0)
    df_lemma = df_lemma.apply(pd.to_numeric)
    prefixe=f"{seuil}lemma{downhill_pos4lemma}/"
    path_out=path_out+prefixe
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    if downhill_pos4lemma==".*":
        downhill_pos4lemma="allPos"
    # Formatter le timestamp sans espaces ni caractères problématiques
    timestamp = execution_time.strftime('%Y%m%d_%H%M%S')
    file_out = f"{path_out}{seuil}lemma{downhill_pos4lemma}Texte_df_{timestamp}.tsv"
    file_total = f"{path_out}{seuil}lemma{downhill_pos4lemma}TexteOrdered_df_{timestamp}.tsv"

    return file_out, path_out, df_lemma, file_total

def compute_freq_Textes_BigramsLemma_noAFC(execution_time, path_out, seuil, registry_path=None):
    lignes_table = []
    print("indexing bigrams lemma")
    liste_bigrams_lemma = enslave_perl.cqp_index_property("bigrams_lemma")
    print("index done")
    print(f"Computing {seuil} bigrams_lemma freq X texte...")
    print("index done")
    indice=0
    for big in liste_bigrams_lemma[:seuil]:
        lemma1, lemma2 = big.split(" ")
        req = f'[lemma="{lemma1}"][lemma="{lemma2}"]'
        indice+=1
        print(f"{indice} {req}")
        ligne_de_table = enslave_perl.cqp_freq_textes(req)
        lignes_table.append(ligne_de_table)
    df_big = pd.DataFrame(lignes_table, index=liste_bigrams_lemma[:seuil])
    df_big = df_big.fillna(0)
    df_big = df_big.apply(pd.to_numeric)
    prefixe=f"{seuil}bigramslemma/"
    path_out=path_out+prefixe
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    # Formatter le timestamp sans espaces ni caractères problématiques
    timestamp = execution_time.strftime('%Y%m%d_%H%M%S')
    file_out_bigrams = f"{path_out}{seuil}bigramslemmaTexte_df_{timestamp}.tsv"
    return file_out_bigrams, path_out, df_big

def compute_freq_TextesPos_AFC(execution_time, path_out, registry_path=None):
    lignes_table = []
    print("indexing pos")
    liste_pos = enslave_perl.cqp_index_pos()
    print("index done")
    nombre = len(liste_pos)
    print(f"Computing {nombre} pos freq X texte...")
    for pos in liste_pos:
        pos = f'[pos="{pos}"]'
        ligne_de_table = enslave_perl.cqp_freq_textes(pos)
        lignes_table.append(ligne_de_table)
    df_pos = pd.DataFrame(lignes_table, index=liste_pos)
    df_pos = df_pos.fillna(0)
    df_pos = df_pos.apply(pd.to_numeric)
    prefixe="pos/"
    path_out=path_out+prefixe
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    # Formatter le timestamp sans espaces ni caractères problématiques
    timestamp = execution_time.strftime('%Y%m%d_%H%M%S')
    file_out= f"{path_out}posTexte_df_{timestamp}.tsv"
    file_total = f"{path_out}posTexteOrdered_df_{timestamp}.tsv"

    return file_out, path_out, df_pos, file_total


def compute_specifs_function(df_k, minsup_percent, execution_time, specifs, path_out, T, dictionnaire_t, patterns_results_dir):
    dictionnaire_f = df_k.sum(axis=1).to_dict()
    dictionnaire_k = df_k.T.to_dict()
    données_specifs = []
    for motif in dictionnaire_k.keys():
        for texte in dictionnaire_k[motif].keys():
            données_specifs.append({
                "fichier":texte,
                "motif":motif,
                "k":dictionnaire_k[motif][texte],
                "f":dictionnaire_f[motif],
                "t":dictionnaire_t[texte],
                "T":T    
                })
    df_spec = pd.DataFrame(données_specifs)
    # Formatter le timestamp sans espaces ni caractères problématiques
    timestamp = execution_time.strftime('%Y%m%d_%H%M%S')
    specifs_dir = _build_specifs_output_dir(patterns_results_dir, path_out)
    file_out=f"{specifs_dir}SpecifsMotifsTexte_df_{timestamp}.tsv"
    df_spec.to_csv(file_out, sep="\t", encoding="utf-8", index=False)
    final_specif_path = None
    if specifs==True:
        _run_specifs_rscript(minsup_percent, timestamp, specifs_dir, file_out)
        final_specif_path = f"{specifs_dir}specif_{timestamp}.tsv"
    return file_out, final_specif_path

def fusion_internal_clusters(df, lexic_int_str, args, clustering_results_dir="./Clustering_results"):
    # Charger les fichiers de clustering depuis le bon répertoire
    internal_clusters = tools.load_pickles(f"{clustering_results_dir}/Clusters/{args}_clustering_3.pk")
    medoids_clusters = tools.load_pickles(f"{clustering_results_dir}/Medoids/{args}_medoids_3.pk")
    
    internal_clusters_str = {}
    for cluster_id, motifs in internal_clusters.items():
        internal_clusters_str[cluster_id]=[formate_patterns.from_int_to_str(motif, lexic_int_str) for motif in motifs]

    medoids_clusters_str = {k : formate_patterns.from_int_to_str(valeur[0], lexic_int_str) for k, valeur in medoids_clusters.items() if valeur and len(valeur) > 0}
    
    dfs_fusionnes = []
    
    for cluster_id, lignes_a_fusionner in internal_clusters_str.items():
        if cluster_id not in medoids_clusters_str:
            print(f"⚠ Cluster {cluster_id} n'a pas de médoïde valide, ignoré")
            continue
            
        df_cluster = df.loc[lignes_a_fusionner]
        df_somme = df_cluster.sum(numeric_only=True).to_frame().T
        medoid_index = medoids_clusters_str[cluster_id]
        df_medoid = df.loc[[medoid_index]]

        for col in df_somme.columns:
            values = df_somme[col].values
            if len(values) > 0:
                df_medoid[col] = values[0]
            
        dfs_fusionnes.append(df_medoid)

    df_result = pd.concat(dfs_fusionnes)
    return df_result

def get_already_computed_df_id(forme, minsup_percent,gap_min, gap_max, nb_itemset_min, path_id, path_out,modif):
    print("re-using computing data from 'id' metadata instanciation of script")
    if forme=="motifs":
        for file in os.listdir(path_id):
            path_id=path_id+file
            path_out=path_out+file
    else:
        path_out=path_out+forme
    fichiers = sorted(os.listdir(path_id), key=lambda f: os.path.getmtime(os.path.join(path_id, f)),reverse=True)
    # Filtrer pour ne garder que les fichiers avec timestamps valides
    fichiers = [f for f in fichiers if is_valid_timestamp_filename(f)]
    
    # Variables pour stocker le résultat
    f = None
    df_k = None
    
    for f_candidate in fichiers: 
        if f"{forme}Texte_" in f_candidate:
            if _uses_internal_clustering(modif):
                if "_FUS" in f_candidate:
                    print("re-using : " + f_candidate)
                    file_id=path_id+"/"+f_candidate
                    df_k=pd.read_csv(file_id, sep="\t", index_col=0)
                    f = f_candidate
                    break
                else:
                    print("Error : internal_clustering_id is missing")
            else:
                print("re-using : " + f_candidate)
                file_id=path_id+"/"+f_candidate
                df_k=pd.read_csv(file_id, sep="\t", index_col=0)
                f = f_candidate
                break
    
    # Si aucun fichier valide n'a été trouvé, lever une exception
    if f is None or df_k is None:
        raise FileNotFoundError(f"Aucun fichier valide trouvé avec timestamp correct dans {path_id}")
    
    file_out=path_out+"/"+f
    chaine=path_out+"/"+f
    file_total=chaine.replace(f"{forme}Texte",f"{forme}TexteOrdered",1)
    path_out=path_out+"/"
    if not os.path.exists(path_out):
        os.mkdir(path_out)
    return file_out, file_total, path_out, df_k
     
def main(types_textes, minsup_percent,gap_min, gap_max, nb_itemset_min, specifs, df_metadata, modif, metadata, internal_clustering, results, path_out, mode, args, clustering_results_dir="./Clustering_results", patterns_results_dir="./Patterns_results", registry_path=None, lexiques_dir="./Data/Lexiques"):
    execution_time = datetime.datetime.now()
    path_input = f"{lexiques_dir}/dico_str_to_int_all_items.pk"
    path_output = f"{lexiques_dir}/dico_int_to_str_all_items.pk"
    lexic_int_str = formate_patterns.make_dict_int_to_str(path_input, path_output)
    DMT4_clos_corpus = f"{patterns_results_dir}/Closed/{args}_DMT4_merged_files_sorted_closed.pk"
    liste_motifs_clos_corpus = tools.from_pk_corpus_to_list(DMT4_clos_corpus)
    total_motifs=len(liste_motifs_clos_corpus)
    T, dictionnaire_t = enslave_perl.cqp_general()
    
    if total_motifs>0:
        if not os.path.exists(path_out):
            os.mkdir(path_out)
            
        if metadata!="id":## cas de annee, genre, etc.##
            print(metadata)
            path_id = f"{patterns_results_dir}/R/id/{modif}motifs/itemset_min{nb_itemset_min}/gap_min{gap_min}/gap_max{gap_max}/minsup{str(minsup_percent)}/"
            if os.path.exists(path_id):
                try:
                    file_out_motifs, file_total, path_out, df_k = get_already_computed_df_id("motifs", minsup_percent,gap_min, gap_max, nb_itemset_min, path_id,path_out,modif)
                except (FileNotFoundError, Exception) as e:
                    print("Aucun fichier Motifs valide trouvé, recalcul nécessaire...")
                    df_k, path_out, total_motifs, file_out_motifs, file_total = compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, execution_time, path_out, total_motifs, lexic_int_str, registry_path)
            else:
                print("computing from scratch")
                df_k, path_out, total_motifs, file_out_motifs, file_total = compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, execution_time, path_out, total_motifs, lexic_int_str, registry_path)

            if internal_clustering:
                if "_FUS" not in os.path.basename(file_out_motifs):
                    df_k = fusion_internal_clusters(df_k, lexic_int_str, args, clustering_results_dir)
                    file_out_motifs = _with_fus_suffix(file_out_motifs)
                else:
                    print("re-using fused motifs matrix for metadata aggregation")

            df_k = textes2metadata(df_k, df_metadata, metadata.split('_')[-1]).T
            dictionnaire_t = aggregate_t_by_metadata(dictionnaire_t, df_metadata, metadata.split('_')[-1])
            df_k.to_csv(file_out_motifs, sep="\t")
        
        else:
            print(metadata)
            df_k, path_out, total_motifs, file_out_motifs, file_total = compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, execution_time, path_out, total_motifs, lexic_int_str, registry_path)
                
            if internal_clustering:
                df_k = fusion_internal_clusters(df_k, lexic_int_str, args, clustering_results_dir)
                file_out_motifs = _with_fus_suffix(file_out_motifs)
                print(file_out_motifs)

            df_k.to_csv(file_out_motifs, sep="\t")
            
        results[f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"] = file_out_motifs

        
        if specifs:
                _specif_input, final_specif_path = compute_specifs_function(
                    df_k,
                    minsup_percent,
                    execution_time,
                    specifs,
                    path_out,
                    T,
                    dictionnaire_t,
                    patterns_results_dir,
                )
                if final_specif_path:
                    results[f"{metadata}_specifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"] = final_specif_path

        if mode=="auto":
            subprocess.call(["Rscript", "./src/AFC.R", file_out_motifs, path_out]) 
        df_k_total=add_total(df_k)
        df_k_total.to_csv(file_total, sep="\t")
        
    else:
        if not os.path.exists(path_out):
            os.mkdir(path_out)
        if not os.path.exists(f"{path_out}zero-motifs"):
                os.mkdir(f"{path_out}zero-motifs")
    return results, path_out
    
    
    
