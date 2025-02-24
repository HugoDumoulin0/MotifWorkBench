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
This probably means that there is an encoding error in one of the ```.conllu``` files. Common sources are # and " characters, than are not read as litteral in a ConllU.
Track down the problematic character by looking where a row has less than 8 cols, then add the trouble maker to the sed statements in ```merge_corpus.py```.

Beware: this can also come from a previous DMT4 file: when buliding the general dictionary, the script reads _all_ DMT4 files available.
- Update 24-02: scripts now delete all DMT4 files before attempting to build the general dictionary.
