import os

def combine_files(main_file, output_file):
    base_dir = os.path.dirname(main_file)

    def process_file(file_path):
        content = []
        with open(file_path, 'r') as infile:
            for line in infile:
                if line.startswith('input='):
                    # Extract filename from input line
                    filename = line.split('=')[1].strip()
                    # Construct full path for the input file
                    full_path = os.path.join(base_dir, filename)
                    # Recursively process the referenced file
                    content.extend(['\n'] + process_file(full_path) + ['\n'])
                elif line.lower().startswith('# imports'):
                    # Delete the line
                    continue
                else:
                    content.append(line)
        return content

    # Process the main file
    combined_content = process_file(main_file)

    # Write the combined content to the output file
    with open(output_file, 'w') as outfile:
        outfile.writelines(combined_content)

# Usage
combine_files('vengeance/character.simc', 'vengeance_full.simc')