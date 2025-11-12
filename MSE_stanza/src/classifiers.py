#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 16:34:47 2025

@author: hugodumoulin
"""
from IPython.display import display
import pandas as pd
import numpy as np
import os

import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.decomposition import PCA
from sklearn.preprocessing import LabelEncoder, StandardScaler
from matplotlib.colors import Normalize

from sklearn.metrics import classification_report
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.svm import LinearSVC, SVC
from sklearn.model_selection import GridSearchCV, ParameterGrid
from sklearn.inspection import permutation_importance

import time
from config import *


def equilibrer_classes(df,classe_col=y_class, random_state=42):
    # Calcul du nombre minimal d'exemples par classe
    n = df.groupby(classe_col).size().min()
    
    # Échantillonnage aléatoire de n exemples par classe
    df_equilibre = df.groupby(classe_col).sample(n=n, random_state=random_state)    
    return df_equilibre

def prepare_dataset(path_data, rep_out, path_target, sampling):
    df_target = pd.read_csv(path_target, sep="\t", index_col=0)
    if sampling:
        df_target_equi = equilibrer_classes(df_target)
        y_motifs=df_target_equi[y_class]
    else:
        y_motifs=df_target[y_class]
        
    df = pd.read_csv(path_data, sep="\t", index_col=0)
    df= df.T
    
    if sampling:
        df=df.loc[df_target_equi.index]
    
    # rapporte à la taille de chaque texte
    
    # for ligne in df.index:
    #     for col in df.columns:
    #         df.loc[ligne, col]=df.loc[ligne, col]/dictionnaire_t[ligne]
    
    # mieux est de rapporter à la freq totale de chaque ligne comme en AFC
    df= df.div(df.sum(axis=1), axis=0)
    
    
    X_motifs=df.to_numpy()
    X_features=df.columns.tolist()
    X_features = [s.replace('"', '').replace("'", '') for s in X_features]
    
    nb_col = df.shape[1]
    
    df.to_csv(f"{rep_out}{nb_col}motifs_data_classif.tsv",  sep="\t")
    
    return X_motifs, y_motifs, X_features

def PCA_transform(X_motifs, nb_comp, rep_out, X_features):
    scaler = StandardScaler()
    nrow,ncol=X_motifs.shape
    min_dim=min(nrow,ncol)
    if nb_comp>min_dim:
        nb_comp=min_dim
    scaler.fit(X_motifs)
    X_motifs_scaled =scaler.transform(X_motifs)
    pca = PCA(n_components=nb_comp)
    X_motifs_scaled_reduced = pca.fit_transform(X_motifs_scaled)
    
    loadings = pca.components_.T
    n_features = X_motifs_scaled_reduced.shape[1]
    variable_names = X_features
    df_result = pd.DataFrame(index=variable_names)
    for i in range(2):  # pour PC1 et PC2
        coord = loadings[:, i]
        contrib = 100 * coord**2 / np.sum(coord**2)
        df_result[f'contrib_PC{i+1}'] = contrib
        df_result[f'coord_PC{i+1}'] = coord
    # Sauvegarde en CSV
    df_result.to_csv(f"{rep_out}pca_contributions_{nb_comp}comps.tsv", sep="\t")
    
    return X_motifs_scaled_reduced

def split_data(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
    return X_train, X_test, y_train, y_test, X, y

def cross_val_classification_report(model,X,y,n_splits,n_repeats,random_state = 42, target_names = None):
    cv = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=random_state)
    y_true = []
    y_pred = []
    for train,test in cv.split(X,y):
        X_train = X[train]
        X_test = X[test]
        y_train = y[train]
        y_test = y[test]

        y_test_pred = model.fit(X_train,y_train).predict(X_test)
        y_true.append(y_test)
        y_pred.append(y_test_pred)
    y_true=np.concatenate(y_true)
    y_pred=np.concatenate(y_pred)
    return classification_report(y_true,y_pred,target_names=target_names)

#-------- SVM --------------
def svm_grid_search(X_motifs_scaled_reduced, y_motifs, rep_out):
     param_grid=[
    {'C': [1, 10, 100, 1000], 'kernel': ['linear']},
    {'C': [1, 10, 100, 1000], 'gamma': [0.001, 0.0001], 'kernel': ['rbf']},
  ]
     class_counts = pd.Series(y_motifs).value_counts()
     min_class_size = class_counts.min()
     n_splits=n_splits = min(5, min_class_size)
     n_repeats=10
     cv = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=50)
     
     total_combinations = len(list(ParameterGrid(param_grid)))
     total_fits = total_combinations * n_splits * n_repeats
     
     grid_search = GridSearchCV(SVC(class_weight='balanced'), param_grid, cv=cv, scoring='f1_macro', n_jobs=-1, verbose=1)
     grid_search.fit(X_motifs_scaled_reduced, y_motifs)
     
     best_model = grid_search.best_estimator_
     best_params = grid_search.best_params_
     
     report = cross_val_classification_report(
        model=best_model,
        X=X_motifs_scaled_reduced,
        y=y_motifs,
        n_splits= min(5, min_class_size),
        n_repeats=10,
        random_state=50
    )
     
     with open(f"{rep_out}svm_best_model_report.txt", "w") as f:
         f.write(report)
    
     return best_model, best_params

def cut_plot_decision(svm, X_scaled_reduced, y_motifs, rep_out):
    X_2D = X_scaled_reduced[:, :2]

    x_min, x_max = X_2D[:, 0].min() - 1, X_2D[:, 0].max() + 1
    y_min, y_max = X_2D[:, 1].min() - 1, X_2D[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.1),
                         np.arange(y_min, y_max, 0.1))
    grid_2D = np.c_[xx.ravel(), yy.ravel()]

    #Extension de la grille à 50 dimensions (avec zéros pour les composantes >2)
    n_comp = X_scaled_reduced.shape[1]
    grid_full = np.zeros((grid_2D.shape[0], n_comp))
    grid_full[:, :2] = grid_2D  # seules les 2 premières dimensions varient

    Z = svm.predict(grid_full)

    le = LabelEncoder()
    y_encoded = le.fit_transform(y_motifs)
    Z_encoded = le.transform(Z)
    Z_encoded = Z_encoded.reshape(xx.shape)

    plt.figure(figsize=(8, 6))
    plt.contourf(xx, yy, Z_encoded, alpha=0.8, cmap=plt.cm.coolwarm)

    scatter = plt.scatter(X_2D[:, 0], X_2D[:, 1], c=y_encoded,
                          cmap=plt.cm.coolwarm, edgecolors='k', s=40)

    plt.xlabel('Composante 1')
    plt.ylabel('Composante 2')
    plt.title('Frontière de décision SVM (projection 2D)')
    handles, _ = scatter.legend_elements()
    plt.legend(handles, le.classes_, title="Classes", loc="best")

    plt.savefig(f"{rep_out}/{svm}svm_cut_plot.png", dpi=300, bbox_inches='tight')
    plt.close()


#-------- Decision Tree -------
def decision_tree(X_motifs, y_motifs, X_features, rep_out):
    from sklearn import tree
    
    X_train, X_test, y_train, y_test, X_motifs, y_motifs = split_data(X_motifs, y_motifs)

    
    clf_tree = tree.DecisionTreeClassifier()
    clf_tree.fit(X_train, y_train)
    
    import graphviz 
    dot_data = tree.export_graphviz(clf_tree, out_file=None,
                                    feature_names=X_features,
                                    class_names=clf_tree.classes_) 
    graph = graphviz.Source(dot_data) 
    graph.render(f"{rep_out}tree") 
    

#----- Dummy -------
from sklearn.dummy import DummyClassifier

def dummy(X_motifs, y_motifs,rep_out):
    X_train, X_test, y_train, y_test, X_motifs, y_motifs = split_data(X_motifs, y_motifs)
    dummy = DummyClassifier(strategy='stratified')
    dummy.fit(X_train, y_train)
    y_pred_dummy = dummy.predict(X_test)
    report = classification_report(y_test, y_pred_dummy)
    with open(f"{rep_out}dummy.txt", "w") as f:
            f.write(report)
    
def main(minsup, results, path_target, sampling, sub_tidy_metadata, list_metadata):
    path_classif_out = "./Patterns_results/Classifieurs/"
    if not os.path.exists(path_classif_out):
        os.mkdir(path_classif_out)
    for metadata in list_metadata:
        path_classif_out=path_classif_out+metadata+"/"
        if not os.path.exists(path_classif_out):
            os.mkdir(path_classif_out)
        for prefixe,filename in results.items():
            print("classification : \n"+prefixe+"\n"+filename)
            if metadata in prefixe:
                if not ("lemma" in prefixe or "pos" in prefixe or "bigrams" in prefixe):
                        if not os.path.exists(path_classif_out+"motifs/"):
                            os.mkdir(path_classif_out+"motifs/")
                        rep_pref=path_classif_out+"motifs/"
                        if not os.path.exists(rep_pref):
                            os.mkdir(rep_pref)
                        for tidy_metadata in sub_tidy_metadata:
                            if metadata in tidy_metadata:
                                if tidy_metadata in prefixe:
                                    rep_pref=rep_pref+tidy_metadata+"/"
                                    if not os.path.exists(rep_pref):
                                        os.mkdir(rep_pref)
                                    name = prefixe.split("motifs_")[1]
                                    rep_out = rep_pref+"minsup"+name+"/"
                else:
                    name = prefixe.replace(f"{metadata}_","")
                    rep_pref=path_classif_out+name+"/"
                    rep_out = rep_pref
                
            if not os.path.exists(rep_out):
                os.mkdir(rep_out)
                X_motifs, y_motifs, X_features= prepare_dataset(filename, rep_out, path_target, sampling)
                if len(X_motifs)>0:
                    nb_comp=50
                    X_motifs_scaled_reduced = PCA_transform(X_motifs, nb_comp, rep_out, X_features)
                    decision_tree(X_motifs, y_motifs, X_features, rep_out)
                    best_model, best_params = svm_grid_search(X_motifs_scaled_reduced, y_motifs, rep_out)
                    
                
                    cut_plot_decision(best_model, X_motifs_scaled_reduced, y_motifs, rep_out)
                    dummy(X_motifs, y_motifs, rep_out)


    

 