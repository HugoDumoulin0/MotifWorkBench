#!/usr/bin/perl

use CWB::CQP;
use IPC::Open2;

# Chemin vers le registre
my $registry = './Data/cwb-corpus/registry';
my $corpus   = 'MERGED';
my $query    = $ARGV[0];
my $query_text = 'group motif match text_id';

# Lancement du binaire CQP en mode silencieux (-e)
my $cmd = "cqp -r '$registry' -e";
my ($out, $in);

my $pid = open2($out, $in, $cmd) or die "Impossible de lancer CQP";

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
