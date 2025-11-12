#-------------------
# stanza
#-------------------
download=False

specifs=False

#-------------------
# Mode
#-------------------
mode="server"
# mode="interface"


#-------------------
# Early specifs mode
#-------------------

earlySpecifs=False
seuil_early_specifs=200
partition_cible = "genre"
seuil_banalité=2
#early_pos4lemma=".*"  #toutes les pos possibles
early_pos4lemma = "ADJ|NOUN|VERB" #restriction aux mots lexicaux

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
list_minsup_percent = [25]

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
                 ,"test"
# 		,"genre"
                 #,"annee"
                 # ,"target"
                 ]

#-------------------
# Comparison with lemmas and pos
#-------------------
liste_seuils_lemma=[100,200]
#downhill_pos4lemma = ".*" #restriction pos 
downhill_pos4lemma="ADJ|ADV|NOUN|VERB" #restriction des lemma aux seuls mots_lexicaux
liste_seuils_bigrams = [100]

#-------------------
# Machine learning params
#-------------------
classification=False
path_target = "./Data/metadata.tsv"
y_class = "genre"
sampling=False  #équilibre les classes à l'échantillonnage 

