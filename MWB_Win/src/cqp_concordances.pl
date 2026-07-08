#!/usr/bin/perl

# """
# Script de concordancier CQP pour MotifWorkBench
# @author: @JcharlesDS (2026)
# """

use IPC::Open2;

# Chemin vers le registre (obligatoirement fourni par l'environnement)
my $registry = $ENV{'CORPUS_REGISTRY_PATH'} || die "CORPUS_REGISTRY_PATH manquant\n";
my $corpus   = 'MERGED';
my $pattern  = $ARGV[0];  # Motif de recherche 
my $context  = $ARGV[1] || 10;  # Nombre de mots de contexte

my ($out, $in);
my $pid = open2($out, $in, 'cqp', '-r', $registry, '-e') or die "Impossible de lancer CQP";

# On envoie la requête CQP
print $in "$corpus;\n";
print $in "Pattern = $pattern;\n";
print $in "set Context $context words;\n";
print $in "set LeftKWICDelim '-->';\n";
print $in "set RightKWICDelim '<--';\n";
print $in "set PrintStructures 'text_id';\n";  # Afficher l'ID de texte
print $in "cat Pattern;\n";
print $in "exit;\n";

# Fermer le flux d'entrée pour signaler que nous avons terminé
close($in);

# Lire et afficher les résultats de la requête
while (my $line = <$out>) {
    print $line;
}

close($out);
waitpid($pid, 0);
