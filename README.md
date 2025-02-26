# MSE_ArchivU

> This is a provisional README. It should be changed in the future.

MSE_ArchivU is part of the [ArchivU](https://archivu.hypotheses.org) project. The python script is based on scripts by Jade Mekki (2022).

It aims at detecting reccurrent sequential patterns in textual data, comparing two or more subcorpora.
Two methods are available: Mekki (2022)'s method for emergent sequential patterns (using Growth Rate), and Dumoulin, Premat and Diwersy's method using specificities.

Tagging is privded by Stanza, and word pieces by CamamBERT.

## How ot use
If all goes well, ```python src/main.py Subcorpus1 Subcorpus2``` should be enough. Just ```pip install``` whatever packages are needed. R is needed for better specificity computation.

## References
Mekki, Jade (2022). _Caractérisation de registres de langue par extraction de motifs séquentiels émergent._ PhD Thesis, Rennes 1 University.
