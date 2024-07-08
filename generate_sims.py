import argparse
import functools
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from itertools import product

# Simple in-memory cache
_profile_cache = None
_talent_filter_cache = {}

def find_simc_files(folder_path):
    character_file = os.path.join(folder_path, 'character.simc')
    profiles_file = os.path.join(folder_path, 'profile_templates.simc')

    if not os.path.isfile(character_file):
        raise FileNotFoundError(f"character.simc not found in {folder_path}")
    if not os.path.isfile(profiles_file):
        raise FileNotFoundError(f"profile_templates.simc not found in {folder_path}")

    return character_file, profiles_file

def parse_profiles_simc(profiles_path):
    global _profile_cache
    if _profile_cache is not None:
        return _profile_cache

    with open(profiles_path, 'r') as f:
        content = f.read()

    talents = {category: {} for category in ['hero_talents', 'class_talents', 'spec_talents']}
    sections = re.split(r'#\s*(Hero tree variants|Class tree variants|Spec tree variants)', content)

    if len(sections) != 7:
        raise ValueError(f"Unexpected number of sections in profile_templates.simc: {len(sections)}")

    for i, section_name in enumerate(['hero_talents', 'class_talents', 'spec_talents']):
        section_content = sections[i*2 + 2]
        talent_defs = re.findall(r'\$\(([\w_]+)\)="([^"]+)"', section_content)
        talents[section_name] = dict(talent_defs)

    _profile_cache = talents
    return talents

@functools.lru_cache(maxsize=None)
def generate_simc_profile(hero_talents, class_talents, spec_talents, hero_terms, hero_exclude_terms, class_terms, class_exclude_terms, spec_terms, spec_exclude_terms):
    def format_term(template, include_terms, exclude_terms):
        if include_terms == frozenset(['all']) and not exclude_terms:
            return template
        terms = [f"+{term}" for term in include_terms if term != 'all' and term.lower() not in template.lower()]
        terms.extend(f"-{term}" for term in exclude_terms)
        return f"{template}:{','.join(terms)}" if terms else template

    hero_term = format_term(hero_talents, hero_terms, hero_exclude_terms)
    class_term = format_term(class_talents, class_terms, class_exclude_terms)
    spec_term = format_term(spec_talents, spec_terms, spec_exclude_terms)

    formatted_name = f"[{hero_term}] ({class_term}) - {spec_term}"
    return '\n'.join([
        f'profileset."{formatted_name}"=talents=',
        f'profileset."{formatted_name}"+="hero_talents=$({hero_talents})"',
        f'profileset."{formatted_name}"+="class_talents=$({class_talents})"',
        f'profileset."{formatted_name}"+="spec_talents=$({spec_talents})"'
    ])

def create_simc_file(character_content, profiles_content, profiles):
    content = f"{character_content}\n\n{profiles_content}\n\n" + "\n\n".join(profiles)
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
                    sys.stdout.write(f"\rSimulating profile {current}/{total}, {remaining_time} remaining")
                    sys.stdout.flush()

        sys.stdout.write("\n")
        rc = process.poll()
        if rc != 0:
            print(f"SimC process exited with return code {rc}")
            print(f"SimC stderr output: {process.stderr.read()}")
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
    parser.add_argument('--hero-talents', nargs='*', default=None, help='Hero talents to include')
    parser.add_argument('--hero-talents-exclude', nargs='*', default=[], help='Hero talents to exclude')
    parser.add_argument('--class-talents', nargs='*', default=None, help='Class talents to include')
    parser.add_argument('--class-talents-exclude', nargs='*', default=[], help='Class talents to exclude')
    parser.add_argument('--spec-talents', nargs='*', default=None, help='Spec talents to include')
    parser.add_argument('--spec-talents-exclude', nargs='*', default=[], help='Spec talents to exclude')
    parser.add_argument('--targettime', nargs='+', help='List of target and time combinations in the format "targets,time"')
    args = parser.parse_args()

    # Handle "all" cases for talents
    for talent_type in ['hero_talents', 'class_talents', 'spec_talents']:
        talent_arg = getattr(args, talent_type)
        if talent_arg is None or len(talent_arg) == 0 or 'all' in talent_arg:
            setattr(args, talent_type, {'all'})
        else:
            setattr(args, talent_type, set(talent_arg))

    args.hero_talents_exclude = set(args.hero_talents_exclude)
    args.class_talents_exclude = set(args.class_talents_exclude)
    args.spec_talents_exclude = set(args.spec_talents_exclude)

    if args.targettime:
        args.targettime = [tuple(map(int, combo.split(','))) for combo in args.targettime]

    return args

def filter_talents(talents, include_list, exclude_list):
    cache_key = (frozenset(talents.items()), frozenset(include_list), frozenset(exclude_list))
    if cache_key in _talent_filter_cache:
        return _talent_filter_cache[cache_key]

    filtered_talents = []
    for talent_name, talent_content in talents.items():
        talent_abilities = set(ability.split(':')[0].lower() for ability in talent_content.split('/'))

        # Include all talents if 'all' is in the include_list
        if 'all' in include_list:
            include = True
        else:
            include = any(term.lower() in ability for term in include_list for ability in talent_abilities)

        # Apply exclusions
        if include and exclude_list:
            include = not any(term.lower() in ability for term in exclude_list for ability in talent_abilities)

        if include:
            filtered_talents.append((talent_name, talent_content))

    _talent_filter_cache[cache_key] = filtered_talents
    return filtered_talents

def generate_output_filename(args, character_content):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hero_talents = '_'.join(args.hero_talents) if args.hero_talents != {'all'} else 'all'
    class_talents = '_'.join(args.class_talents) if args.class_talents != {'all'} else 'all'
    spec_talents = '_'.join(args.spec_talents) if args.spec_talents != {'all'} else 'all'

    targets = re.search(r'desired_targets=(\d+)', character_content)
    time = re.search(r'max_time=(\d+)', character_content)

    targets = targets.group(1) if targets else 'default'
    time = time.group(1) if time else 'default'

    return f"simc_result_{timestamp}_targets{targets}_time{time}_{hero_talents}_{class_talents}_{spec_talents}.html"

def print_summary(talents, filtered_talents, profiles, search_terms, generation_time):
    print("\nSimulation Summary:")
    print("===================")

    print("\nDetected Templates:")
    for category, talent_list in talents.items():
        print(f"  {category.capitalize()}: {len(talent_list)}")

    print("\nSelected Talents:")
    for category in ['hero_talents', 'class_talents', 'spec_talents']:
        print(f"  {category.capitalize()}:")
        print(f"    Total available: {len(talents[category])}")
        print(f"    Selected: {len(filtered_talents[category])}")
        if search_terms[category] != {'all'}:
            print(f"    Included terms: {', '.join(search_terms[category])}")
        if search_terms[f'{category}_exclude']:
            print(f"    Excluded terms: {', '.join(search_terms[f'{category}_exclude'])}")
        print(f"    Selected talent names: {', '.join(name for name, _ in filtered_talents[category])}")

    print(f"\nTotal Profilesets Generated: {len(profiles)}")
    print(f"Time taken to generate profiles and prepare SimC execution: {generation_time:.2f} seconds")

def update_character_simc(content, targets, time):
    if targets is not None:
        content = re.sub(r'desired_targets=\d+', f'desired_targets={targets}', content)
    if time is not None:
        content = re.sub(r'max_time=\d+', f'max_time={time}', content)
    return content

def main(args):
    start_time = time.time()

    try:
        character_file, profiles_file = find_simc_files(args.folder)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    try:
        with open(character_file, 'r') as f:
            character_content = f.read()

        with open(profiles_file, 'r') as f:
            profiles_content = f.read()
    except IOError as e:
        print(f"Error reading files: {e}")
        return

    try:
        talents = parse_profiles_simc(profiles_file)
    except ValueError as e:
        print(f"Error parsing profile_templates.simc: {e}")
        return

    if not os.path.isfile(args.simc):
        print(f"Error: SimulationCraft executable not found at: {args.simc}")
        return

    filtered_talents = {
        'hero_talents': filter_talents(talents['hero_talents'], args.hero_talents, args.hero_talents_exclude),
        'class_talents': filter_talents(talents['class_talents'], args.class_talents, args.class_talents_exclude),
        'spec_talents': filter_talents(talents['spec_talents'], args.spec_talents, args.spec_talents_exclude)
    }

    if not any(filtered_talents.values()):
        print("Error: No valid profiles generated. Please check your talent selections.")
        return

    search_terms = {
        'hero_talents': args.hero_talents,
        'hero_talents_exclude': args.hero_talents_exclude,
        'class_talents': args.class_talents,
        'class_talents_exclude': args.class_talents_exclude,
        'spec_talents': args.spec_talents,
        'spec_talents_exclude': args.spec_talents_exclude
    }

    profiles = [
        generate_simc_profile(
            hero_name, class_name, spec_name,
            frozenset(args.hero_talents), frozenset(args.hero_talents_exclude),
            frozenset(args.class_talents), frozenset(args.class_talents_exclude),
            frozenset(args.spec_talents), frozenset(args.spec_talents_exclude)
        )
        for hero_name, _ in filtered_talents['hero_talents']
        for class_name, _ in filtered_talents['class_talents']
        for spec_name, _ in filtered_talents['spec_talents']
    ]

    if not profiles:
        print("Error: No valid profiles generated. Please check your talent selections.")
        return

    generation_time = time.time() - start_time
    print_summary(talents, filtered_talents, profiles, search_terms, generation_time)

    simulations = args.targettime or [(args.targets, args.time)]

    for sim_targets, sim_time in simulations:
        print(f"\nPreparing simulation for {sim_targets} target(s) and {sim_time} seconds")

        current_character_content = update_character_simc(character_content, sim_targets, sim_time)
        simc_file = create_simc_file(current_character_content, profiles_content, profiles)
        print(f"SimC input file created: {simc_file}")

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