  *******************************************
 **** Extracteurs de motifs séquentiels ****
*******************************************

Ces programmes sont des outils en ligne de commande permettant d'extraire des motifs séquentiels. Les exécutables ont été compilés sont une Ubuntu Linux 12.04 64 bits.
Contact : nicolas.bechet at irisa.fr

Auteur : Nicolas Béchet (IRISA Lab/UMR CNRS 6074 - Université Bretagne-Sud)
Autres contributeurs : 
Peggy Cellier (IRISA Lab/UMR CNRS 6074 - INSA de Rennes)
Thierry Charnois (LIPN Lab/UMR CNRS 7030 - Université Paris-Nord)
Bruno Crémilleux (GREYC Lab/UMR CNRS 6072 - Université de Caen Basse-Normandie)

Sommaire :
1. Introduction
2. Quelques définitions
3. Les différents outils
4. L'arborescence des outils
5. Les entrées/sorties
6. Les options des outils
7. Remarques diverses

-={ 1. Introduction }=-

Introduite par [Srikant et Agrawal, EDBT 1996], l'extraction de motifs séquentiels permet de découvrir des corrélations entre des événements selon une relation d'ordre (comme par exemple le temps).
Les outils proposés permettent l'extraction de motifs séquentiels de différentes natures, avec la particularité de fixer un certain nombre de contraintes comme des contraintes de temps ou des contraintes de longueur.
Ainsi, le jeu de données en entrée des outils est un jeu de séquences d’événements, sachant que plusieurs événements peuvent apparaître au même instant.

-={ 2. Quelques définitions }=-

En fouille de données séquentielles, un itemset, noté I = (i1 ... in ) est un ensemble de littéraux appelés items. Par exemple, (a b) est un itemset avec deux items a et b. 
Une séquence S est une liste ordonnée d’itemsets, notée s = I1 ... Im. Par exemple, (a) (a b c) (a c) (d) est une séquence de quatre itemsets. 
Une séquence S1 = I1 ... In est dite incluse dans une autre séquence S2 = I1 ... Im s’il existe des entiers 1 ≤ j1 < ... < jn ≤ m tels que Ij1 ,..., In ⊆ Ijn. La séquence S1 est alors appelée une sous-séquence de S2 , noté S1. Par exemple, (a)(a c) est incluse dans (a)(a b c)(a c)(d).
Une base de séquences, notée SDB, est un ensemble de tuples (sid, S), où sid est un identifiant de séquence, et S est une séquence. Un tuple (sid, S) contient une séquence S1 si S1 est inclus dans S. Le support d’une séquence S1 dans une base de données de séquences SDB, noté sup(S1), est le nombre de tuples de la SDB contenant S1. Par exemple, dans l’exemple 1, sup( (a b)(c) ) = 2, car les séquences 1 et 3 contiennent (a b)(c). Un motif séquentiel fréquent est un motif ayant un support supérieur ou égal à un certain seuil MINSUP.

-={ 3. Les différents outils }=-

I. SpeedBIDE

Permet l'extraction de motifs séquentiels fermés autour du support des motifs. Basé sur la recherche bi-directionnelle de motifs séquentiels pour le test de fermeture (BIDE - Wang et al. TKDE 2007) avec ajout de différentes contraintes. 

II. GapBIDE

Basé sur la recherche bi-directionnelle et la notion de sous-motifs contigus (GapBIDE - Li et al. SDM 2008) avec prise en compte des itemsets et ajout d'autres contraintes. La fermeture est calculée autour du support de manière contigus (cf. Li SDM 2008).

III. PrefixConstraint

Algorithme d'extraction de motifs séquentiels contraints, basé sur PrefixSpan (Pei et al. 2001) avec ajout de contraintes.

IV. BIDESpanTree

Algorithme d'extraction de motifs séquentiels fermés autour du support des motifs. Repose sur la recherche bi-directionnelle de motifs (BIDE) et l'utilisation d'une table de hachages pour l'élagage final des motifs séquentiels (CloSpan).

V. MaxSpanTree

Idem à VI. avec recherche des motifs séquentiels maximaux.

-={ 4. L'arborescence des outils }=-

Les outils sont organisés dans trois sous répertoires :
1) 'bin/'
2) 'config/'
3) 'src/'

1) Contient le fichier binaire de l'outil correspondant, ainsi qu'un dataset de test.
2) Contient le fichier 'Load.ini'. Ce fichier de configuration permet de gérer toutes les options des outils de fouilles de données séquentielles proposés. Par exemple, le chemin d'accès vers le corpus, le nombre de threads, etc.
3) Contient les sources des outils, avec un Makefile associé pour la compilation.

-={ 5. Les entrées/sorties }=-

I. Le dataset en entrée

Le dataset à fournir en entrée doit vérifier le format suivant (format de données issus de l'outil Dmt4SP, http://liris.cnrs.fr/~crigotti/dmt4sp) :
seqId SEQ_ID
DATE EVENT_TYPE
DATE EVENT_TYPE
...

soit par exemple :
seqId 1
1 1
2 1
2 2
2 3
3 1
3 3
seqId 2
1 1
1 4
2 3
3 2
3 3
4 1
Dans cet exemple, les séquences correspondantes sont :
S1 = <(1)(1 2 3)(1 3)>
S2 = <(1 4)(3)(2 3)(1)>

Le chemin d'accès à ce fichier doit être renseigné dans le fichier 'Load.ini' situé dans le répertoire 'config/' de la manière suivante :
-> en relatif, le corpus doit être dans le dossier 'bin/', sinon, adapter le chemin en conséquence, exemple :
CORPUS=exVigier.txt 
-> en absolut, exemple :
CORPUS=/home/becni/dataset/exVigier.txt 

II. Les sorties des extracteurs

Une fois un extracteur exécuté (./nom_extracteur), les motifs extraits sont affichés sur la sortie standard.
Le format de sortie est le suivant. Une séquence est affichée par ligne, un itemset est délimité par des accolades et les items sont les constituants des itemsets. Le support absolut est indiqué à la fin de chaque motifs séquentiels.

Par exemple :
{11 23} {12 4564} {97} : 2
{11} {5048 15258} {46176} : 3
{11} {23557} {9} : 4
{11} {23561} {9} {23558} : 2

-={ 6. Les options des outils }=-

I. Les contraintes

** Communes à tous les extracteurs **

- Contrainte de support minimal
Dans 'Load.ini', saisir par exemple :
MINSUP=2 -> pour n'extraire que des motifs dont le support sera supérieur ou égal à 2.

- Contrainte de Gap
La contrainte de Gap permet d'extraire des motifs séquentiels dont l'intervalle entre chaque itemset sera d'au moins GAPMIN itemsets et au maximum GAPMAX itemsets dans les séquences d'où ils sont issus.
Dans 'Load.ini', saisir par exemple respectivement (une option par ligne) :
GAPMIN=1
GAPMAX=3
pour un gap minimum de 1 et un gap maximal de 3. Un gap nul (tous les itemsets des motifs sont contigus dans les séquences du dataset) est obtenu pour une valeur de :
GAPMIN=0
GAPMAX=0

- Contrainte de longueur
Il s'agit du nombre minimal et maximal d'itemsets toléré pour chaque motif. Dans 'Load.ini', saisir par exemple respectivement (une option par ligne) :
NB_ITEMSET_MIN=4 (non fonctionnel dans l'algorithme I)
NB_ITEMSET_MAX=100
pour une taille minimale de 4 et une taille maximale de 100.

- Contrainte d'appartenance
[ET] Un et plusieurs items doivent être contenu dans les motifs extraits, ajout dans 'Load.ini' de :
IN=1,2 -> tous les motifs extraits contiendront les items (dans des itemsets différents) 1 ET 2
[OU] Un ou plusieurs items doivent être contenu dans les motifs extraits, ajout dans 'Load.ini' de :
OR=1,2 -> tous les motifs extraits contiendront les items (dans des itemsets différents) 1 OU 2

** Spécifique à l'extracteur I, SpeedBIDE **

- Contrainte de durée maximale
Le temps maximum entre le début et la fin d'un motif séquentiel, c'est à dire que le premier et le dernier itemset des motifs extraits ne doivent pas être séparés de plus de TIME_MAX itemsets dans les séquences d'où ils sont issus.
Dans 'Load.ini', ajouter :
TIME_MAX=10 -> pour une durée maximale de 10

- Contrainte d'association gauche
Tous les itemsets contenant les items mentionnés dans 'Load.ini' avec la contrainte OR doivent être composés d'au moins 2 items, avec un item qui précède celui mentionné dans 'OR'.
Dans 'Load.ini', pour n'extraire que des motifs contenant l'item '2' avec une association à gauche, saisir :
OR=2
OR_IS_ITEMSET=1
Ainsi, en sortie le motif '{1,2} {4} {3} : 2' est correct, mais pas le motif '{1} {2} : 4' car l'item '2' est seul dans son itemset, ni le motif '{1} {2,3} {1} : 2' car l'item '2' n'est pas précédé (à gauche) dans son itemset d'un autre item.

** Spécifique à l'extracteur IV, BIDESpanTree **

- Contrainte commence_par
Au moins un des items du premier itemset de chaque motif séquentiel extrait sera un de ceux mentionnés dans 'Load.ini' avec la contrainte OR.

Dans 'Load.ini', saisir par exemple :
IN=1
BEGINWITH=1
Ainsi, les motifs extraits aurons tous dans leur premier itemset l'item '1'.
Exemple : 
{1} {3} {3} : 3
{1,2} {4} {3} : 2
-> corrects
{4} {3} {2} : 2
{5} {1} {3} {2} : 2
-> incorrects

-={ 7. Remarques diverses }=-

I. Remarque sur le fichier 'Load.ini'

- Ce fichier doit TOUJOURS être situé dans 'config/' quelque soit le programme utilisé.
- Il n'y a pas d'ordre particulier pour la saisie des options dans ce fichier.
- On ne peut saisir qu'une option par lignes.
- L'ajout de commentaires est possible en débutant la ligne par un ';'.

II. Compilation des binaires.

Si besoin, vous pouvez compiler les binaires des programmes.
Placer vous dans le répertoire 'src/' d'un des outils, et saisissez dans une console :
make clean
make
L'exécutable est généré dans 'bin/'.

III. Le multithreading
Les exécutables II, III, IV et V utilise la librairie 'OpenMP' pour le multithreading.
Pour en bénéficier, ajouter par exemple dans 'Load.ini' :
THREAD=4 -> signifie que 4 threads seront créés, attention à ne pas mettre une valeur supérieur aux nombre de processeurs/cœurs dont dispose votre machine; Notez que le multithreading agmente significativement l'utilisation de mémoire vive lors de l'extraction des motifs séquentiels.
