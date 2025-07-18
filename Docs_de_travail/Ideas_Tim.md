# Points à voir ensemble
- [ ] on a quoi comme MINSUP de référence ? On pourrait définir un truc 'standard' en fonction de notre expérience, et ensuite on le change quand on arrive sur un nouveau corpus.
    - ce serait intéressant que, dans un papier, on dise "par défaut, nous travaillons avec tels MINSUP et INTEMSET_MINSIZE, ça permettrait à d'autres de savoir de quel point de départ partir.
    - (dans le dernier pull de ta branche metadata_trick, les MINSUP sont très bas, en-dessous de 3. C'était pour une tâche précise, ou c'est notre nouvelle norme ?)
    - MINSUP très bas reste sur les lemmes
    - de manière standard, 24, 10, 5 c'est un bon point de départ pour toutes les features
    - pour les lemmes : 1, 0.5, 0.25
- [X] Requirements :
    - [X] scipy ?
    - [X] torch ?
- [ ] Je peux essayer de commenter/documenter le code pendant l'été, mais je n'ai pas une connaissance suffisante de tout le code pour ça.

- [ ] Multiprocessing pour l'extraction ?
    - De ce que je vois sur ma machine Linux, l'étape d'extraction des motifs clots ne fonctionne que sur un seul coeur à la fois (un monte à 100% puis redescent et alors un autre prend la relève)
    - Ça a l'air d'être le fonctionnement par défaut avec Python
    - Or il est possible de parser des processus pour utiliser en parallèle différents coeurs (p.ex. avec la lib. ```multiprocessing```). On pourrait lancer l'extraction pour chaque MINSUP dans un coeur différent et gagner beaucoup de temps ?
        - Tim regarde
    - il y a aussi l'option du multithreading (exécution parallèle dans le même process = dans le même coeur ?), python ne le faisait pas par défaut non plus. Mais puisque nos machines ont toujours plus de coeurs que de MINSUP qu'on calcule (enfin, jusqu'à présent), je me dis qu'on peut y aller avec un marteau et passer directement au multiprocessing...

# TODO
(transférer ici des points de supra après validation)
- [ ] renommer train machin en metadata
- [ ] passer la sélection de la métadonnée pour les specif en config
- [ ] Chantiers R ?
    - [ ] Tim : apprendre à utiliser la fonction qu'utilisait Sascha et qui permettait d'appeler des commandes R en tant que commandes python (plutôt que de lancer R dans Python) ?
    - [ ] Réécriture du code R pour les spécifs ? Jusque là je n'ai fait qu'adapter de manière fonctionnelle le code de Sascha, mais on a vu qu'on ne comprenait pas tout dans ce code... Et il y a des lignes franchement mystérieuses !
    - [ ] doute sur le fait que le script calcule les bonnes choses, on a des résultats vraiment perturbants.
- [ ] dans CQP_main.py, mettre des FUS dans un dossier FUS, pour avoir R_internal et R_external, et passer les choix en config si internal_clustering=TRUE
- [ ] On essaie de rétablir l'extension des conllu ? Ça me semble pas une bonne pratique de laisser des fichiers sans extension comme ça (cf. pb. de reconnaissance des fichiers sur Mac + impossibilité de gitignore them + pas une bonne idée en général, non ?)
- [ ] On a encore besoin de l'architecture des dossiers pour les textes ? Pourquoi est-ce qu'on ne pourrait pas juste avoir les textes en vrac dans chaque dossier ?
- [ ] Tester le multiprocessing (Tim)

# Remarques random
- Les extracteurs ne font pas le multithreading ? Sur ma machine Linux, un coeur monte à 100%, puis un autre alors que le premier redescent, etc.
- Avec les MINSUP très bas de ce pull, j'ai systématiquement ```No closed patterns removed```, tu valides que c'est une possibilité théorique qu'on n'avait pas forcément rencontrée/remarquée jusqu'à présent ?
- early specif = calcul des specifs en fonction des paramètres de metadata. Avec un paramètre de seuil dans les config.