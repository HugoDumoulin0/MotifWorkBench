# MSE_ArchivU

> This is a provisional README. It should be changed in the future.

MSE_ArchivU is part of the [ArchivU](https://archivu.hypotheses.org) project. The python script is based on scripts by Jade Mekki (2022).

It aims at detecting recurrent sequential patterns in textual data, comparing two or more subcorpora.
Two methods are available: Mekki (2022)'s method for emergent sequential patterns (French _Motifs Séquentiels Émergents_, MSE; using Growth Rate as a core measure), and Dumoulin, Premat and Diwersy's method using specificities (Lafon, 1980).

POs, lemma and dependency tagging is provided by Stanza (Qi _et al._, 2020), and word-pieces tagging by CamamBERT (Martin _et al._, 2020).

## How to use?
If all goes well, ```python src/main.py Subcorpus1 Subcorpus2``` should be enough. Just ```pip install``` whatever packages are needed.

In the previous command, ```Subcorpus1``` and ```Subcorpus2``` are the two corpora whose sequential patterns the script will compare.
There is no limit to the max number of subcorpus in arg of the command. Beware of computation time when working with very large and/or numerous subcorpora.

## What does it do?
A simple run such as the one before goes through the following operations:
- 0. Merging files (if one of the args is a directory containing more than one file)
- 1. Tagging
	- 1.1. through Stanza (except if ```.conllu``` files from previous run or already present) — this is time consuming, brace yourself with big corpora [1].
	- 1.2. through CamamBERT for word pieces, in the ```.conllu``` files from stanza (except if ```.conllu``` files from previous run or already present)
- 2. Extracting itemsets into DMT4 files
- 3. Pattern mining
- 4. Extracting patterns based on emergence or specificity [2]
- 5. [optional] Clustering emergent patterns
- 6. [optional] Extracting represent patterns
- 7. [optional] RandomForest : evaluate pattern quality as features as learning descriptors

Outputs of step (4) can be processed by the R script for CA analysis.

> [1] Stanza-produced .conllu files are modified so that they do not contain underscore. This is normal for a .conllu file (N/A value), but is not OK for mining pattern. As cols can't be empty, we chose to past the form in place of every underscore. This property is redundant, and should be always less stringent than lemma, so it should not introduce de bias in pattern mining.
> [2] Mekki's scripts compute Growth Rate of patterns. Dumoulin's ```compute_specifs.py``` computes specificity of patterns. One of the (practical) benefits of specificity is that it can compare more than two corpora in a robust manner. Here, the specificity indice of each pattern in each texts is computing by comparing _m_ the expected frequency of a pattern's supports (i.e., sentences comprising this pattern) with its actual frequency _k_ in each subcorpus. The expected frequency _m_ is obtained from the frequency of this pattern's support in the whole corpus (_t_) and the number of sentences in the whole corpus (_T_), considering the number of sentences in each text (_f_); see Lafon (1980).

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
