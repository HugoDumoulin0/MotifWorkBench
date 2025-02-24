import os

def merge_texts(input_base_folder, output_base_folder, types_textes):
    """
    Merges all text files in each subdirectory of input_base_folder.
    If a directory contains more than one file, all are merged into a single file.
    The merged file is stored in a new directory with the same name as type_texte.

    Args:
        input_base_folder (str): Path to the directory containing subdirectories of text files.
        output_base_folder (str): Path where merged files will be saved in separate folders.

    This is ChatGPT-based script, then customized. It is probably suboptimal but it works.
    Contrary to what Talismane seems to do, Stanza performs on individual texts. Here, we need to
    merge all files of each type_texte into a single file before running Stanza.
    """
    os.makedirs(output_base_folder, exist_ok=True)  # Ensure base output directory exists

    for type_texte in types_textes:
        rep = os.path.join(input_base_folder, type_texte)  # Path to each type_texte folder

        if os.path.isdir(rep):  # Ensure it's a directory
            files = [f for f in os.listdir(rep) if f.endswith(".txt")]  # Get only .txt files

        
            type_output_folder = os.path.join(output_base_folder, type_texte)  # Create a folder for each type_texte
            os.makedirs(type_output_folder, exist_ok=True)  # Ensure the output folder exists

            output_file = os.path.join(type_output_folder, f"{type_texte}.txt")  # Define output file name

            with open(output_file, "w", encoding="utf-8") as outfile:
                for file in sorted(files):  # Sorting ensures a consistent order
                    file_path = os.path.join(rep, file)
                    with open(file_path, "r", encoding="utf-8") as infile:
                        for line in infile:
                            # Apply `sed`-like transformations
                            line = line.replace("#", "HASHTAG ")  # Remove `#` symbols
                            line = line.replace('“', 'QUOTE ')  # Replace multiple spaces with a single space
                            line = line.replace('"', 'QUOTE ')  # Replace multiple spaces with a single space
                            line = line.replace('”', 'QUOTE ')  # Replace multiple spaces with a single space
                            # line = line.strip()  # Remove leading/trailing whitespace
                            # line = line.lower()  # Convert text to lowercase

                            if line:  # Skip empty lines
                                outfile.write(line + "\n")  # Write cleaned line with newline

            print(f"\t Merged {len(files)} files into {output_file}")
