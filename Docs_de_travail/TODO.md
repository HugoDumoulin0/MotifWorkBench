# TODO
Todo liste générale du projet, cocher les cases quand c'est fait. Se substitue à la todo du doc _IdeasTim_.

## Code
- [ ] passer la sélection de la métadonnée pour les specif en config
    - à cocher ? Tu l'as complètement implémenté pendant la réunion, Hugo, ou seulement partiellement ?
- [ ] Chantiers R (Tim)
    - [ ] ***Prioritaire :*** se plonger dans le code R des spécifs, le commenter, le simplifier si possible, et vérifier les calculs.  
    - [ ] _Facultatif/non prioritaire_ : apprendre à utiliser la fonction qu'utilisait Sascha et qui permettait d'appeler des commandes R en tant que commandes python (plutôt que de lancer R dans Python)
- [ ] dans CQP_main.py, mettre des FUS dans un dossier FUS, pour avoir R_internal et R_external, et passer les choix en config si internal_clustering=TRUE
- [ ] Système de fichiers :
    - [ ] Rétablir l'extension ```.conllu```
    - [ ] Supprimer la structure avec un dossier par fichier
        - (ce qui, d'ailleurs, lèverait le problème des extensions, qui avaient été supprimée pour avoir correspondance exacte entre nom de dossier et nom de fichier)
- [X] Requirements :
    - [X] scipy ?
    - [X] torch ?
- [ ] Performance :
    - [X] Multithreading
    - [ ] Multiprocessing : Tim, regarder comment mettre ça en place pour les extracteurs (et le clustering si encapsulé en parallèle).
- [ ] Préparation du code pour diffusion :
    - [ ] Nettoyer et commenter le code pour diffusion
        - [ ] Dont renommer toutes les variables en anglais pour avoir un usage homogène
    - [ ] Compléter/réécrire le README.md, en ajoutant une section _human-readable_ sur les prérequis (R, Perl, CWB::CQP)

## Recherche
- [ ] Comparer performance et résultats avec les packages de Legallois
- [ ] Vérifier 