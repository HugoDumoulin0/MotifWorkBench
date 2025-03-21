# DMT4 index out of range
Error type:
```
Traceback (most recent call last):
  File ".../src/main.py", line 122, in <module>
    conll_dmt4.instancier_dict("./Data/Textes_tagged_WP/")
  File ".../src/conll_dmt4.py", line 59, in instancier_dict
    dep = "dep_{}".format(tokens[8])
IndexError: list index out of range
```
This probably means that there is an encoding error in one of the ```.conllu``` files. Common sources are # and " characters, than are not read as literal in a ConllU.
Track down the problematic character by looking where a row has less than 8 cols, then add the trouble maker to the sed statements in ```merge_corpus.py```.

Beware: this can also come from a previous DMT4 file: when building the general dictionary, the script reads _all_ DMT4 files available.
- Update 24-02: scripts now delete all DMT4 files before attempting to build the general dictionary.

# File do not exist for a data file not in sys.argv
As of 19/03/2025, this error could arise right after Stanza called. Setting ```tagging=TRUE``` in ```config.py``` should temporarily fix it.

> Hugo, je ne comprends pas d'où ça vient. Je crois que tu avais temporairement changé le script pour utiliser tous les fichiers d'un rep au lieu des sys.argv ; j'ai changé ça en tête du main.py (en rétablissant type_textes = sys.argv[1:]), mais apparemment ça continue à le faire ailleurs...

- ***This error should be taken care of in a sustainable maner (temp fix not acceptable here)***
