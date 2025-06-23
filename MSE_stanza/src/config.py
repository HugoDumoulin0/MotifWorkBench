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
# Patterns params
#-------------------
#Set param for minimal number of itemsets in a pattern
nb_itemset_min = 3 #Tim, 27/02
gap_min = 0
gap_max = 0

#Set minimal frequency/ies for a pattern to be reccurrenxt
list_minsup_percent = [25, 10, 5]


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
# Machine learning params
#-------------------
path_target = "./Data/df_target_train_classif.tsv"
sampling=True  #équilibre les classes
classification=False
