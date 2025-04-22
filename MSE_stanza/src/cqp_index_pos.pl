#!/usr/bin/perl

use CWB::CQP;
use IPC::Open2;

# Chemin vers le registre
my $registry = './Data/cwb-corpus/registry';
my $corpus   = 'MERGED';
my $query_0 = 'A = [pos=".*"]';
my $query_1 = 'count A by pos';

# Lancement du binaire CQP en mode silencieux (-e)
my $cmd = "cqp -r '$registry' -e";
my ($out, $in);

my $pid = open2($out, $in, $cmd) or die "Impossible de lancer CQP";

# On envoie la requête CQP
print $in "$corpus;\n";
print $in "$query_0;\n";
print $in "$query_1;\n";
print $in "exit;\n";

# Lire et afficher les résultats de la requête
print "Résultats' :\n";
while (my $line = <$out>) {
    print $line;  # Affiche chaque ligne de la sortie
}
