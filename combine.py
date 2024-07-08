import os
import subprocess
import argparse

def combine_and_compile_files(main_file, output_file, simc_path):
    base_dir = os.path.dirname(main_file)

    def process_file(file_path):
        content = []
        with open(file_path, 'r') as infile:
            for line in infile:
                if line.startswith('input='):
                    filename = line.split('=')[1].strip()
                    full_path = os.path.join(base_dir, filename)
                    content.extend(['\n'] + process_file(full_path) + ['\n'])
                elif line.lower().startswith('# imports'):
                    continue
                else:
                    content.append(line)
        return content

    combined_content = process_file(main_file)

    temp_file = 'temp_combined.simc'
    with open(temp_file, 'w') as outfile:
        outfile.writelines(combined_content)

    try:
        subprocess.run([simc_path, temp_file, f'save={output_file}'], check=True)
        print(f"Successfully compiled and saved to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error running simc: {e}")
    except FileNotFoundError:
        print(f"Error: simc executable not found at {simc_path}")

    os.remove(temp_file)

def main():
    parser = argparse.ArgumentParser(description='Combine and compile SimulationCraft files.')
    parser.add_argument('simc', help='Path to the simc executable')
    parser.add_argument('--main', default='vengeance/character.simc', help='Path to the main .simc file (default: vengeance/character.simc)')
    parser.add_argument('--output', default='vengeance_full.simc', help='Path for the output .simc file (default: vengeance_full.simc)')

    args = parser.parse_args()

    combine_and_compile_files(args.main, args.output, args.simc)

if __name__ == "__main__":
    main()