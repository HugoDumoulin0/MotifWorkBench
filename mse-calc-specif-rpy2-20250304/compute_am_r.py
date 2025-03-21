# _*_coding:utf-8_*_
import sys
import os
import argparse

import pandas as pd
from stats import stats as amstats



def main(df):
    # process command line arguments
    arg_parser = argparse.ArgumentParser(description='Python script to perform Multidimensional Analysis (MDA).')
    arg_parser.add_argument('infile', help='YAML configuration file defining sample composition, MDA feature queries and query engine.')
    arg_parser.add_argument('outfile', help='Output directory for result files.')
    arg_parser.add_argument('--ams', dest="ams", help='Base name of the result files.', action="store")
    
    args = arg_parser.parse_args()
    infile = args.infile
    outfile = args.outfile
    ams = args.ams if args.ams else []
    
    # Load input data frame
    # df = pd.read_csv(infile, sep="\t")
    
    # Process input data frame with R
    print("Compute specificities stats.")
    R_inc_file = os.path.join(os.path.dirname(__file__), 'stats', 'calc_specif.inc.R')
    R_am = amstats.StatsR(R_inc_file)
    # transform pandas data frame to R data frame
    r_df = R_am.pd2R(df)
    # Perform specificity score computation with R function
    print("Computing scores with R.")
    r_df_res = R_am.r.calc_specif(r_df)
    df_res = R_am.R2pd(r_df_res)
    df_res.to_csv(outfile, sep="\t", index=False)
    
    print("Processing done.")
    
