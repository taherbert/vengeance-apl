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
        'hero': [],
        'class': [],
        'spec': []
    }

    sections = re.split(r'#\s*(Hero tree variants|Class tree variants|Spec tree variants)', content)

    if len(sections) != 7:
        print("Warning: Unexpected number of sections in profile_templates.simc")
        print(f"Number of sections: {len(sections)}")
        return talents

    for i, section_name in enumerate(['hero', 'class', 'spec']):
        section_content = sections[i*2 + 2]
        talent_defs = re.findall(r'(\$\([\w_]+\)="[^"]+")$', section_content, re.MULTILINE)
        talents[section_name].extend(talent_defs)

    return talents

def generate_simc_profile(params, search_terms):
    def format_term(template, include_terms, exclude_terms):
        if include_terms == ['all'] and not exclude_terms:
            return template
        terms = []
        if include_terms != ['all']:
            terms.extend([f"+{term}" for term in include_terms if term.lower() not in template.lower()])
        terms.extend([f"-{term}" for term in exclude_terms])
        if terms:
            return f"{template}:{','.join(terms)}"
        return template

    hero_term = format_term(params['hero'], search_terms['hero'], search_terms['hero_exclude'])
    class_term = format_term(params['class'], search_terms['class'], search_terms['class_exclude'])
    spec_term = format_term(params['spec'], search_terms['spec'], search_terms['spec_exclude'])

    formatted_name = f"[{hero_term}] ({class_term}) - {spec_term}"
    return "\n".join([
        f'profileset."{formatted_name}"=talents=',
        f'profileset."{formatted_name}"+="hero_talents=$({params["hero"]})"',
        f'profileset."{formatted_name}"+="class_talents=$({params["class"]})"',
        f'profileset."{formatted_name}"+="spec_talents=$({params["spec"]})"'
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
    parser.add_argument('--targets', type=int, default=None, help='Number of targets')
    parser.add_argument('--time', type=int, default=None, help='Fight duration in seconds')
    parser.add_argument('--hero', nargs='*', default=['all'], help='Hero abilities to include')
    parser.add_argument('--hero-exclude', nargs='*', default=[], help='Hero abilities to exclude')
    parser.add_argument('--class', dest='class_talents', nargs='*', default=['all'], help='Class abilities to include')
    parser.add_argument('--class-exclude', dest='class_talents_exclude', nargs='*', default=[], help='Class abilities to exclude')
    parser.add_argument('--spec', nargs='*', default=['all'], help='Spec abilities to include')
    parser.add_argument('--spec-exclude', nargs='*', default=[], help='Spec abilities to exclude')
    parser.add_argument('--targettime', nargs='+', help='List of target and time combinations in the format "targets,time"')
    args = parser.parse_args()

    # If no arguments were passed, set to 'all'
    if not args.hero and not args.class_talents and not args.spec:
        args.hero = ['all']
        args.class_talents = ['all']
        args.spec = ['all']

    # Parse targettime string into a list of tuples
    if args.targettime:
        args.targettime = [tuple(map(int, combo.split(','))) for combo in args.targettime]

    return args

def filter_talents(all_talents, include_list, exclude_list):
    if 'all' in include_list and not exclude_list:
        return all_talents

    filtered_talents = []
    for talent in all_talents:
        talent_name, talent_content = talent.split('=')
        talent_content = talent_content.strip('"')
        talent_abilities = {ability.split(':')[0]: ability.split(':')[1] for ability in talent_content.split('/')}

        include = True
        if 'all' not in include_list:
            include = any(term.lower() in ability.lower() and value != '0' for ability, value in talent_abilities.items() for term in include_list)

        if include and exclude_list:
            include = not any(term.lower() in ability.lower() and value != '0' for ability, value in talent_abilities.items() for term in exclude_list)

        if include:
            filtered_talents.append(talent)

    return filtered_talents

def generate_output_filename(args, character_content):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hero = '_'.join(args.hero) if args.hero != ['all'] else 'all'
    class_talent = '_'.join(args.class_talents) if args.class_talents != ['all'] else 'all'
    spec = '_'.join(args.spec) if args.spec != ['all'] else 'all'

    targets = re.search(r'desired_targets=(\d+)', character_content)
    time = re.search(r'max_time=(\d+)', character_content)

    targets = targets.group(1) if targets else 'default'
    time = time.group(1) if time else 'default'

    return f"simc_result_{timestamp}_targets{targets}_time{time}_{hero}_{class_talent}_{spec}.html"

def print_summary(talents, filtered_talents, profiles, search_terms):
    print("\nSimulation Summary:")
    print("===================")

    print("\nDetected Templates:")
    for category, talent_list in talents.items():
        print(f"  {category.capitalize()} talents: {len(talent_list)}")
        print(f"    {', '.join(talent.split('=')[0].strip('$()') for talent in talent_list)}")

    print("\nSelected Talents:")
    for category in ['hero', 'class', 'spec']:
        print(f"  {category.capitalize()} talents: {len(filtered_talents[category])}")
        if search_terms[category] != ['all']:
            print(f"    Included: {', '.join(search_terms[category])}")
        print(f"    Excluded: {', '.join(search_terms[f'{category}_exclude'])}")

    print(f"\nTotal Profilesets Generated: {len(profiles)}")

def update_character_simc(content, targets, time):
    if targets is not None:
        content = re.sub(r'desired_targets=\d+', f'desired_targets={targets}', content)
    if time is not None:
        content = re.sub(r'max_time=\d+', f'max_time={time}', content)
    return content

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
        'hero': filter_talents(talents['hero'], args.hero, args.hero_exclude),
        'class': filter_talents(talents['class'], args.class_talents, args.class_talents_exclude),
        'spec': filter_talents(talents['spec'], args.spec, args.spec_exclude)
    }

    if not any(filtered_talents.values()):
        print("Error: No valid profiles generated. Please check your talent selections.")
        return

    search_terms = {
        'hero': args.hero,
        'hero_exclude': args.hero_exclude,
        'class': args.class_talents,
        'class_exclude': args.class_talents_exclude,
        'spec': args.spec,
        'spec_exclude': args.spec_exclude
    }

    profiles = []
    for hero_talent in filtered_talents['hero']:
        for class_talent in filtered_talents['class']:
            for spec_talent in filtered_talents['spec']:
                hero_name = hero_talent.split('=')[0].strip('$()')
                class_name = class_talent.split('=')[0].strip('$()')
                spec_name = spec_talent.split('=')[0].strip('$()')
                profile = generate_simc_profile({
                    'hero': hero_name,
                    'class': class_name,
                    'spec': spec_name
                }, search_terms)
                profiles.append(profile)

    if not profiles:
        print("Error: No valid profiles generated. Please check your talent selections.")
        return

    print_summary(talents, filtered_talents, profiles, search_terms)

    if args.targettime:
        simulations = args.targettime
    else:
        simulations = [(args.targets, args.time)]

    for sim_targets, sim_time in simulations:
        print(f"\nRunning simulation for {sim_targets} target(s) and {sim_time} seconds")

        # Update character_content for this simulation
        current_character_content = update_character_simc(character_content, sim_targets, sim_time)

        simc_file = create_simc_file(current_character_content, profiles_content, profiles)
        print(f"\nCreated SimC file: {simc_file}")

        html_output = generate_output_filename(args, current_character_content)
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