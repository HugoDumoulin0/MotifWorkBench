# Guide d'installation Linux

## Version simple

1. Récupérer le dossier `MWB_Linux` du Github
2. Ouvrir le dossier et lancer `install_and_run_linux.sh`
4. Suivre les instructions et l'application s'ouvrira pour vous.
5. Après la première installation, vous pouvez lancer directement l'outil avec `launch_motifworkbench.sh`

## Autorisation de lancement

Si le lancement indique `Permission denied`, ouvrir un terminal dans le dossier
`MWB_Linux`, puis exécuter :

```sh
chmod u+x install_and_run_linux.sh launch_motifworkbench.sh
```

Lancer ensuite `./install_and_run_linux.sh` pour l'installation, ou
`./launch_motifworkbench.sh` si l'application est déjà installée.

## Alternative

1. Installer Python
2. Installer R
3. Installer Perl
4. Récupérer le dossier `MWB_Linux` du Github
5. Créer un environnement virtuel
6. Installer les dépendances (pip install -r "src/requirements.txt") [vous installe obligatoirement Torch CPU]
7. Lancer dans le terminal (après avoir activé votre environnement virtuel) : `python run_gui.py`
8. Vous pouvez maintenant utiliser l'outil !
