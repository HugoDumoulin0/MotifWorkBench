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
from sklearn.model_selection import GridSearchCV


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
def svm_train(X_motifs_scaled_reduced, y_motifs, rep_out):
    X_train, X_test, y_train, y_test, X_motifs_scaled_reduced, y_motifs = split_data(X_motifs_scaled_reduced, y_motifs)
    svm = LinearSVC()
    classify = svm.fit(X_train, y_train)

    y_pred = svm.predict(X_test)
    report = classification_report(y_test, y_pred)

    with open(f"{rep_out}svm_report.txt", "w") as f:
        f.write(report)
    
    return svm, classify

def svm_train_mean(X_motifs_scaled_reduced, y_motifs, rep_out):
    # X_train, X_test, y_train, y_test, X_motifs_scaled_reduced, y_motifs = split_data(X_motifs_scaled_reduced, y_motifs)
    svm = LinearSVC()
    # classify = svm.fit(X_motifs_scaled_reduced, y_motifs)
    report = cross_val_classification_report(
    model=svm,
    X=X_motifs_scaled_reduced,
    y=y_motifs,
    n_splits=5,
    n_repeats=10,
    random_state=50,
    # target_names=["class1","class2","and so on"]
)
    # y_pred = svm.predict(X_test)
    # report = classification_report(y_test, y_pred)
    
    # scores = cross_val_score(svm, X_train, y_train, scoring="f1_weighted", cv=5)
    # print("%0.2f f1_score with a standard deviation of %0.2f" % (scores.mean(), scores.std()))


    with open(f"{rep_out}svm_mean_report.txt", "w") as f:
        f.write(report)
        

    # from sklearn.model_selection import GridSearchCV

 #    create_grid = GridSearchCV(svm, param_grid=param_grid)
 #    create_grid.fit(X_train, Y_train)
 #    print ("score for %d fold CV := %3.2f" %(cv, create_grid.score(X_test, Y_test)))
 #    print ("!!!!!!!! Best-Fit Parameters From Training Data !!!!!!!!!!!!!!")
 #    print ("grid best params: ", create_grid.best_params_) 
    return svm

def svm_grid_search(X_motifs_scaled_reduced, y_motifs, rep_out):
     param_grid=[
   {'C': [1, 10, 100, 1000], 'kernel': ['linear']},
   {'C': [1, 10, 100, 1000], 'gamma': [0.001, 0.0001], 'kernel': ['rbf']},
  ]
     
     cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=50)
     
     grid_search = GridSearchCV(SVC(), param_grid, cv=cv, scoring='accuracy', n_jobs=-1, verbose=1)
     grid_search.fit(X_motifs_scaled_reduced, y_motifs)
     
     best_model = grid_search.best_estimator_
     best_params = grid_search.best_params_
     
     report = cross_val_classification_report(
        model=best_model,
        X=X_motifs_scaled_reduced,
        y=y_motifs,
        n_splits=5,
        n_repeats=10,
        random_state=50
    )
     
     with open(f"{rep_out}svm_best_model_report.txt", "w") as f:
         f.write(report)
    
     return best_model


def svm_plot_decision(svm, X_motifs_scaled_reduced, y_motifs, rep_out, classify):
    x_min, x_max = X_motifs_scaled_reduced[:, 0].min() - 1, X_motifs_scaled_reduced[:, 0].max() + 1
    y_min, y_max = X_motifs_scaled_reduced[:, 1].min() - 1, X_motifs_scaled_reduced[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.1),
                         np.arange(y_min, y_max, 0.1))
    grid = np.c_[xx.ravel(), yy.ravel()]
    Z = svm.predict(grid)
    
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
    plt.savefig(f"{rep_out}{svm}_plot.png", dpi=300, bbox_inches='tight')
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
    
    
def main(minsup, file_out_motifs, file_out_lemma, file_out_pos, path_target):
    path_classif_out = "./Patterns_results/Classifieurs/"
    if not os.path.exists(path_classif_out):
        os.mkdir(path_classif_out)
    path_classif_out += str(minsup)+"/"
    if not os.path.exists(path_classif_out):
        os.mkdir(path_classif_out)
    liste_prefixes = ["motifs/", "lemma/", "pos/"]
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
        svm = svm_train_mean(X_motifs_scaled_reduced, y_motifs, rep_out)
        best_model = svm_grid_search(X_motifs_scaled_reduced, y_motifs, rep_out)
        svm_plot_decision(best_model, X_motifs_scaled_reduced, y_motifs, rep_out, classify)

    

 