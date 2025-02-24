# replace_underscore.py
import pandas as pd

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
        second_cell_value = row[1]  # Get the value of the second cell in the row
        df.loc[index] = row.apply(lambda x: second_cell_value if x == '_' else x)
    
    # Write back to the same file
    df.to_csv(file_path, sep='\t', index=False, header=False, quoting=3)

def delete_empty_line(file_path):
    # Read the file with tab separator, skipping comment lines
    df = pd.read_csv(file_path, sep='\t', comment='#', header=None, quoting=3, engine='python')

    # Remove rows where the entire row contains only numbers and tabs
    df_cleaned = df[~df.apply(lambda x: x.str.match(r'^[0-9\t]*$').all(), axis=1)]

    # Save the cleaned DataFrame back to a tab-separated file
    df_cleaned.to_csv(file_path, sep='\t', index=False, header=False)

