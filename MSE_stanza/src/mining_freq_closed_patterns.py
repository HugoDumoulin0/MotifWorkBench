#!/usr/bin/python3
# -*- coding:utf8 -*-

"""
$1 : fichier DMT4
$2 : minsup
$3 : gap premiere val
$4 : gap seconde val
action : extraction des motifs frequents / clos sous les contraintes donnees en input
"""

import os
import sys
import re


def get_nbr_seq(dmt4_files):
    with open("{}".format(dmt4_files), 'r', encoding="utf-8") as dmt4 :
        return len([line for line in dmt4.readlines() if "seqId" in line])


def get_minsup(minsup, dmt4_files):
    return round((get_nbr_seq(dmt4_files) / 100) * minsup)


if __name__ == '__main__':

    print("-" * 70)
    print("\t\t\t Extract freq patterns")
    print("-" * 70)

    dmt4_files = sys.argv[1]
    minsup = sys.argv[2]
    gap_min = sys.argv[3]
    gap_max = sys.argv[4]
    threads = sys.argv[5]

    file_out = "{}_{}{}_{}_freq.txt".format(sys.argv[2], gap_min, gap_max,dmt4_files.split("/")[-1][:-4])

    with open("Prefixscontraint/config/Load.ini", "w", encoding="utf8") as set_up:
        set_up.write("MINSUP={}\n".format(minsup))
        set_up.write("CORPUS=../../{}\n".format(dmt4_files))
        set_up.write("THREAD={}\n".format(threads))
        set_up.write("GAPMIN={}\n".format(gap_min))
        set_up.write("GAPMAX={}\n".format(gap_max))

    os.system("bash src/execute_freq_pattern.sh {}".format(file_out))

    print("-" * 70)
    print("\t\t\t Extract closed patterns")
    print("-" * 70)

    with open("BideSpanTree/bin/Load.ini", "w", encoding="utf8") as set_up:
        set_up.write("MINSUP={}\n".format(minsup))
        set_up.write("CORPUS=../../{}\n".format(dmt4_files))
        set_up.write("THREAD=1\n")
        set_up.write("GAPMIN={}\n".format(0))
        set_up.write("GAPMAX={}\n".format(0))

    os.system("bash src/execute_closed_pattern.sh {}".format(file_out.replace("freq", "closed")))
