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
from sklearn.preprocessing import LabelEncoder



def prepare_dataset(path_data, rep_out, path_target):
    df = pd.read_csv(path_data, sep="\t", index_col=0)
    df= df.T
    
    df_target = pd.read_csv(path_target, sep="\t", index_col=0)
    
    # X_motifs=df.values()
    X_motifs=df.to_numpy()
    X_features=df.columns.tolist()
    X_features = [s.replace('"', '').replace("'", '') for s in X_features]
    # for nom_ligne in df.index:
    #     if nom_ligne.isupper():
    #         df.loc[nom_ligne, "target"] = "rapport"
    #     else:
    #         df.loc[nom_ligne, "target"] = "CR"
    # y_motifs=df.target
    
    y_motifs=df_target.target
    
    
    df.to_csv(f"{rep_out}data_classif.tsv",  sep="\t")
    
    # Séparation des données
    X_train, X_test, y_train, y_test = train_test_split(X_motifs, y_motifs, test_size=0.3)

    return X_train, X_test, y_train, y_test, X_motifs, y_motifs, X_features

#-------- SVM --------------
def svm_train(X_train, X_test, y_train, y_test, rep_out):
    from sklearn.svm import LinearSVC
        
    # Entraînement du SVM
    svm = LinearSVC()
    svm.fit(X_train, y_train)
    y_pred = svm.predict(X_test)
    report = classification_report(y_test, y_pred)
    with open(f"{rep_out}svm_report.txt", "w") as f:
        f.write(report)
        
    return svm

def svm_plot_decision(svm, X_motifs, y_motifs, rep_out):
    # Réduction de dimension avec PCA
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_motifs)
    
    # Tracer le graphique
    plt.figure(figsize=(8, 6))
    ax = plt.gca()
    
    # Encodage des étiquettes (si nécessaire)
    le = LabelEncoder()
    y_numeric = le.fit_transform(y_motifs)
    
    # Définir les limites de la zone de tracé pour les données réduites
    xlim = (X_pca[:, 0].min() - 1, X_pca[:, 0].max() + 1)
    ylim = (X_pca[:, 1].min() - 1, X_pca[:, 1].max() + 1)
    
    # Créer un maillage de points pour la surface de décision
    xx, yy = np.meshgrid(np.linspace(xlim[0], xlim[1], 30),
                         np.linspace(ylim[0], ylim[1], 30))
    
    # Prédire les valeurs de la fonction de décision sur le maillage
    Z = svm.decision_function(pca.inverse_transform(np.c_[xx.ravel(), yy.ravel()]))
    Z = Z.reshape(xx.shape)
    
    # Tracer la frontière de décision (niveau 0)
    plt.contour(xx, yy, Z, levels=[0], linewidths=2, colors='k')
    
    # Tracer les points de données
    scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=y_numeric, cmap=plt.cm.Paired, edgecolors='k', s=50)
    
    # Récupérer les handles et labels
    handles, labels = scatter.legend_elements()
    
    # Nettoyer les labels LaTeX et les convertir en noms de classes
    named_labels = [le.inverse_transform([int(lbl.strip('$\\mathdefault{}'))])[0] for lbl in labels]
    
    # Ajouter une légende avec les noms de classes réels
    plt.legend(handles, named_labels, title="Classes")
    
    # Ajouter des labels et le titre
    plt.xlabel('PCA Component 1')
    plt.ylabel('PCA Component 2')
    plt.title('SVM Decision Boundary and Data Points')
    
    # Afficher le graphique
    plt.savefig(f"{rep_out}svm_plot.png", dpi=300, bbox_inches='tight')
    # plt.show()

#-------- Decision Tree -------
def decision_tree(X_train, y_train, X_features, rep_out):
    from sklearn import tree
    
    clf_tree = tree.DecisionTreeClassifier()
    clf_tree.fit(X_train, y_train)
    
    import graphviz 
    dot_data = tree.export_graphviz(clf_tree, out_file=None,
                                    feature_names=X_features,
                                    class_names=clf_tree.classes_) 
    graph = graphviz.Source(dot_data) 
    graph.render(f"{rep_out}tree") 
    
    
def main(minsup, file_out_motifs, file_out_lemma, file_out_pos, prefixe_motifs, prefixe_lemma, prefixe_pos, path_target):
    path_classif_out = "./Patterns_results/Classifieurs/"
    if not os.path.exists(path_classif_out):
        os.mkdir(path_classif_out)
    path_classif_out += str(minsup)+"/"
    if not os.path.exists(path_classif_out):
        os.mkdir(path_classif_out)
    liste_prefixes = [prefixe_motifs, prefixe_lemma, prefixe_pos]
    liste_data = [file_out_motifs, file_out_lemma, file_out_pos]
    for filename, prefixe in zip(liste_data, liste_prefixes):
        # if not os.path.exists(path_out):
        #     os.mkdir(path_out)
        # name = filename[:-4].replace(path_out, "")
        rep_out = path_classif_out+prefixe
        if not os.path.exists(rep_out):
            os.mkdir(rep_out)
        X_train, X_test, y_train, y_test, X_motifs, y_motifs, X_features = prepare_dataset(filename, rep_out, path_target)
        svm = svm_train(X_train, X_test, y_train, y_test, rep_out)
        svm_plot_decision(svm, X_motifs, y_motifs, rep_out)
        decision_tree(X_train, y_train, X_features, rep_out)
    



 