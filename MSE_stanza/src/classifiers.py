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
def svm_train(X_motifs_scaled_reduced, y_motifs, rep_out, params):
    X_train, X_test, y_train, y_test, X_motifs_scaled_reduced, y_motifs = split_data(X_motifs_scaled_reduced, y_motifs)
    svm = SVC(**params)
    classify = svm.fit(X_train, y_train)

    y_pred = svm.predict(X_test)
    report = classification_report(y_test, y_pred)

    with open(f"{rep_out}svm_report.txt", "w") as f:
        f.write(report)
    
    return svm

# def svm_train_mean(X_motifs_scaled_reduced, y_motifs, rep_out):
#     svm = LinearSVC()
#     classify = svm.fit(X_motifs_scaled_reduced, y_motifs)
#     report = cross_val_classification_report(
#     model=svm,
#     X=X_motifs_scaled_reduced,
#     y=y_motifs,
#     n_splits=5,
#     n_repeats=10,
#     random_state=50,
# )
    # with open(f"{rep_out}svm_mean_report.txt", "w") as f:
    #     f.write(report)
        

    # from sklearn.model_selection import GridSearchCV

 #    create_grid = GridSearchCV(svm, param_grid=param_grid)
 #    create_grid.fit(X_train, Y_train)
 #    print ("score for %d fold CV := %3.2f" %(cv, create_grid.score(X_test, Y_test)))
 #    print ("!!!!!!!! Best-Fit Parameters From Training Data !!!!!!!!!!!!!!")
 #    print ("grid best params: ", create_grid.best_params_) 
    return svm

# def svm_grid_search(X_motifs_scaled_reduced, y_motifs, rep_out):
def svm_grid_search(X_motifs_scaled_reduced, y_motifs, rep_out):
     param_grid=[
    {'C': [1, 10, 100, 1000], 'kernel': ['linear']},
   # {'C': [10], 'kernel': ['linear']},
    {'C': [1, 10, 100, 1000], 'gamma': [0.001, 0.0001], 'kernel': ['rbf']},
   # {'C': [10], 'gamma': [0.001], 'kernel': ['rbf']},
  ]
     class_counts = pd.Series(y_motifs).value_counts()
     min_class_size = class_counts.min()
     n_splits=n_splits = min(5, min_class_size)
     n_repeats=10
     cv = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=50)
     
     total_combinations = len(list(ParameterGrid(param_grid)))
     total_fits = total_combinations * n_splits * n_repeats
     
     grid_search = GridSearchCV(SVC(), param_grid, cv=cv, scoring='accuracy', n_jobs=-1, verbose=1)
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


def svm_mini_plot_decision(svm, X_motifs_scaled_reduced, y_motifs, rep_out): #un plot de la svm mini permettant de visualiser les frontières en 2D 
    # for i in range(0,X_motifs_scaled_reduced.shape[1]):
    x_min, x_max = X_motifs_scaled_reduced[:, 0].min() - 1, X_motifs_scaled_reduced[:, 0].max() + 1
    y_min, y_max = X_motifs_scaled_reduced[:, 1].min() - 1, X_motifs_scaled_reduced[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.1),
                         np.arange(y_min, y_max, 0.1))
    grid = np.c_[xx.ravel(), yy.ravel()]
    
    Z = svm.predict(grid)
    # Z = svm.predict(X_motifs_scaled_reduced)
    
    le = LabelEncoder()
    le.fit(y_motifs)
    y_encoded = le.transform(y_motifs)
    # Z_encoded = le.fit_transform(Z)
    Z_encoded = le.transform(Z)
    Z_encoded = Z_encoded.reshape(xx.shape)
    
    
    plt.figure()
    plt.contourf(xx, yy, Z_encoded.reshape(xx.shape), alpha=0.8, cmap=plt.cm.coolwarm)
    scatter = plt.scatter(X_motifs_scaled_reduced[:, 0], X_motifs_scaled_reduced[:, 1], c=y_encoded, edgecolors='k', marker='o', cmap=plt.cm.coolwarm)
    plt.xlabel('Axe 1')
    plt.ylabel('Axe 2')
    plt.title('SVM Decision Boundary')
    
    
    handles, labels = scatter.legend_elements()
    
    plt.legend(handles, le.classes_, title="Classes", loc="best")
    plt.savefig(f"{rep_out}{svm}_mini_plot.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    
def svm_plot_decision_alt(svm, X_motifs_scaled_reduced, y_motifs, rep_out, nb_comp):##permet d'avoir une svm entraînée sur un nb_composantes principales > 2 et de plot sa projection sur 2D, par contre on a pas le contourf joli
     # 1. Créer les plages de valeurs pour chaque dimension (tu peux ajuster `num`)
    num = 5  # nombre de points par axe
    dim_ranges = [
        np.linspace(X_motifs_scaled_reduced[:, i].min() - 1, X_motifs_scaled_reduced[:, i].max() + 1, num=num)
        for i in range(nb_comp)
    ]
    
    # 2. Générer la grille 5D complète (produit cartésien)
    mesh = np.meshgrid(*dim_ranges)
    grid = np.array(mesh).T.reshape(-1, nb_comp)  # shape (n_points, 5)
    
    # 3. Prédiction sur la grille 5D
    Z = svm.predict(grid)
    # 4. Projeter les deux premières dimensions pour affichage
    x_plot = grid[:, 0]
    y_plot = grid[:, 1]
    
    # 5. Encoder les classes pour affichage couleur
    le = LabelEncoder()
    le.fit(y_motifs)                # apprendre toutes les classes possibles
    Z_encoded = le.transform(Z)    # transformer les prédictions
    y_encoded = le.transform(y_motifs)
    
    # 6. Visualisation (scatter, car grille non régulière en 2D)
    plt.figure(figsize=(8, 6))
    # scatter = plt.scatter(x_plot, y_plot, c=Z_encoded, cmap=plt.cm.coolwarm, alpha=0.6, s=30, edgecolors='k') #dégueu
    
    cmap = plt.cm.coolwarm
    n_classes = len(le.classes_)
    norm = Normalize(vmin=0, vmax=n_classes - 1)
    
    # Ajout des points d'entraînement projetés
    plt.scatter(X_motifs_scaled_reduced[:, 0], X_motifs_scaled_reduced[:, 1], c=y_encoded, edgecolor='white', cmap=cmap, norm=norm, marker='o', s=40)
    
    plt.xlabel('Axe 1')
    plt.ylabel('Axe 2')
    plt.title('SVM – frontière de décision (projection 2D des prédictions 5D)')
    
    # Légende
    for i, class_name in enumerate(le.classes_):
        plt.scatter([], [], color=cmap(norm(i)), label=class_name)
    plt.legend(title="Classes", loc="best")

    # Sauvegarde
    plt.savefig(f"{rep_out}{svm}_plot_alt.png", dpi=300, bbox_inches='tight')
    plt.close()


def importance(model, X_train, y_train, X_features, rep_out):### annulé car cela met en avant la forte contribution des premiers axes d'une ACP ce qui esttrivial et donc moyennement intéressant
    result = permutation_importance(model, X_train, y_train, n_repeats=30, random_state=42, n_jobs=-1)

# Les features les plus importantes
    sorted_idx = result.importances_mean.argsort()[::-1]
    top_n = min(10, len(X_features))
    with open(f"{rep_out}svm_best_model_report_features.txt", "w") as f:
        for i in sorted_idx[:top_n]:
            # importance = result.importances_mean[i]
            importance = result.importances[i]
            print(f"{X_features[i]}: {importance}")
            f.write(f"{X_features[i]}: {importance}\n")
    top_features = [X_features[i] for i in sorted_idx[:top_n]]
    # top_importances = result.importances_mean[sorted_idx[:top_n]]
    top_importances = result.importances[sorted_idx[:top_n]]
    plt.figure(figsize=(8, 5))
    plt.barh(top_features[::-1], top_importances[::-1])  # inverser pour top en haut
    plt.xlabel("Importance (permutation)")
    plt.title("Top 10 features")
    plt.tight_layout()
    plt.savefig(f"{rep_out}svm_best_model_report_top_10_features.svg", format="svg")
    print("SVG enregistré sous : top_10_features.svg")


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
    
    
def main(minsup, results, path_target, sampling,tidy_metadata):
    path_classif_out = "./Patterns_results/Classifieurs/"
    if not os.path.exists(path_classif_out):
        os.mkdir(path_classif_out)
    for prefixe,filename in results.items():
    # liste_prefixes = ["motifs/", "lemma/", "pos/", "20000lemma/", "20000bigrams"]
    # liste_data = [file_out_motifs, file_out_lemma, file_out_pos, file_out_ALLlemma]
    # for filename, prefixe in zip(liste_data, liste_prefixes):
        # if not os.path.exists(path_out):
        #     os.mkdir(path_out)
        # name = filename[:-4].replace(path_out, "")
        # if not prefixe in (f"{seuil_bigrams_comparison}bigramslemma"):
        print("classification : "+prefixe+"/n"+filename)
        if not ("lemma" in prefixe or "pos" in prefixe or "bigrams" in prefixe):
            if not os.path.exists(path_classif_out+"motifs/"):
                os.mkdir(path_classif_out+"motifs/")
            rep_pref=path_classif_out+f"motifs/{tidy_metadata}/"
            if not os.path.exists(rep_pref):
                os.mkdir(rep_pref)
            name = prefixe.split("motifs_")[1]
            rep_out = rep_pref+"minsup"+name+"/"
        else:
            rep_pref=path_classif_out+prefixe+"/"
            if not os.path.exists(rep_pref):
                os.mkdir(rep_pref)
            rep_out = rep_pref
            
        if not os.path.exists(rep_out):
            os.mkdir(rep_out)
        X_motifs, y_motifs, X_features= prepare_dataset(filename, rep_out, path_target, sampling)
        if len(X_motifs)>0:
            nb_comp=50
            X_motifs_scaled_reduced = PCA_transform(X_motifs, nb_comp, rep_out, X_features)
            decision_tree(X_motifs, y_motifs, X_features, rep_out)
            best_model, best_params = svm_grid_search(X_motifs_scaled_reduced, y_motifs, rep_out)
            
            # if nb_comp < 32:
            #     svm_plot_decision_alt(best_model, X_motifs_scaled_reduced, y_motifs, rep_out, nb_comp)
            # importance(best_model, X_motifs_scaled_reduced, y_motifs, X_features, rep_out)
        
            
            ###mini svm pour mini plot en 2D###
            nb_comp=2
            X_motifs_mini = PCA_transform(X_motifs, nb_comp, rep_out, X_features) 
            svm_mini = svm_train(X_motifs_mini, y_motifs, rep_out, best_params)
            svm_mini_plot_decision(svm_mini, X_motifs_mini, y_motifs, rep_out)# best_model est en 50D il y a un tru c à faire là 
    
    

    

 