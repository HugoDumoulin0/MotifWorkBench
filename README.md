# MSE_ArchivU

> This is a provisional README. It should be changed in the future.

MSE_ArchivU is part of the [ArchivU](https://archivu.hypotheses.org) project. The python script is based on scripts by Jade Mekki (2022).

POs, lemma and dependency tagging is provided by Stanza (Qi _et al._, 2020)

## How to use?
If all goes well, ```python src/main.py``` should be enough. 

The script will work on all texts located into ```Data/textes_raw```. Texts must be in .txt formate, with one folder for each text.

Technical requirements are listed in ```src/requierements.txt```. In short, you'll need some libs + R + Perl + CWB.

## What does it do?
A simple run such as the one before goes through the following operations:
- 0. Merging files (if one of the args is a directory containing more than one file)
- 1. Tagging
	- 1.1. through Stanza (except if ```.conllu``` files from previous run or already present) — this is time consuming, brace yourself with big corpora [1].
- 2. Extracting itemsets into DMT4 files
- 3. Pattern mining
- 4. Extracting patterns based on emergence or specificity [2]
- 5. [optional] Clustering emergent patterns
- 6. [optional] Extracting represent patterns
- 7. [optional] RandomForest : evaluate pattern quality as features as learning descriptors

Outputs of step (4) can be processed by the R script for CA analysis.

> [1] Stanza-produced .conllu files are modified so that they do not contain underscore. This is normal for a .conllu file (N/A value), but is not OK for mining pattern. As cols can't be empty, we chose to replace underscores by random integers.

## Parameters
### Vocabulary
- itemset: a token of the pattern mining; in most cases, an itemset is a word.
- item: properties attached to an itemset, such as POS, lemma, etc.
- a pattern is therefore comprised of one or several itemsets.

### Number of itemsets in a pattern
By default, there is no minimum to the number of itemsets (tokens) that constitutes a pattern. In this case, a pattern could be one itemset (token), and it is the combination of its properties (items) that would be relevant for it to be an emergent or specific pattern. This, however, does not necessarily match the linguistic definition of a pattern.

The minimal number of itemsets required to form a pattern is defined by ```NB_ITEMSET_MIN```, instantiated as ```nb_itemset_min``` in ```main.py```. It can be edited in ```main.py```. Similarly, there is a possible limitation on the maximum number of itemsets, ```nb_itemset_max```; however this variable is not currently implemented (though it should not be too hard to implement it).

### Minsup
The variable called ```minsup``` defines the minimal frequency needed for a string of tokens to be recurrent enough in a text to be considered a pattern. It is measured by the absolute frequency of its support (number of sentences comprising this string of tokens). Our temporary default is ```25```.

### Gap in patterns
Variables ```GAPMIN``` and ```GAPMAX``` define the necessity/possibility of gaps in a pattern, i.e. the fact that an itemset not belonging to the pattern is present in the span of the pattern. Default is ```0```.

### More parameters
Other parameters are detailed in ```src/Prefixconstraint/README.txt```. These have not been tested with our implementation.

## References
- Lafon, Pierre (1980). "[Sur la variabilité de la fréquence des formes dans un corpus](https://doi.org/10.3406/mots.1980.1008)". In: _Mots_, (1), p. 127‑165.
- Martin, Louis, Benjamin Muller, Pedro Javier Ortiz Suárez, Yoann Dupont & Laurent Romary, Éric Villemonte de la Clergerie, Djamé Seddah, Benoît Sagot (2020). "[CamemBERT: a Tasty French Language Model](https://arxiv.org/pdf/1911.03894)". In: _Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics, July 2020_.
- Mekki, Jade (2022). _Caractérisation de registres de langue par extraction de motifs séquentiels émergent._ PhD Thesis, Rennes 1 University.
- Qi Peng, Yuhao Zhang, Yuhui Zhang, Jason Bolton & Christopher D. Manning (2020). "[Stanza: A Python Natural Language Processing Toolkit for Many Human Languages.](https://nlp.stanford.edu/pubs/qi2020stanza.pdf)" In: _Association for Computational Linguistics (ACL) System Demonstrations 2020_.
