def combine_files(main_file, output_file):
    with open(output_file, 'w') as outfile:
        with open(main_file, 'r') as infile:
            for line in infile:
                if line.startswith('input='):
                    # Extract filename from input line
                    filename = line.split('=')[1].strip()
                    # Write contents of the referenced file
                    with open(filename, 'r') as imported_file:
                        outfile.write(f"# Contents of {filename}\n")
                        outfile.write(imported_file.read())
                        outfile.write("\n")
                else:
                    outfile.write(line)

# Usage
combine_files('vengeance.simc', 'vengeance_full.simc')