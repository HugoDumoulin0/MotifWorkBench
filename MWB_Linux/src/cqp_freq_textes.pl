#!/usr/bin/perl

# """
# @author: hugodumoulin
# Modifié par @JcharlesDS
# """

use IPC::Open2;

# Chemin vers le registre (obligatoirement fourni par l'environnement)
my $registry = $ENV{'CORPUS_REGISTRY_PATH'} || die "CORPUS_REGISTRY_PATH manquant\n";
my $corpus   = 'MERGED';
my $query    = $ARGV[0];
my $query_text = 'group pattern match text_id';

my ($out, $in);
my $pid = open2($out, $in, 'cqp', '-r', $registry, '-e') or die "Impossible de lancer CQP";

# On envoie la requête CQP
print $in "$corpus;\n";
print $in "$query;\n";
print $in "$query_text;\n";
print $in "exit;\n";

# Lire et afficher les résultats de la requête
print "Résultats pour 'laboratoire' :\n";
while (my $line = <$out>) {
    print $line;  # Affiche chaque ligne de la sortie
}
