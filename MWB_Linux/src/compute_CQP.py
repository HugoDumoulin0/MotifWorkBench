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


def add_total(df):
    df_total = df.copy()
    df_total["total"] = df.sum(axis=1)
    df_total = df_total.sort_values(by="total", ascending=False)
    return df_total


def aggregate_t_by_metadata(dictionnaire_t, df_metadata, metadata):
    """Agrège les tailles de textes par valeur de métadonnée pour le calcul des spécificités."""
    if metadata == "id":
        return dictionnaire_t

    metadata_key = metadata.split('_')[-1]
    if metadata_key not in df_metadata.columns:
        raise KeyError(f"Colonne de métadonnée introuvable pour les spécificités : {metadata_key}")

    df_meta = df_metadata.copy()
    df_meta = df_meta[df_meta.index.isin(dictionnaire_t.keys())].copy()
    df_meta[metadata_key] = df_meta[metadata_key].astype(str)
    df_meta["_taille_texte"] = df_meta.index.map(dictionnaire_t)

    aggregated = (
        df_meta
        .groupby(metadata_key)["_taille_texte"]
        .sum()
        .to_dict()
    )
    return aggregated

def compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, execution_time, path_out, total_motifs, lexic_int_str, registry_path=""):
    motif_count = 0
    liste_motifs_str = []
    
    for motif in liste_motifs_clos_corpus:
        liste_motifs_str.append(formate_patterns.from_int_to_str(motif, lexic_int_str))
    lignes_table = [] 
    
    nombre = len(liste_motifs_str)
    print(f"Computing {nombre} motifs freq X texte...")
    print(f"[DEBUG] Registry path: {registry_path}")
    print(f"[DEBUG] Registry exists: {os.path.exists(registry_path)}")
    
    empty_count = 0
    for i, motif in enumerate(liste_motifs_str):
        trad_motif = str(tools.read_req_CQP(motif))
        print(trad_motif)
        ligne_de_table = enslave_perl.cqp_freq_textes(trad_motif, registry_path)
        if not ligne_de_table:  # Dict vide
            empty_count += 1
            if empty_count <= 3:  # Afficher seulement les 3 premiers
                print(f"[DEBUG] Motif {i+1}/{nombre}: aucune fréquence retournée pour {trad_motif[:50]}...")
        lignes_table.append(ligne_de_table)
    
    if empty_count > 0:
        print(f"[DEBUG] Total: {empty_count}/{nombre} motifs sans fréquences")
        
    df_k = pd.DataFrame(lignes_table, index=liste_motifs_str)
    print(f"[DEBUG] DataFrame créé: {df_k.shape[0]} lignes x {df_k.shape[1]} colonnes")
    
    if df_k.shape[1] == 0:
        print(f"[ERREUR] DataFrame vide (0 colonnes) - Le corpus CWB n'a peut-être pas été interrogé correctement")
        print(f"    Vérifiez que le corpus CWB est correctement indexé et accessible via {registry_path}")
    
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
    
def compute_freq_TextesLemma_AFC(seuil, execution_time, path_out, downhill_pos4lemma, registry_path=""):
    lignes_table = []
    print("indexing lemma")
    liste_lemma = enslave_perl.cqp_index_lemma(downhill_pos4lemma, registry_path)
    print("index done")
    nombre = len(liste_lemma[:seuil])
    print(f"Computing {nombre} lemma freq X texte...")
    print("index done")
    indice=0
    for lemma in liste_lemma[:seuil]:
        req = f'[lemma="{lemma}"]'
        indice+=1
        print(f"{indice} {lemma}")
        ligne_de_table = enslave_perl.cqp_freq_textes(req, registry_path)
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

def compute_freq_Textes_BigramsLemma_noAFC(execution_time, path_out, seuil, registry_path=""):
    lignes_table = []
    print("indexing bigrams lemma")
    liste_bigrams_lemma = enslave_perl.cqp_index_property("bigrams_lemma", registry_path)
    print("index done")
    print(f"Computing {seuil} bigrams_lemma freq X texte...")
    print("index done")
    indice=0
    for big in liste_bigrams_lemma[:seuil]:
        lemma1, lemma2 = big.split(" ")
        req = f'[lemma="{lemma1}"][lemma="{lemma2}"]'
        indice+=1
        print(f"{indice} {req}")
        ligne_de_table = enslave_perl.cqp_freq_textes(req, registry_path)
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

def compute_freq_TextesPos_AFC(execution_time, path_out, registry_path=""):
    lignes_table = []
    print("indexing pos")
    liste_pos = enslave_perl.cqp_index_pos(registry_path)
    print("index done")
    nombre = len(liste_pos)
    print(f"Computing {nombre} pos freq X texte...")
    for pos in liste_pos:
        pos = f'[pos="{pos}"]'
        ligne_de_table = enslave_perl.cqp_freq_textes(pos, registry_path)
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


def _validate_specifs_counts(df_k, T, dictionnaire_t):
    """Le modèle hypergéométrique exige k <= t, f <= T et t > 0 : on refuse explicitement sinon."""
    missing = [col for col in df_k.columns if col not in dictionnaire_t]
    if missing:
        raise ValueError("Tailles de partition manquantes pour les spécificités : " + ", ".join(map(str, missing[:10])))
    t_series = pd.Series({col: dictionnaire_t[col] for col in df_k.columns}, dtype=float)
    problems = []
    if (t_series <= 0).any():
        problems.append("partitions de taille nulle : " + ", ".join(map(str, t_series[t_series <= 0].index[:10])))
    over_t = df_k.gt(t_series, axis=1)
    if over_t.values.any():
        n_cells = int(over_t.values.sum())
        motifs = list(df_k.index[over_t.any(axis=1)][:3])
        problems.append(f"{n_cells} fréquence(s) de motif supérieure(s) à la taille de la partition (ex. : {motifs})")
    f_over = df_k.sum(axis=1) > T
    if f_over.any():
        problems.append(f"{int(f_over.sum())} motif(s) plus fréquent(s) que la taille du corpus")
    if problems:
        raise ValueError("Spécificités impossibles à calculer : " + " ; ".join(problems))


def _write_specifs_input(df_k, T, dictionnaire_t, file_out):
    """Table large (motifs x partitions) + ligne "others" = taille t de chaque partition.

    Remplace l'ancien format long, qui ferait des millions de lignes sur des motifs non fusionnés.
    Écriture brute (motifs non échappés, relus par R avec quote="") : pandas échapperait les guillemets.
    """
    df_k = df_k.apply(pd.to_numeric)
    _validate_specifs_counts(df_k, T, dictionnaire_t)
    if any("\t" in str(name) or "\n" in str(name) for name in df_k.index):
        raise ValueError("Un motif contient une tabulation ou un saut de ligne : format TSV impossible.")
    def fmt(v):
        v = float(v)
        return str(int(v)) if v == int(v) else format(v, "g")
    with open(file_out, "w", encoding="utf-8", newline="") as handle:
        handle.write("\t".join(["motif"] + [str(col) for col in df_k.columns]) + "\n")
        for name, values in zip(df_k.index, df_k.itertuples(index=False, name=None)):
            handle.write("\t".join([str(name)] + [fmt(v) for v in values]) + "\n")
        handle.write("\t".join(["others"] + [fmt(dictionnaire_t[col]) for col in df_k.columns]) + "\n")
    return file_out


def _keep_medoid_specifs(specif_path, keep_rows):
    """Clustering interne : la table complète devient allmotifs_specif_*.tsv, et specif_*.tsv
    ne garde que les médoïdes (dans l'ordre des clusters), sans réinterpréter les valeurs écrites par R."""
    full_path = os.path.join(os.path.dirname(specif_path), "allmotifs_" + os.path.basename(specif_path))
    os.replace(specif_path, full_path)
    with open(full_path, encoding="utf-8") as handle:
        header = handle.readline()
        lines = {line.split("\t", 1)[0]: line for line in handle}
    missing = [row for row in keep_rows if row not in lines]
    if missing:
        raise RuntimeError(f"Spécificités absentes pour {len(missing)} médoïde(s), ex. : {missing[:3]}")
    with open(specif_path, "w", encoding="utf-8") as handle:
        handle.write(header)
        for row in keep_rows:
            handle.write(lines[row])
    return specif_path


def compute_specifs_function(df_k, minsup_percent, execution_time, specifs, path_out, T, dictionnaire_t, total_motifs=None, keep_rows=None):
    """Spécificités calculées sur des fréquences de motifs NON fusionnées (df_k : motifs x partitions).
    keep_rows (clustering interne) : médoïdes à conserver dans specif_*.tsv ; table complète dans allmotifs_specif_*.tsv."""
    os.makedirs(path_out, exist_ok=True)
    # Formatter le timestamp sans espaces ni caractères problématiques
    timestamp = execution_time.strftime('%Y%m%d_%H%M%S')
    file_out = _write_specifs_input(df_k, T, dictionnaire_t, f"{path_out}SpecifsMotifsTexte_wide_{timestamp}.tsv")
    display_file = file_out
    if specifs==True:
        seuil_arg = str(total_motifs) if total_motifs is not None else "motifs"
        result = subprocess.call([
            "Rscript", "./src/compute_specifs.r",
            str(minsup_percent), timestamp, path_out, file_out, seuil_arg, "motifs"
        ])
        r_output_file = os.path.join(path_out, f"specif_{seuil_arg}motifs{timestamp}.tsv")
        if result == 0 and os.path.exists(r_output_file):
            display_file = r_output_file
            if keep_rows is not None:
                display_file = _keep_medoid_specifs(r_output_file, keep_rows)
        if result != 0:
            print(f"⚠ compute_specifs.r a retourné le code {result} pour {file_out}")
    return display_file

def fusion_internal_clusters(df, lexic_int_str, args, clustering_results_dir="./Clustering_results"):
    # Charger les fichiers de clustering depuis le bon répertoire
    clusters_path = f"{clustering_results_dir}/Clusters/{args}_clustering_3.pk"
    medoids_path = f"{clustering_results_dir}/Medoids/{args}_medoids_3.pk"
    
    print(f"[FUSION] Tentative de chargement des clusters:")
    print(f"  - Clusters: {clusters_path}")
    print(f"  - Medoids: {medoids_path}")
    print(f"  - DataFrame entrée: {df.shape[0]} lignes x {df.shape[1]} colonnes")
    
    try:
        internal_clusters = tools.load_pickles(clusters_path)
        medoids_clusters = tools.load_pickles(medoids_path)
    except FileNotFoundError as e:
        print(f"[FUSION] Fichier de clustering introuvable: {e}")
        print(f"    Retour du DataFrame original sans fusion")
        return df
    except Exception as e:
        print(f"[FUSION] Erreur lors du chargement des fichiers de clustering: {e}")
        print(f"    Retour du DataFrame original sans fusion")
        return df
    
    if not internal_clusters or not medoids_clusters:
        print(f"[FUSION] Fichiers de clustering vides pour {args}")
        print(f"    Clusters: {len(internal_clusters) if internal_clusters else 0} entrées")
        print(f"    Medoids: {len(medoids_clusters) if medoids_clusters else 0} entrées")
        print(f"    Retour du DataFrame original sans fusion")
        return df
    
    print(f"[FUSION] Clusters chargés: {len(internal_clusters)} clusters, {len(medoids_clusters)} médoïdes")
    
    internal_clusters_str = {}
    for cluster_id, motifs in internal_clusters.items():
        internal_clusters_str[cluster_id]=[formate_patterns.from_int_to_str(motif, lexic_int_str) for motif in motifs]

    medoids_clusters_str = {k : formate_patterns.from_int_to_str(valeur[0], lexic_int_str) for k, valeur in medoids_clusters.items() if valeur and len(valeur) > 0}
    
    print(f"[FUSION] Après conversion en strings: {len(internal_clusters_str)} clusters, {len(medoids_clusters_str)} médoïdes")
    
    dfs_fusionnes = []
    clusters_ignores = []
    
    for cluster_id, lignes_a_fusionner in internal_clusters_str.items():
        if cluster_id not in medoids_clusters_str:
            clusters_ignores.append(cluster_id)
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
    
    if clusters_ignores:
        print(f"{len(clusters_ignores)} cluster(s) sans médoïde valide ignoré(s): {clusters_ignores[:5]}{'...' if len(clusters_ignores) > 5 else ''}")
    
    if not dfs_fusionnes:
        print(f"[FUSION] ERREUR: Aucun cluster valide trouvé après fusion")
        print(f"    Total clusters: {len(internal_clusters_str)}, tous ignorés")
        print(f"    Médoïdes disponibles: {len(medoids_clusters_str)}")
        print(f"    Retour du DataFrame original sans fusion")
        return df

    df_result = pd.concat(dfs_fusionnes)
    print(f"[FUSION] Résultat final: {df_result.shape[0]} lignes x {df_result.shape[1]} colonnes")
    return df_result

def get_already_computed_df_id(forme, minsup_percent,gap_min, gap_max, nb_itemset_min, path_id, path_out,modif, want_raw=False):
    print("re-using computing data from 'id' metadata instanciation of script")
    internal_clustering_enabled = "internal_clustering_" in (modif or "")

    if forme=="motifs":
        subdirs = [
            file_name
            for file_name in os.listdir(path_id)
            if os.path.isdir(os.path.join(path_id, file_name))
        ]
        if not subdirs:
            raise FileNotFoundError(f"Aucun sous-dossier de résultats trouvé dans {path_id}")

        subdirs = sorted(
            subdirs,
            key=lambda f: os.path.getmtime(os.path.join(path_id, f)),
            reverse=True,
        )
        selected_subdir = subdirs[0]
        path_id = os.path.join(path_id, selected_subdir)
        path_out = os.path.join(path_out, selected_subdir)
    else:
        path_out = os.path.join(path_out, forme)

    fichiers = sorted(os.listdir(path_id), key=lambda f: os.path.getmtime(os.path.join(path_id, f)),reverse=True)
    # Filtrer pour ne garder que les fichiers avec timestamps valides
    fichiers = [f for f in fichiers if is_valid_timestamp_filename(f)]
    
    # Variables pour stocker le résultat
    f = None
    df_k = None
    
    for f_candidate in fichiers: 
        if f"{forme}Texte_" not in f_candidate:
            continue
        if internal_clustering_enabled:
            # want_raw : matrice des motifs individuels (avant fusion) ; sinon matrice fusionnée
            if ("_FUS" in f_candidate) == want_raw:
                continue
        print("re-using : " + f_candidate)
        file_id = os.path.join(path_id, f_candidate)
        df_k=pd.read_csv(file_id, sep="\t", index_col=0)
        f = f_candidate
        break
    
    # Si aucun fichier valide n'a été trouvé, lever une exception
    if f is None or df_k is None:
        raise FileNotFoundError(f"Aucun fichier valide trouvé avec timestamp correct dans {path_id}")
    
    os.makedirs(path_out, exist_ok=True)
    file_out = os.path.join(path_out, f)
    chaine = file_out
    file_total=chaine.replace(f"{forme}Texte",f"{forme}TexteOrdered",1)
    path_out = path_out + "/"
    return file_out, file_total, path_out, df_k
     
def main(types_textes, minsup_percent,gap_min, gap_max, nb_itemset_min, specifs, df_metadata, modif, metadata, internal_clustering, results, path_out, mode, args, clustering_results_dir="./Clustering_results", patterns_results_dir="./Patterns_results", registry_path="", lexiques_dir=""):
    if not lexiques_dir:
        raise ValueError("lexiques_dir est requis pour compute_CQP.main().")
    execution_time = datetime.datetime.now()
    lexic_int_str = formate_patterns.make_dict_int_to_str(
        f"{lexiques_dir}/dico_str_to_int_all_items.pk"
    )
    DMT4_clos_corpus = f"{patterns_results_dir}/Closed/{args}_DMT4_merged_files_sorted_closed.pk"
    liste_motifs_clos_corpus = tools.from_pk_corpus_to_list(DMT4_clos_corpus)
    total_motifs=len(liste_motifs_clos_corpus)
    T, dictionnaire_t = enslave_perl.cqp_general(registry_path)
    path_specifs = (
        f"{patterns_results_dir}/Specifs/{metadata}/{modif}motifs/"
        f"itemset_min{nb_itemset_min}/gap_min{gap_min}_gap_max{gap_max}/minsup{str(minsup_percent)}/"
        f"{total_motifs}motifs/"
    )
    
    if total_motifs>0:
        if not os.path.exists(path_out):
            os.mkdir(path_out)
            
        if metadata!="id":## cas de annee, genre, etc.##
            print(metadata)
            path_id = f"{patterns_results_dir}/R/id/{modif}motifs/itemset_min{nb_itemset_min}/gap_min{gap_min}_gap_max{gap_max}/minsup{str(minsup_percent)}/"
            if os.path.exists(path_id):
                try:
                    # Toujours repartir des motifs individuels : les spécificités se calculent avant fusion.
                    file_out_motifs, file_total, path_out, df_raw = get_already_computed_df_id("motifs", minsup_percent,gap_min, gap_max, nb_itemset_min, path_id,path_out,modif, want_raw=True)
                except (FileNotFoundError, Exception) as e:
                    print("Aucun fichier Motifs valide trouvé, recalcul nécessaire...")
                    df_raw, path_out, total_motifs, file_out_motifs, file_total = compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, execution_time, path_out, total_motifs, lexic_int_str, registry_path)
            else:
                print("computing from scratch")
                df_raw, path_out, total_motifs, file_out_motifs, file_total = compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, execution_time, path_out, total_motifs, lexic_int_str, registry_path)
            # Agrégation par métadonnée (somme par colonne : commute avec la fusion des clusters)
            df_raw = textes2metadata(df_raw, df_metadata, metadata.split('_')[-1]).T
            df_raw.to_csv(file_out_motifs, sep="\t")
            if internal_clustering:
                df_k = fusion_internal_clusters(df_raw, lexic_int_str, args, clustering_results_dir)
                if not file_out_motifs.endswith("_FUS.tsv"):
                    file_out_motifs = file_out_motifs[:-4]+"_FUS.tsv"
                df_k.to_csv(file_out_motifs, sep="\t")
            else:
                df_k = df_raw
        
        else:
            print(metadata)
            df_raw, path_out, total_motifs, file_out_motifs, file_total = compute_freq_TextesMotifs_AFC(liste_motifs_clos_corpus, execution_time, path_out, total_motifs, lexic_int_str, registry_path)
            # Matrice non fusionnée conservée : réutilisée par les autres métadonnées et les spécificités
            df_raw.to_csv(file_out_motifs, sep="\t")
            df_k = df_raw
                
            if internal_clustering:
                lexic_int_str = formate_patterns.make_dict_int_to_str(
                    f"{lexiques_dir}/dico_str_to_int_all_items.pk"
                )
                df_k = fusion_internal_clusters(df_raw, lexic_int_str, args, clustering_results_dir)
                file_out_motifs = file_out_motifs[:-4]+"_FUS.tsv"
                print(file_out_motifs)
                df_k.to_csv(file_out_motifs, sep="\t")
            
        results[f"{metadata}_{modif}motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"] = file_out_motifs

        
        if specifs:
                dictionnaire_t_specifs = aggregate_t_by_metadata(dictionnaire_t, df_metadata, metadata)
                # Spécificités AVANT clustering : sur les motifs individuels, puis chaque cluster
                # reçoit la spécificité de son médoïde (la somme des membres double-compte les occurrences).
                specifs_file = compute_specifs_function(
                    df_raw,
                    minsup_percent,
                    execution_time,
                    specifs,
                    path_specifs,
                    T,
                    dictionnaire_t_specifs,
                    total_motifs,
                    keep_rows=list(df_k.index) if internal_clustering else None,
                )
                results[f"{metadata}_{modif}specifs_motifs_{minsup_percent}_{gap_min}_{gap_max}_{nb_itemset_min}"] = specifs_file

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
    
    
    
