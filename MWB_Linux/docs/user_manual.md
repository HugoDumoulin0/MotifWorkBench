# Manuel d'utilisation — MotifWorkBench

## 1. À quoi sert MotifWorkBench ?

MotifWorkBench aide à :

- préparer un corpus de textes ;
- lancer des analyses de motifs séquentiels ;
- comparer des partitions de corpus à l'aide de métadonnées ;
- calculer des spécificités ;
- explorer les résultats dans Shiny et dans le concordancier.

L'application est pensée pour accompagner tout le flux de travail, depuis la préparation des données jusqu'à l'interprétation des motifs en contexte.

## 2. Parcours conseillé

Si vous débutez, suivez cet ordre :

1. préparer le corpus ;
2. vérifier ou ajouter les métadonnées ;
3. régler l'analyse ;
4. lancer un premier test sur un petit corpus ;
5. consulter les tableaux et graphiques dans Shiny ;
6. vérifier les occurrences dans le concordancier ;
7. ajuster les réglages et relancer si besoin.

## 3. Préparer le corpus

Avant de lancer l'analyse :

- regroupez les textes dans un dossier propre ;
- vérifiez que les fichiers sont lisibles et bien encodés ;
- évitez de mélanger des corpus de nature très différente dans un premier test ;
- préparez si besoin des métadonnées comme `id`, `genre`, `auteur`, `période`, `source`.

### Bonnes pratiques

- Commencez avec peu de textes pour valider le pipeline.
- Utilisez des noms de fichiers stables et explicites.
- Vérifiez que les métadonnées importantes sont bien renseignées avant l'analyse.

## 4. Première analyse pas à pas

Pour une première prise en main :

1. ouvrez la page `Réglages` ;
2. gardez des paramètres simples ;
3. activez seulement les options utiles ;
4. ouvrez la page `Analyse` ;
5. vérifiez le résumé de configuration ;
6. lancez l'analyse ;
7. attendez la fin complète du traitement ;
8. ouvrez la page `Résultats` puis le `Concordancier`.

### Réglages prudents pour commencer

- un `minsup` modéré ;
- des `gap min` et `gap max` simples ;
- un `itemset min` faible ;
- peu de représentations linguistiques à la fois ;
- spécificités activées seulement si vous avez une métadonnée contrastive utile.

## 5. Régler l'analyse

Dans la page `Réglages`, vous pouvez notamment :

- choisir les représentations linguistiques ;
- activer ou non les motifs ;
- ajuster `minsup`, `gap min`, `gap max`, `itemset min` ;
- activer les spécificités ;
- choisir une liste de lemmes manuelle ;
- activer le clustering interne ;
- contrôler certains réglages de performance.

### Glossaire des paramètres

- `minsup` : support minimal des motifs, exprimé en pourcentage des séquences. Plus il est bas, plus l'extraction est permissive.
- `gap min` : distance minimale entre deux itemsets consécutifs d'un motif. Une valeur supérieure à 0 impose une discontinuité.
- `gap max` : distance maximale autorisée entre deux itemsets consécutifs d'un motif. Une valeur élevée autorise des motifs plus souples.
- `itemset min` : longueur minimale d'un motif en nombre d'itemsets. Plus la valeur monte, plus les motifs retenus sont longs.
- `threads` : nombre de cœurs CPU utilisés pour certaines étapes de calcul. Augmenter cette valeur peut accélérer l'analyse si la machine le permet.
- `lemmes` : représentation fondée sur les formes lemmatisées des mots. Utile pour regrouper des variantes fléchies.
- `formes` : représentation fondée sur les formes brutes observées dans le corpus. Plus fine, mais souvent plus dispersée.
- `POS` : catégories grammaticales (`NOUN`, `VERB`, etc.). Permet de travailler sur des schémas morphosyntaxiques.
- `dépendances` : informations syntaxiques de type relation de dépendance (`nsubj`, `obj`, `prep`, etc.).
- `feats` : traits morphologiques disponibles dans l'annotation (genre, nombre, temps, etc.).
- `early selection` : filtrage préalable qui réduit le nombre d'éléments étudiés avant la fouille de motifs.
- `liste de lemmes manuelle` : liste imposée par l'utilisateur pour cibler certains lemmes, indépendamment de l'early selection.
- `clustering interne` : fusion de motifs proches après extraction, afin de réduire la redondance et d'obtenir des tableaux plus lisibles.
- `spécificités` : calcul statistique mesurant la sur- ou sous-représentation d'un motif dans une partition donnée.
- `métadonnée contrastive` : colonne utilisée pour comparer des groupes de textes, comme `genre`, `auteur` ou `période`.

### Conseils de réglage

- Si vous obtenez trop peu de motifs, baissez légèrement `minsup`.
- Si vous obtenez trop de motifs, augmentez `minsup` ou `itemset min`.
- Si les motifs sont trop rigides, assouplissez `gap max`.
- Si les tableaux deviennent trop difficiles à lire, activez le clustering interne.

## 6. Lancer l'analyse

Depuis la page `Analyse` :

- vérifiez le résumé de configuration ;
- surveillez le niveau de verbosité et les logs ;
- lancez l'analyse ;
- attendez que toutes les étapes se terminent ;
- notez le dossier de sortie si vous voulez retrouver rapidement les fichiers produits.

Si le corpus est nouveau, l'application peut aussi proposer d'exporter un ZIP avec les textes annotés.

### Pendant l'exécution

Les logs peuvent vous aider à comprendre :

- quelle étape est en cours ;
- si un calcul est réutilisé ;
- si un fichier attendu est manquant ;
- si une option produit un volume de sortie important.

## 7. Lire les résultats

### 7.1 Résultats Shiny

L'interface Shiny permet de :

- visualiser les tableaux de contingence ;
- consulter les tables de spécificités ;
- afficher les graphiques d'AFC et de contribution ;
- comparer les sorties selon les métadonnées et les paramètres ;
- vérifier si les éléments étudiés sont des motifs.

### 7.2 Concordancier

Le concordancier permet :

- de chercher un mot, un lemme, une catégorie grammaticale ou un motif ;
- d'afficher soit le motif abstrait, soit les mots trouvés ;
- de relire les occurrences en contexte ;
- de filtrer les résultats avec les métadonnées disponibles.

### 7.3 Comment interpréter un motif

Pour interpréter un motif :

1. repérez sa place dans le tableau ou dans les spécificités ;
2. observez dans quelle partition il est fréquent ou spécifique ;
3. ouvrez-le dans le concordancier ;
4. vérifiez plusieurs occurrences réelles ;
5. confrontez l'observation linguistique au contexte des textes.

## 8. Fichiers et dossiers utiles

Les sorties sont généralement réparties entre plusieurs emplacements :

- `logs` : journaux d'exécution, exports techniques, traces utiles pour le diagnostic ;
- `Data/analyses` : dossiers d'analyses successives ;
- `Patterns_results` : tableaux et sorties principales ;
- `Clustering_results` : résultats liés au clustering ;
- `docs` : documentation et manuel.

### À retenir

Si vous cherchez un résultat précis, commencez souvent par :

- le dernier dossier d'analyse ;
- `logs/last_results_for_shiny.json` ;
- les sous-dossiers `Patterns_results` et `Specifs`.

## 9. Problèmes fréquents

### Shiny n'affiche rien

Vérifiez que :

- l'analyse est terminée ;
- les fichiers TSV existent bien ;
- le dernier export Shiny pointe vers des chemins valides ;
- vous avez ouvert le bon jeu de résultats.

### Le registry CWB est introuvable

Relancez une analyse complète si le corpus indexé n'existe plus ou si le dossier d'analyse a été déplacé.

### Les spécificités n'apparaissent pas

Vérifiez que :

- l'option est activée ;
- une métadonnée contrastive pertinente est disponible ;
- les fichiers du dossier `Specifs` ont bien été générés.

### Le concordancier ne montre pas ce que j'attends

Vérifiez :

- le mode d'affichage choisi (`motif` ou `mots trouvés`) ;
- le motif sélectionné ;
- le registry utilisé ;
- la cohérence entre le résultat affiché et le corpus analysé.

### Il y a trop de résultats

Essayez de :

- monter `minsup` ;
- augmenter `itemset min` ;
- restreindre les représentations ;
- travailler d'abord sur un sous-corpus.

## 10. Conseils pour travailler confortablement

- Sauvegardez plusieurs profils de configuration.
- Gardez un réglage de base simple pour comparaison.
- Relisez les motifs en contexte avant de conclure.
- Utilisez les spécificités pour guider l'interprétation, pas pour remplacer la lecture qualitative.
- Revenez souvent aux logs si un résultat semble surprenant.

