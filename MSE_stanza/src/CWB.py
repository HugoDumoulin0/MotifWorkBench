import os

if not os.path.exists("./Data/cwb-corpus"):
    os.mkdir("./Data/cwb-corpus")

if not os.path.exists("./Data/cwb-corpus/registry"):
    os.mkdir("./Data/cwb-corpus/registry")

if not os.path.exists("./Data/cwb-corpus/data"):
    os.mkdir("./Data/cwb-corpus/data")

#types_textes = os.listdir("./Data/textes_raw")

#for type_texte in types_textes:
 #  if type_texte!=".DS_Store":
  #  	if not os.path.exists(f"./Data/cwb-corpus/data/{type_texte.lower()}"):
   #  	 	os.mkdir(f"./Data/cwb-corpus/data/{type_texte.lower()}")
#    	os.system(f"cwb-encode -f ./Data/Textes_tagged_stanza/{type_texte.lower()} -d ./Data/#cwb-corpus/data/{type_texte.lower()}/ -c utf8 -R ./Data/cwb-corpus/registry/{type_texte.lower()} -xsBC9 -N id -L s -P lemma -P upos -P xpos -P feats -P head -P deprel -P un #-P deux")

if not os.path.exists(f"./Data/cwb-corpus/data/merged"):
    	os.mkdir(f"./Data/cwb-corpus/data/merged")
os.system(f"cwb-encode -f ./Data/textesVRT/merged.vrt -d ./Data/cwb-corpus/data/merged/ -c utf8 -R ./Data/cwb-corpus/registry/merged -xsBC9 -N id -P lemma -P upos -P xpos -P feats -P head -P deprel -P deps -P misc -S text:0+id -S s:0+id")

#attention ! dans le registre les chemins vers les fichiers de données 
#seront notés avec un relative path ./Data/cwb-corpus/data/merged
#donc il faudra toujours lancer cqp depuis le même point de départ:
#exemple:
# cqp
# set Registry "./Data/cwb-corpus/registry";
# MERGED;
 