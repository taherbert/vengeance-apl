import itertools
import subprocess
import tempfile
import argparse
import os
import re
import sys
from datetime import datetime

def find_simc_files(folder_path):
    character_file = os.path.join(folder_path, 'character.simc')
    profiles_file = os.path.join(folder_path, 'profile_templates.simc')

    if not os.path.isfile(character_file):
        raise FileNotFoundError(f"character.simc not found in {folder_path}")
    if not os.path.isfile(profiles_file):
        raise FileNotFoundError(f"profile_templates.simc not found in {folder_path}")

    return character_file, profiles_file

def parse_profiles_simc(profiles_path):
    with open(profiles_path, 'r') as f:
        content = f.read()

    talents = {
        'hero': set(),
        'class': set(),
        'spec': set()
    }

    sections = re.split(r'#\s*(Hero tree variants|Class tree variants|Spec tree variants)', content)

    if len(sections) != 7:
        print("Warning: Unexpected number of sections in profile_templates.simc")
        print(f"Number of sections: {len(sections)}")
        return talents

    for i, section_name in enumerate(['hero', 'class', 'spec']):
        section_content = sections[i*2 + 2]
        talent_defs = re.findall(r'\$\(([\w_]+)\)=', section_content)
        talents[section_name].update(talent_defs)

    return {k: sorted(v) for k, v in talents.items()}

def generate_simc_profile(params):
    return "\n".join([
        f'profileset."{params["name"]}"=talents=',
        f'profileset."{params["name"]}"+="hero_talents=$({params["hero"]})"',
        f'profileset."{params["name"]}"+="class_talents=$({params["class"]})"',
        f'profileset."{params["name"]}"+="spec_talents=$({params["spec"]})"'
    ])

def create_simc_file(character_content, profiles_content, profiles):
    content = character_content + "\n\n" + profiles_content + "\n\n" + "\n\n".join(profiles)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.simc', delete=False) as temp_file:
        temp_file.write(content)
    return temp_file.name

def run_simc(simc_path, simc_file, html_output):
    try:
        process = subprocess.Popen([simc_path, simc_file, f'html={html_output}'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)

        pattern = re.compile(r'(\d+)/(\d+) \[.*\] \d+/\d+ .* \((\d+m, \d+s|\d+s)\)$')

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                match = pattern.search(output)
                if match:
                    current, total, remaining_time = match.groups()
                    sys.stdout.write(f"\rGenerating profileset {current}/{total}, {remaining_time} remaining")
                    sys.stdout.flush()

        sys.stdout.write("\n")  # New line after progress is complete
        rc = process.poll()
        if rc != 0:
            print(f"SimC process exited with return code {rc}")
            err = process.stderr.read()
            print(f"SimC stderr output: {err}")
            return None
        return "SimC completed successfully"
    except subprocess.CalledProcessError as e:
        print(f"Error running SimC: {e}")
        print(f"SimC stderr output: {e.stderr}")
        return None

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate and run SimulationCraft profiles')
    parser.add_argument('--simc', required=True, help='Path to SimulationCraft executable')
    parser.add_argument('--folder', required=True, help='Path to folder containing character.simc and profile_templates.simc')
    parser.add_argument('--targets', type=int, default=1, help='Number of targets')
    parser.add_argument('--time', type=int, default=300, help='Fight duration in seconds')
    parser.add_argument('--hero', nargs='*', default=['all'], help='Hero talents to include')
    parser.add_argument('--class', dest='class_talents', nargs='*', default=['all'], help='Class talents to include')
    parser.add_argument('--spec', nargs='*', default=['all'], help='Spec talents to include')
    args = parser.parse_args()

    # If no arguments were passed, set to 'all'
    args.hero = ['all'] if not args.hero else args.hero
    args.class_talents = ['all'] if not args.class_talents else args.class_talents
    args.spec = ['all'] if not args.spec else args.spec

    return args

def filter_talents(all_talents, include_list):
    if 'all' in include_list:
        return all_talents
    include_terms = [term.lower() for item in include_list for term in item.split()]
    return [t for t in all_talents if any(inc in t.lower() for inc in include_terms)]

def generate_output_filename(args):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hero = '_'.join(args.hero) if args.hero != ['all'] else 'all'
    class_talent = '_'.join(args.class_talents) if args.class_talents != ['all'] else 'all'
    spec = '_'.join(args.spec) if args.spec != ['all'] else 'all'
    return f"simc_result_{timestamp}_targets{args.targets}_time{args.time}_{hero}_{class_talent}_{spec}.html"

def print_summary(talents, filtered_talents, profiles):
    print("\nSimulation Summary:")
    print("===================")

    print("\nDetected Templates:")
    for category, talent_list in talents.items():
        print(f"  {category.capitalize()} talents: {len(talent_list)}")
        print(f"    {', '.join(talent_list)}")

    print("\nSelected Talents:")
    for category, talent_list in filtered_talents.items():
        print(f"  {category.capitalize()} talents: {len(talent_list)}")
        print(f"    {', '.join(talent_list)}")

    print(f"\nTotal Profilesets Generated: {len(profiles)}")

def main(args):
    # Find and validate character.simc and profile_templates.simc
    character_file, profiles_file = find_simc_files(args.folder)

    # Parse profile_templates.simc to get talent options
    talents = parse_profiles_simc(profiles_file)

    # Validate SimC path
    if not os.path.isfile(args.simc):
        raise FileNotFoundError(f"SimulationCraft executable not found at: {args.simc}")

    with open(character_file, 'r') as f:
        character_content = f.read()

    with open(profiles_file, 'r') as f:
        profiles_content = f.read()

    filtered_talents = {
        'hero': filter_talents(talents['hero'], args.hero),
        'class': filter_talents(talents['class'], args.class_talents),
        'spec': filter_talents(talents['spec'], args.spec)
    }

    if not any(filtered_talents.values()):
        print("Error: No valid profiles generated. Please check your talent selections.")
        return

    profiles = []
    for talent_combo in itertools.product(*filtered_talents.values()):
        params = dict(zip(filtered_talents.keys(), talent_combo))
        params['name'] = "_".join(talent_combo)
        profiles.append(generate_simc_profile(params))

    if not profiles:
        print("Error: No valid profiles generated. Please check your talent selections.")
        return

    print_summary(talents, filtered_talents, profiles)

    simc_file = create_simc_file(character_content, profiles_content, profiles)

    print(f"\nCreated SimC file: {simc_file}")

    html_output = generate_output_filename(args)
    print(f"Starting SimC simulation...")
    results = run_simc(args.simc, simc_file, html_output)

    if results:
        print("\nSimC Results:")
        print(results)
        print(f"HTML output saved to: {html_output}")
    else:
        print("\nSimC did not produce any results.")

if __name__ == "__main__":
    args = parse_arguments()
    main(args)