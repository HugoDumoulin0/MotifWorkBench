#-------------------
# stanza
#-------------------
download=False


# tagging=True
# shortcut_underscore_fix=True
# shortcut_DMT4=True
# shortcut_extract = True
only_clustering = False
shortcut_association = True
shortcut_specifs = True
specifs=False


GrowthRate = False
wordpieces = False
#-------------------
# Computation method
#-------------------
méthode = "partition"
# Two possible values:
    # - "partition", i.e. specificty computation for each partition of a corpus
    # - "corpus", i.e. growth rate computation for each corpus of a set of corpora
    # This sets the switch between two parallel paths in the script.

if méthode=="partition":
    wordpieces=False
    GrowthRate = False

#-------------------
# Early specifs mode
#-------------------

earlySpecifs=False
seuil_early_specifs=1000
partition_cible = "target"
seuil_banalité=2

user_input_list=False
liste_earlyspecifs_lemma = ["président", "comité", "formation"]
    
    

#-------------------
# Internal clustering
#-------------------
internal_clustering=True


#-------------------
# Patterns params
#-------------------
#Set param for minimal number of itemsets in a pattern
list_itemset_min = [3] 
list_gap_min = [0]
list_gap_max = [0]

#Set minimal frequency/ies for a pattern to be reccurrenxt
list_minsup_percent = [1]

threads=30

#-------------------
# Patterns detection params
#-------------------
Form=False 
Lemma=True
Pos=True
Dep=True
Feats=False

#attention avec form=True il y a aura les résultats non contractés
#-------------------
# Metadata
#-------------------
path_metadata = "./Data/metadata.tsv"
list_metadata = ["id"
                 #,"annee"
                 # ,"target"
                 ]

#-------------------
# Comparison with lemmas and pos
#-------------------
liste_seuils_lemma=[100,200]
seuil_bigrams_comparison = 100

#-------------------
# Machine learning params
#-------------------
path_target = "./Data/metadata.tsv"
sampling=True  #équilibre les classes
classification=False
# seuil_lemma_comparaison = 1000
