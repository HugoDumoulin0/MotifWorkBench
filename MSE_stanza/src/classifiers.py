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


def prepare_dataset(path_data, rep_out, path_target):
    df = pd.read_csv(path_data, sep="\t", index_col=0)
    df= df.T
    
    df_target = pd.read_csv(path_target, sep="\t", index_col=0)
    
    X_motifs=df.to_numpy()
    X_features=df.columns.tolist()
    X_features = [s.replace('"', '').replace("'", '') for s in X_features]
    
    y_motifs=df_target.target
    
    
    df.to_csv(f"{rep_out}data_classif.tsv",  sep="\t")
    
    return X_motifs, y_motifs, X_features

def PCA_transform(X_motifs):
    scaler = StandardScaler()
    scaler.fit(X_motifs)
    X_motifs_scaled =scaler.transform(X_motifs)
    pca = PCA(n_components=2)
    X_motifs_scaled_reduced = pca.fit_transform(X_motifs_scaled)
    
    return X_motifs_scaled_reduced

def split_data(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
    return X_train, X_test, y_train, y_test, X, y

#-------- SVM --------------
def svm_train(X_motifs_scaled_reduced, y_motifs, rep_out):
    from sklearn.svm import LinearSVC
    
    X_train, X_test, y_train, y_test, X_motifs_scaled_reduced, y_motifs = split_data(X_motifs_scaled_reduced, y_motifs)


    svm = LinearSVC()
    classify = svm.fit(X_train, y_train)
    y_pred = svm.predict(X_test)
    report = classification_report(y_test, y_pred)
    with open(f"{rep_out}svm_report.txt", "w") as f:
        f.write(report)
        
    return svm, classify

def svm_plot_decision(svm, X_motifs_scaled_reduced, y_motifs, rep_out, classify):
    x_min, x_max = X_motifs_scaled_reduced[:, 0].min() - 1, X_motifs_scaled_reduced[:, 0].max() + 1
    y_min, y_max = X_motifs_scaled_reduced[:, 1].min() - 1, X_motifs_scaled_reduced[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.01),
                         np.arange(y_min, y_max, 0.01))
    Z = svm.predict(np.c_[xx.ravel(), yy.ravel()])
    
    le = LabelEncoder()
    Z_encoded = le.fit_transform(Z)
    Z_encoded = Z_encoded.reshape(xx.shape)
    y_encoded = le.transform(y_motifs)
    
    plt.figure()
    plt.contourf(xx, yy, Z_encoded.reshape(xx.shape), alpha=0.8, cmap=plt.cm.coolwarm)
    scatter = plt.scatter(X_motifs_scaled_reduced[:, 0], X_motifs_scaled_reduced[:, 1], c=y_encoded, edgecolors='k', marker='o', cmap=plt.cm.coolwarm)
    plt.xlabel('Axe 1')
    plt.ylabel('Axe 2')
    plt.title('SVM Decision Boundary')
    
    
    handles, labels = scatter.legend_elements()
    
    plt.legend(handles, le.classes_, title="Classes", loc="best")
    plt.savefig(f"{rep_out}svm_plot.png", dpi=300, bbox_inches='tight')
    plt.close()

    
    # plt.show()


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
        X_motifs, y_motifs, X_features= prepare_dataset(filename, rep_out, path_target)
        X_motifs_scaled_reduced = PCA_transform(X_motifs)
        svm, classify = svm_train(X_motifs_scaled_reduced, y_motifs, rep_out)
        svm_plot_decision(svm, X_motifs_scaled_reduced, y_motifs, rep_out, classify)
        decision_tree(X_motifs, y_motifs, X_features, rep_out)
    

 