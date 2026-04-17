# Shiny_settings TODO

J'ai avancé sur une première version de la page Shiny pour entrer les réglages, appelé `Shiny_settings.r` provisoirement. Pour rappel, l'idée est que le mode d'exécution par défaut de MWB entraîne l'exécution de ce script et donc l'ouverture d'une GUI pour saisir les paramètres et effectuer quelques actions basiques. En accord avec Hugo, je laisse ce chantier de côté au 31-03-2026 et liste ici ce qui devra être repris.

## Overview
Une page avec deux onglets principaux et une card, avec trois onglets dans la card. Les deux onglets de page correspondent aux réglages (`Basic` -> à renommer en `Settings`) et à une recopie du `README.md` du dépôt GitHub (`References`). Les onglets de la card sous `Basic` sont `Basics` (réglages de tout sauf l'extraction de motifs), `Pattern mining` (réglages de l'extraction de motifs) et `browse metadata` (explorer les métadata pour trouver quels axe de partition utiliser).

L'onglet `Basics` comprend des réglages de Stansa (modèle, bool GPU), l'activation/désactivation de la GUI pour l'AFC, et *NEW* des options pour changer le corpus, vider les dossiers de MWB des anciens corpus et motifs minés, et sélectionner le fichier de métadonnées *NEW*. Attention, les options destructives ne sont pas protégées par une notif de confirmation, donc ça peut détruire votre dossier MWB.

## TODO

- [ ] Interface avec python
    - [ ] lancer la GUI depuis le code python
    - [ ] implémenter un flag dans la commande python pour bypasser la GUI et retomber sur `config.py` en mode par défaut
    - [ ] feeder à Python les paramètres réglés dans la GUI en overwrite des defaults
- [ ] Finir le dév. de la GUI
    - [ ] implémener un bouton `RUN` qui ferme la page et reprend l'exécution du script python
    - [ ] passer les packages utilisés dans une commande `ipak` (cf. GUI des AFC)
    - [ ] rassembler l'ensemble des variables réglées par les onglets `basics` et `pattern mining` dans un JSON pour le feeder à python
    - [ ] Vérifier le fonctionnement des routines de sélection des métadonnées (je ne sais plus jusqu'où j'avais poussé le truc)
    - [ ] Mettre en forme l'onglet de card `Pattern mining` 
    - [ ] Mettre en forme l'onglet de card `Browse metadata`
    - [ ] Protéger par fenêtre sugissante de confirmation les options destructrice de l'onglet de card `Basics`
    - [ ] Vérifier que l'onglet de page `References` fonctionne une fois que le dépôt Github est passé en public, et/ou rédiger un contenu pour remplacer la reproduction du README.md du Github
    - [ ] Vérifier que je n'ai pas oublié de paramètre
    - [ ] Prévoir de répliquer les derniers réglages utilisés
        - [ ] Suppose d'avoir sauvegardé le dernier JSON de réglages (= il doit échapper aux options descructrices)
        - [ ] Soit sous la forme du mode par défaut (avec un bouton de ré-initialisation des réglages) soit grâce à un bouton `Resume previous settings`
    - [ ] Corriger les coquilles dans la GUI (je ne l'ai pas relue)
    - [ ] Ajouter des infos sur `Use GPU` pour Stanza: je comptais préciser que même avec un GPU décent Stanza galère sur des gros textes et va juste avorter le process quand il atteint son max de mémoire. Avec un GPU de 8Go, il y a ~20% des textes du corpus ArchivU que je dois tagger au CPU parce qu'ils débordent la mémoire que Stanza emmagasine dans le GPU (alors que pas de problème en CPU, si ce n'est que c'est long)
- [ ] Vérifier le fonctionnement sous différents OS ? Je l'ai développée sous Linux. À savoir : normalement c'est bon, mais il peut arriver que les réglages de sécurité des navigateurs internet bloquent certaines actions, donc ça vaut le coup de vérifier sur différentes machines.

D'autres choix de design peuvent être faits, ce n'est qu'un truc provisoire que je propose. Par exemple, je n'ai pas du tout utilisé de `tooltip`s (cf. GUI de l'AFC), parce que c'est plutôt des trucs que je rajoute à la fin... et que je n'ai pas fini!

Enfin, bon à savoir, les IA se perdent souvent dans le Shiny, les rétroactions entre tous les boutons peuvent vraiment les rendre perplexes... Parfois il faut remonter à la main jusqu'à la cause du problème au lieu de passer 30 minutes à s'énerver sur un chatbot éditeur de code.

> Timothée, 31-03-2026.