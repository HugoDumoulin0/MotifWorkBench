shortcut_association = True
shortcut_specifs = True
shortcut_GR = True
shortcut_underscore_fix=True
only_clustering = False
shortcut_wp = True
tagging=False
shortcut_grewpy = False

#-------------------
# Computation method
#-------------------
méthode = "partition"
# Two possible values:
    # - "partition", i.e. specificty computation for each partition of a corpus
    # - "corpus", i.e. growth rate computation for each corpus of a set of corpora
    # This sets the switch between two parallel paths in the script.

if méthode=="partition":
    shortcut_wp=True
    shortcut_GR = True

#-------------------
# Patterns params
#-------------------
#Set param for minimal number of itemsets in a pattern
nb_itemset_min = 3 #Tim, 27/02

#Set minimal frequency/ies for a pattern to be reccurrent
list_minsup_percent = [25,10]


#-------------------
# Patterns detection params
#-------------------
Form=False 
Lemma=True
Pos=True
Dep=True
Feats=False

#attention pour l'instant cela ne fonctionne qu'avec cette condition :
if Lemma==True or Pos==True or Dep==True:
    Lemma=True
    Pos=True
    Dep=True

