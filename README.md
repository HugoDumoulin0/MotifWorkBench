# MotifWorkBench

Motif Work Bench is a textual data analysis software designed for the analysis of discursive routines using textual corpora. Situated within the field of discourse analysis, the design approach relies on the notion of motif, defined as a statistically significant linguistic sequence capable of carrying a discursive function characteristic of a particular genre. MWB aims to fill a gap in the state of the art: the lack of a tool bridging corpus-driven (Longrée & Vanni 2025) methods for the automatic extraction of sequential motifs with a multidimensional statistical framework (Lebart & Salem 1998) enabling their discursive interpretation.

Unlike corpus-based approaches that rely on pivot forms, MWB extracts all motifs that meet formal constraints (frequency, length, gap) among multidimensional sequential motifs (Mellet & Longrée 2012) comprising itemsets describing linguistic units (lemmas, morphosyntactic categories, dependency relations). This abstraction allows the grouping of formally diverse realizations, at the cost of sometimes reduced readability, which MWB accepts by considering any statistically relevant motif as valid from a contrastive perspective.

The pipeline relies on linguistic annotation using Stanza (Qi et al. 2020), motif extraction with the CloSPEC algorithm (Béchet et al. 2015) – also found in the SDMC software (Béchet et al. 2013) –, internal clustering aimed at reducing redundancy (Mekki 2022), and CWB indexing (Evert & Hardie 2011) to produce contingency tables that can be analyzed in R using statistical packages such as FactoMineR (Lê, Josse & Husson 2008) through a Shiny graphic user interface.

The CloSPEC algorithm (Béchet et al. 2015) can be found in the form of the binary file BideSpanTree. Some of the initial annotation, extraction and internal clustering scripts are based on the work of Mekki 2022.

## How to use?
Run: 
```bash
python src/main.py
```

The script will process all `.txt` files located into ```Data/textes_raw```. The textometric part of MWB needs a `metadata.tsv` file relating to its corpus texts (see textometric settings below).

## How to cite?
If you like (or really hate) this work, please use the following citation:
> Dumoulin, Hugo and Premat, Timothée (2026). The Motif Work Bench Pipeline: From Sequential Pattern Mining to Multidimensional Statistics. JADT 2026. Scripts at: [https://github.com/HugoDumoulin0/MotifWorkBench](https://github.com/HugoDumoulin0/MotifWorkBench)

## Requirements
MWB needs Python, R, Perl, CWB and bash. On Mac OS, Docker is needed to run the Linux binaries of BideSpanTree motif extractor (see ```execute_closed_pattern.sh```).
- Python requirements are listed in ```src/requirements.txt```
- R packages are automatically downloaded if not installed, and loaded
- [CWB download page](https://cwb.sourceforge.io/install.php)
- [Perl download page](https://www.perl.org/get.html)

On Mac OS, the following should work:
```bash
# Install Perl
curl -L https://xrl.us/installperlosx | bash

# Install base CWB (with brew)
brew install cwb

# Install Perl CQP command from CWB (with cpan)
cpan
install CWB::CQP
```

## What does it do?
A simple run such as the one before goes through the following operations:

1. Tagging and processing text files
	- MWB runs Stanza (except if ```.conllu``` files from previous run or already present) — this is time consuming, brace yourself with big corpora [^1].
2. Extracting itemsets into DMT4 files
3. Closed pattern mining with the CloSPEC / BideSpanTree algorithm
4. [optional] Clustering patterns
5. Computing multidimensional statistics with CQP and R
6. Visualizing with Shiny GUI

[^1]: Stanza-produced `.conllu` files are modified so that they do not contain underscore (this is what MWB calls `underscore-fixing`). While it is normal for `.conllu` files to contains underscores, this is not suitable for pattern mining. As cols can't be empty, we chose to replace underscores by random integers.

## Parameters
### Vocabulary
- itemset: a token of the pattern mining; in most cases, an itemset is a word.
- item: properties attached to an itemset, such as POS, lemma, etc.
- a motif contains one or several itemsets, each containing one or several items.

Basic parameters are accessible in `config.py` and through a Shiny graphic interface.

### Pattern mining settings
Most notable pattern mining parameters used in MWB are:
- `itemset_min`: the minimal number of itemsets (tokens) required to form a motif.
- `minsup`: the frequency threshold for a string to be considered a motif.
	- On small corpora, if no motifs are produced, try lowering the `minsup`
- `gapmin` and `gapmax`: minimal and maximal size of gap in the motifs.
	- With `gapmax == 1`, motifs can contain one exogeneous token (i.e. one token irrelevant to the statistical qualification of the motif); with `gapmin == 1`, motifs must contain exogeneous token.
The above parameters takes one or several numerical values.

### Motif representation settings
- Motifs representation is regulated by the following booleans:
 - `Forms == TRUE` use column `Form` of the `.conllu` files as items 
 - `Lemma` _idem_
 - `Pos` _idem_
 - `Dep` _idem_
 - `Feats` _idem_
 - `ìnternal_clustering`: if `TRUE`, MWB peforms a clustering of motifs before sending them to the textometrical analysis (makes CA computation way faster)

### Textometric settings
- `early_specifs`: if `TRUE`, MWB performs a prefiltering of motifs based on specific vocabulary (Lafon 1980). In this case, only motifs comprising at least one specific token will be mined. Early specificity filtering requires the following arguments:
 - `target_subcorpus`: column of `metadata.tsv` used to split the corpus in contrastive subcorpora
 - `triviality_treshold`: threshold for positive and negative specificity (default value is 2)
 - `early_pos4lemma`: Parts of Speech defining the lemmas whose specificity is calculated. If several values, enter them separated by a pipe `|`, e.g. `ADJ|NOUN|VERB`

Finally, the textometric and visualisation approach rely on a metadata file: `metadata.tsv`. Its address can be changed by changing the value of `path_metadata == "./Data/metadata.tsv"`. The columns to use for spliting the data in contrastive subcorpora is `list_metadata`. Classically, the metadata file have a first column `id` containing the name of each texts, and additional columns containing various qualification of the texts. If your texts does not match the file `metadata.tsv` and/or the values passed to `list_metadata`, the textometric approach will not work.

## References
- Béchet, N., Cellier, P., Charnois, T. & Crémilleux, B. (2015). Sequence mining under multiple constraints. In: Proceedings of the 30th Annual ACM Symposium on Applied Computing, 908-914. 
- Béchet, N., Cellier, P., Charnois, Th., Crémilleux, B. & Quiniou, S. (2013). « SDMC : un outil en ligne d'extraction de motifs séquentiels pour la fouille de textes ». Conférence Francophone sur l'Extraction et la Gestion des Connaissances (EGC'13), Jan 2013, Toulouse, France.
- Dumoulin, Hugo and Premat, Timothée (2026). The Motif Work Bench Pipeline: From Sequential Pattern Mining to Multidimensional Statistics. JADT 2026.
- Evert, Stefan and Hardie, Andrew (2011). Twenty-first century Corpus Workbench: Updating a query architecture for the new millennium. In Proceedings of the Corpus Linguistics 2011 conference, University of Birmingham, UK. 
- Kassambara Alboukadel, Mundt Fabian, «Factoextra – Extract and Visualize the Results of Multivariate Data Analyses», R package documentation, 2020.
- Lê Sébastien, Josse Julie, Husson François, "FactoMineR: an R package for multivariate analysis", Journal of statistical software 25, 2008, p.1-18.
- Lebart, L., & Salem, A. (1988). Analyse statistique des données textuelles. Dunod.
- Longrée, D. & Vanni, L. « Identification des motifs textuels. Entre statistique et deep learning », Corpus [En ligne], 27 | 2025, mis en ligne le 13 mai 2025, consulté le 16 mai 2025. URL : http://journals.openedition.org/corpus/10326 ; DOI : https://doi.org/10.4000/13woj 
- Mekki, J. (2022). Caractérisation de registres de langue par extraction de motifs séquentiels émergents. Thèse de doctorat, Université de Rennes. 
- Mellet, S. et Longrée, D. (2012). Légitimité d'une unité textométrique : le motif. In A. Dister, D. Longrée, G. Purnelle (éds.), Actes des Journée d'analyse des données textuelles 2012, 715-728. 

