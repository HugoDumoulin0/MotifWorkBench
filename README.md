# MotifWorkBench

> This is a provisional README. It should be changed in the future.

Motif Work Bench is a textual data analysis software designed for the analysis of discursive routines using textual corpora. Situated within the field of discourse analysis, the design approach relies on the notion of motif, defined as a statistically significant linguistic sequence capable of carrying a discursive function characteristic of a particular genre. MWB aims to fill a gap in the state of the art: the lack of a tool bridging corpus-driven (Longrée & Vanni 2025) methods for the automatic extraction of sequential motifs with a multidimensional statistical framework (Lebart & Salem 1998) enabling their discursive interpretation.

Unlike corpus-based approaches that rely on pivot forms, MWB extracts all motifs that meet formal constraints (frequency, length, gap) among multidimensional sequential motifs (Mellet & Longrée 2012) comprising itemsets describing linguistic units (lemmas, morphosyntactic categories, dependency relations). This abstraction allows the grouping of formally diverse realizations, at the cost of sometimes reduced readability, which MWB accepts by considering any statistically relevant motif as valid from a contrastive perspective.

The pipeline relies on linguistic annotation using Stanza (Qi et al. 2020), motif extraction with the CloSPEC algorithm (Béchet et al. 2015) – also found in the SDMC software (Béchet et al. 2013) –, internal clustering aimed at reducing redundancy (Mekki 2022), and CWB indexing (Evert & Hardie 2011) to produce contingency tables that can be analyzed in R using statistical packages such as FactoMineR (Lê, Josse & Husson 2008) through a Shiny graphic user interface.

The CloSPEC algorithm (Béchet et al. 2015) can be find in the form of the binary file BideSpanTree. Some of the initial annotation, extraction and internal clustering scripts are based on the work of Mekki 2022.

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
- 3. Closed pattern mining with the CloSPEC / BideSpanTree algorithm
- 4. [optional] Clustering patterns
- 5. Computing multidimensional statistics with CQP and R
– 6.  Visualizing with shiny

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
–Béchet, N., Cellier, P., Charnois, T. & Crémilleux, B. (2015). Sequence mining under multiple constraints. In: Proceedings of the 30th Annual ACM Symposium on Applied Computing, 908-914. 
–Béchet, N., Cellier, P., Charnois, Th., Crémilleux, B. & Quiniou, S. (2013). « SDMC : un outil en ligne d'extraction de motifs séquentiels pour la fouille de textes ». Conférence Francophone sur l'Extraction et la Gestion des Connaissances (EGC'13), Jan 2013, Toulouse, France.
–Evert, Stefan and Hardie, Andrew (2011). Twenty-first century Corpus Workbench: Updating a query architecture for the new millennium. In Proceedings of the Corpus Linguistics 2011 conference, University of Birmingham, UK. 
–Kassambara Alboukadel, Mundt Fabian, «Factoextra – Extract and Visualize the Results of Multivariate Data Analyses», R package documentation, 2020.
–Lê Sébastien, Josse Julie, Husson François, "FactoMineR: an R package for multivariate analysis", Journal of statistical software 25, 2008, p.1-18.
–Lebart, L., & Salem, A. (1988). Analyse statistique des données textuelles. Dunod.
–Longrée, D. & Vanni, L. « Identification des motifs textuels. Entre statistique et deep learning », Corpus [En ligne], 27 | 2025, mis en ligne le 13 mai 2025, consulté le 16 mai 2025. URL : http://journals.openedition.org/corpus/10326 ; DOI : https://doi.org/10.4000/13woj 
–Mekki, J. (2022). Caractérisation de registres de langue par extraction de motifs séquentiels émergents. Thèse de doctorat, Université de Rennes. 
–Mellet, S. et Longrée, D. (2012). Légitimité d'une unité textométrique : le motif. In A. Dister, D. Longrée, G. Purnelle (éds.), Actes des Journée d'analyse des données textuelles 2012, 715-728. 

