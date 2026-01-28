"""
@author: Timothée Premat 
"""
import pandas as pd
import random

def replace_underscore_in_conllu(file_path):
    """
    ConllU tables include '_' for N/A properties. This is problematic for pattern mining.
    This replaces '_' by a recopy of the form of the word, introducing redundancy and (I
    hope) protecting patterns for over-generation.

    Replace any cell containing '_' with the content of the second cell in the same row.
    
    Args:
    file_path (str): The path to the .conllu file.
    """
    # Read the file with tab separator, skipping comment lines
    df = pd.read_csv(file_path, sep='\t', comment='#', header=None, quoting=3, engine='python')
    
    # Process each row to replace '_'
    for index, row in df.iterrows():
        random_integer = random.randint(1, 100)
        df.loc[index] = row.apply(lambda x: random_integer if x == '_' else x)
    # Write back to the same file
    df.to_csv(file_path, sep='\t', index=False, header=False, quoting=3)
