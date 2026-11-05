# Correction de l'alignement du clustering interne

Branche : `internal_clustering_correcAlignement`, creee directement depuis `main`.
La fusion des frequences reste une somme, comme sur `main`. L'essai des moyennes
est conserve dans le stash nomme `internal-clustering-mean: experiment saved
before alignment fix` ; il n'est pas inclus dans cette branche.

## Probleme reproduit

Deux motifs differant seulement par la precision du deuxieme itemset :

```text
A = {punct, ''} {punct}    {nsubj} {ROOT} {punct}
B = {punct, ''} {punct, ,} {nsubj} {ROOT} {punct}
```

L'ancien alignement de A vers B etait `0->0, 1->4, 2->2, 3->3, 4->5`.
L'indice 5 est hors limites. L'exception etait masquee et convertie en score 0,
alors que la comparaison inverse donnait 0.933333. Le seuil de regroupement 0.50
separait donc les motifs selon l'ordre de traitement.

## Proposition implementee

L'heuristique gloutonne et sa resolution locale des conflits sont remplacees par
un alignement global par programmation dynamique, commun aux trois plateformes :

- chaque position est utilisee au plus une fois ;
- les correspondances conservent l'ordre des itemsets ;
- seules les paires partageant un item peuvent etre associees ;
- la somme des similarites Dice des paires est maximale ;
- a poids egal, davantage de paires puis des positions plus proches sont preferees ;
- les deux orientations sont evaluees, puis la meilleure coherence d'espacement
  departage les alignements obtenus ;
- a score final egal, une orientation canonique garantit le meme alignement
  inverse, sans rendre la similarite dependante des identifiants du lexique.

Le calcul coute O(longueur A * longueur B) en temps et en memoire. Il accepte des
longueurs variables et des positions non associees. Il ne segmente pas le corpus
et n'impose aucune contrainte de non-chevauchement aux occurrences.

Il s'agit d'une variante ordonnee de l'implementation S2MP, pas seulement de la
correction d'un decalage d'indice : les croisements sont desormais exclus.
Des scores et des clusters autres que le couple signale peuvent donc changer.

Le poids moyen des paires est multiplie par leur couverture des deux motifs et
par un facteur de coherence de leurs espacements. Les longueurs des deux motifs
interviennent dans la normalisation. La penalite d'espacement utilise la valeur
absolue des differences entre les distances des positions associees dans les deux
motifs. Le facteur final est borne inferieurement a zero. Les motifs sans paire
compatible ont un score nul ; une erreur de programmation n'est plus convertie
silencieusement en score nul. Le score final est symetrique et compris entre 0 et 1.

Pour A et B, l'alignement devient `0->0, 1->1, 2->2, 3->3, 4->4` et le score vaut
14/15, soit 0.933333, dans les deux sens. Le seuil existant reste inchange.

## Relancer l'essai

Quitter puis relancer MWB sur cette branche avec le clustering interne active.
La GUI inscrit `internal_clustering_alignment = ordered-dice-v1` dans la
configuration avant la recherche d'une analyse existante. Les anciennes analyses
sans ce marqueur ne sont pas reutilisees : clusters, matrices fusionnees et
resultats Shiny sont recalcules dans une nouvelle analyse. Les anciennes analyses
restent disponibles. Les relances avec cette version peuvent reutiliser leur cache.
Les analyses sans clustering ne recoivent pas ce marqueur.

Pour un appel direct aux fonctions hors GUI, utiliser un nouveau dossier de
resultats : les anciens fichiers de clusters ne portent pas de version interne.
Relancer Shiny avec le JSON de la nouvelle analyse pour voir les nouveaux groupes.

## Verification

```bash
python3 -B -m unittest discover -s tests -v
```

Les tests couvrent les trois plateformes, le couple signale, les repetitions,
les motifs vides et disjoints, les longueurs differentes, les insertions, les
alignements partiels et les inversions d'ordre. Une enumeration exhaustive de
petits motifs verifie l'optimalite du poids et les invariants d'alignement. Le
premier regroupement est teste dans les deux ordres pour le couple signale. Les
tests du worker verifient que la version du calcul est prise en compte avant la
recherche du cache. Ils ne lancent ni CQP ni l'interface graphique.

Un rejeu des trois passes, avec des pools sequentiels et des fichiers temporaires,
sur les 288 motifs du dernier run donne 12 clusters contre 38 dans les anciens
resultats. Les deux motifs signales sont dans le meme groupe aux trois passes.
Chaque motif est conserve exactement une fois et chaque medoide appartient a son
cluster. Cette verification ne remplace pas une execution complete de l'interface.
