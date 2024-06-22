def combine_files(main_file, output_file):
    with open(output_file, 'w') as outfile:
        with open(main_file, 'r') as infile:
            for line in infile:
                if line.startswith('input='):
                    # Extract filename from input line
                    filename = line.split('=')[1].strip()
                    # Write contents of the referenced file
                    with open(filename, 'r') as imported_file:
                        outfile.write(f"\n")
                        outfile.write(imported_file.read())
                        outfile.write("\n")
                # else if line contains the phrase "Imports" case insensitive remove the entire line and carriage return and continue
                elif line.lower().startswith('# imports'):
                    # delete the line
                    outfile.write(f"")
                else:
                    outfile.write(line)

# Usage
combine_files('vengeance/vengeance.simc', 'vengeance/vengeance_full.simc')