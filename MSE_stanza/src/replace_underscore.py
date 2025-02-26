# replace_underscore.py
# import pandas as pd

def replace_underscore_in_conllu(file_path):
    """
    ConllU tables include '_' for N/A properties. This is problematic for pattern mining.
    This replaces '_' by a recopy of the form of the word, introducing redundancy and (I
    hope) protecting patterns from over-generation.

    Replace any cell containing '_' with the content of the second cell in the same row.
    
    Args:
    file_path (str): The path to the .conllu file.
    """
    output_lines = []

    with open(file_path, "r", encoding="utf-8") as infile:
        for line in infile:
            if line.startswith("#") or line.strip() == "":
                output_lines.append(line)  # Keep comments and empty lines unchanged
            else:
                row = line.rstrip("\n").split("\t")  # Remove only trailing newlines, not spaces
                if len(row) > 1:
                    row = [row[1] if cell == "_" else cell for cell in row]  # Replace '_'
                output_lines.append("\t".join(row) + "\n")  # Ensure newline is preserved

    with open(file_path, "w", encoding="utf-8") as outfile:
        outfile.writelines(output_lines)  # Writes back without adding extra newlines

# def delete_empty_line(file_path):
#     # Read the file with tab separator, skipping comment lines
#     df = pd.read_csv(file_path, sep='\t', comment='#', header=None, quoting=3, engine='python')

#     # Remove rows where the entire row contains only numbers and tabs
#     df_cleaned = df[~df.apply(lambda x: x.str.match(r'^[0-9\t]*$').all(), axis=1)]

#     # Save the cleaned DataFrame back to a tab-separated file
#     df_cleaned.to_csv(file_path, sep='\t', index=False, header=False)

