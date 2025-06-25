# replace_underscore.py
import pandas as pd
import random

def replace_underscore_in_conllu(file_path):
    """
    ConllU tables include '_' for N/A properties. This is problematic for pattern mining.
    This replaces '_' by a random integer.

    ConllU tables also include 'du' repeated for all columns for contraction (de+le, etc.).
    This deletes their lines.
    
    Args:
    file_path (str): The path to the .conllu file.
    """
    # Read the file with tab separator, skipping comment lines
    df = pd.read_csv(file_path, sep='\t', comment='#', header=None, quoting=3, engine='python')
    
    # Remove rows where first column is a digit range (e.g., '3-4')
    df = df[~df[0].astype(str).str.match(r'^\d+-\d+$')]

    # Process each row to replace '_' and 'du'
    for index, row in df.iterrows():
        random_integer = random.randint(1, 100)
        df.loc[index] = row.apply(lambda x: random_integer if x == '_' else x)
        # df.loc[index] = row.apply(lambda x: random_integer if x == 'du' else x)
        # df.loc[index] = row.apply(lambda x: random_integer if x == 'des' else x)
        # df.loc[index] = row.apply(lambda x: random_integer if x == 'au' else x)
        # df.loc[index] = row.apply(lambda x: random_integer if x == 'aux' else x)
        # This was a temp fix (Tim, 2025-06-04): it would be better to ignore lines with 'du' in col 2 or with two integers in col 1.

    # Write back to the same file
    df.to_csv(file_path, sep='\t', index=False, header=False, quoting=3)

