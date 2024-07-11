import argparse
import configparser
import functools
import os
import re
import subprocess
import sys
from datetime import datetime

# Global caches
_profile_cache = None
_talent_filter_cache = {}

def load_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

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
def generate_simc_profile(hero_talents, class_talents, spec_talents):
    formatted_name = f"[{hero_talents}] ({class_talents}) - {spec_talents}"
    return '\n'.join([
        f'profileset."{formatted_name}"=talents=',
        f'profileset."{formatted_name}"+="hero_talents=$({hero_talents})"',
        f'profileset."{formatted_name}"+="class_talents=$({class_talents})"',
        f'profileset."{formatted_name}"+="spec_talents=$({spec_talents})"'
    ])

def create_simc_file(character_content, profiles_content, profiles, folder_path, sim_targets, sim_time):
    # Update character content with sim_targets and sim_time
    updated_character_content = update_character_simc(character_content, sim_targets, sim_time)

    used_templates = set(re.findall(r'\$\(([\w_]+)\)', '\n'.join(profiles)))
    filtered_profiles_content = [line for line in profiles_content.split('\n') if any(f'$({template})' in line for template in used_templates)]

    content = f"{updated_character_content}\n\n" + "\n".join(filtered_profiles_content) + "\n\n" + "\n\n".join(profiles)
    temp_file_path = os.path.join(folder_path, "temp_simc_input.simc")
    with open(temp_file_path, 'w') as temp_file:
        temp_file.write(content)

    profile_names = [re.search(r'profileset\."([^"]+)"', profile).group(1) for profile in profiles]
    return temp_file_path, profile_names

def run_simc(simc_path, simc_file, html_output, profile_names):
    try:
        simc_path, simc_file, html_output = map(os.path.abspath, [simc_path, simc_file, html_output])
        simc_dir = os.path.dirname(simc_file)
        original_dir = os.getcwd()
        os.chdir(simc_dir)

        if not os.path.exists(simc_path):
            print(f"Error: SimC executable not found at {simc_path}")
            return None

        process = subprocess.Popen([simc_path, os.path.basename(simc_file), f'html={html_output}'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)

        pattern = re.compile(r'(\d+)/(\d+) \[.*\] \d+/\d+ .* \((\d+m, \d+s|\d+s)\)$')
        max_line_length = 0

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                match = pattern.search(output)
                if match:
                    current, total, remaining_time = match.groups()
                    current_profile = profile_names[int(current) - 1] if int(current) <= len(profile_names) else "Unknown"
                    output_line = f"\rSimulating profile {current}/{total}, {remaining_time} remaining - Current: {current_profile}"

                    # Pad the output line with spaces to overwrite the entire previous line
                    max_line_length = max(max_line_length, len(output_line))
                    padded_output = output_line.ljust(max_line_length)

                    sys.stdout.write(padded_output)
                    sys.stdout.flush()

        # Clear the last line
        sys.stdout.write('\r' + ' ' * max_line_length + '\r')
        sys.stdout.flush()
        sys.stdout.write("\n")
        rc = process.poll()
        if rc != 0:
            print(f"SimC process exited with return code {rc}")
            print(f"SimC stderr output: {process.stderr.read()}")
            return None

        # Update the HTML title
        update_html_title(html_output)

        return "SimC completed successfully"
    except subprocess.CalledProcessError as e:
        print(f"Error running SimC: {e}")
        print(f"SimC stderr output: {e.stderr}")
        return None
    except FileNotFoundError:
        print(f"Error: simc executable not found at {simc_path}")
        return None
    finally:
        os.chdir(original_dir)
        try:
            os.remove(simc_file)
        except OSError as e:
            print(f"Error deleting temporary file {simc_file}: {e}")

def update_html_title(html_file):
    with open(html_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # Extract filename without extension
    filename = os.path.splitext(os.path.basename(html_file))[0]

    # Replace the title
    new_content = re.sub(r'<title>SimulationCraft</title>',
                         f'<title>{filename}</title>', content)

    with open(html_file, 'w', encoding='utf-8') as file:
        file.write(new_content)

def filter_talents(talents, include_list, exclude_list, talent_type=''):
    cache_key = (frozenset(talents.items()), frozenset(include_list), frozenset(exclude_list), talent_type)
    if cache_key in _talent_filter_cache:
        return _talent_filter_cache[cache_key]

    filtered_talents = []
    for talent_name, talent_content in talents.items():
        talent_abilities = set(ability.split(':')[0].lower() for ability in talent_content.split('/'))

        if 'all' in include_list:
            include = True
        elif talent_type == 'hero_talents':
            include = ('aldrachi' in include_list and 'art_of_the_glaive' in talent_content.lower()) or \
                      ('felscarred' in include_list and 'demonsurge' in talent_content.lower()) or \
                      any(term.lower() in ability for term in include_list for ability in talent_abilities)
        else:
            include = all(any(term.lower() in ability for ability in talent_abilities) for term in include_list)

        if include and exclude_list:
            include = not any(term.lower() in ability for term in exclude_list for ability in talent_abilities)

        if include:
            filtered_talents.append((talent_name, talent_content))

    _talent_filter_cache[cache_key] = filtered_talents
    return filtered_talents

def generate_output_filename(config, sim_targets, sim_time):
    if config.getboolean('General', 'single_sim', fallback=False):
        filename = f"simc_single_{sim_targets}T_{sim_time}sec"
    else:
        hero_talent = next(iter(config['TalentFilters']['hero_talents'].split())) if config['TalentFilters']['hero_talents'] != 'all' else 'all'
        filename = f"simc_{hero_talent}_{sim_targets}T_{sim_time}sec"

    if config.getboolean('General', 'timestamp', fallback=False):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename}_{timestamp}"

    return f"{filename}.html"

def print_summary(talents, filtered_talents, profiles, search_terms, config, simulations):
    print("\nSimulation Summary:")
    print("===================")

    print("\nSimulation Parameters:")
    if len(simulations) == 1:
        targets, time = simulations[0]
        print(f"  Targets: {targets}")
        print(f"  Time: {time} seconds")
    else:
        print("  Multiple simulations:")
        for i, (targets, time) in enumerate(simulations, 1):
            print(f"    Sim {i}: {targets} target(s), {time} seconds")

    print("\nDetected Templates:")
    for category, talent_list in talents.items():
        print(f"  {category.capitalize()}: {len(talent_list)}")

    print("\nFilter Summary:")
    for category in ['hero_talents', 'class_talents', 'spec_talents']:
        selected_count = len(filtered_talents[category])
        total_count = len(talents[category])
        print(f"  {category.capitalize()} ({selected_count}/{total_count} selected):")

        include_terms = config['TalentFilters'][category]
        exclude_terms = config['TalentFilters'][f'{category}_exclude']

        if include_terms == 'all':
            print(f"    Include: All")
        else:
            print(f"    Include: {include_terms}")

        if exclude_terms:
            print(f"    Exclude: {exclude_terms}")

    print(f"\nTotal Profilesets Generated: {len(profiles)}")

def update_character_simc(content, targets, time):
    content = re.sub(r'desired_targets=\d+', f'desired_targets={targets}', content)
    if 'desired_targets=' not in content:
        content += f'\ndesired_targets={targets}'

    content = re.sub(r'max_time=\d+', f'max_time={time}', content)
    if 'max_time=' not in content:
        content += f'\nmax_time={time}'

    return content

def main(config_path):
    config = load_config(config_path)

    try:
        character_file, profiles_file = find_simc_files(config['General']['folder'])
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

    if not os.path.isfile(config['General']['simc']):
        print(f"Error: SimulationCraft executable not found at: {config['General']['simc']}")
        return

    if config.getboolean('General', 'single_sim', fallback=False):
        print("Running single simulation with talent string from character.simc")
        sim_targets = config['Simulations'].getint('targets', fallback=1)
        sim_time = config['Simulations'].getint('time', fallback=300)
        html_output = generate_output_filename(config, sim_targets, sim_time)
        temp_file_path = os.path.join(config['General']['folder'], "temp_simc_input.simc")
        with open(temp_file_path, 'w') as temp_file:
            temp_file.write(update_character_simc(character_content, sim_targets, sim_time))

        print(f"Starting SimC simulation...")
        results = run_simc(config['General']['simc'], temp_file_path, html_output, ["Single Sim"])

        if results:
            print("\nSimC Results:")
            print(results)
            print(f"HTML output saved to: {html_output}")
        else:
            print("\nSimC did not produce any results.")

        return

    # Continue with multiple profileset generation if not single_sim
    try:
        talents = parse_profiles_simc(profiles_file)
    except ValueError as e:
        print(f"Error parsing profile_templates.simc: {e}")
        return

    filtered_talents = {
        'hero_talents': filter_talents(talents['hero_talents'], config['TalentFilters']['hero_talents'].split(), config['TalentFilters']['hero_talents_exclude'].split(), 'hero_talents'),
        'class_talents': filter_talents(talents['class_talents'], config['TalentFilters']['class_talents'].split(), config['TalentFilters']['class_talents_exclude'].split(), 'class_talents'),
        'spec_talents': filter_talents(talents['spec_talents'], config['TalentFilters']['spec_talents'].split(), config['TalentFilters']['spec_talents_exclude'].split(), 'spec_talents')
    }

    if not any(filtered_talents.values()):
        print("Error: No valid profiles generated. Please check your talent selections.")
        return

    search_terms = {
        'hero_talents': set(config['TalentFilters']['hero_talents'].split()),
        'hero_talents_exclude': set(config['TalentFilters']['hero_talents_exclude'].split()),
        'class_talents': set(config['TalentFilters']['class_talents'].split()),
        'class_talents_exclude': set(config['TalentFilters']['class_talents_exclude'].split()),
        'spec_talents': set(config['TalentFilters']['spec_talents'].split()),
        'spec_talents_exclude': set(config['TalentFilters']['spec_talents_exclude'].split())
    }

    profiles = [
        generate_simc_profile(hero_name, class_name, spec_name)
        for hero_name, _ in filtered_talents['hero_talents']
        for class_name, _ in filtered_talents['class_talents']
        for spec_name, _ in filtered_talents['spec_talents']
    ]

    if not profiles:
        print("Error: No valid profiles generated. Please check your talent selections.")
        return

    if 'targettime' in config['Simulations']:
        simulations = [tuple(map(int, combo.split(','))) for combo in config['Simulations']['targettime'].split()]
    else:
        targets = config['Simulations'].getint('targets', fallback=1)
        time = config['Simulations'].getint('time', fallback=300)
        simulations = [(targets, time)]

    print_summary(talents, filtered_talents, profiles, search_terms, config, simulations)

    for sim_targets, sim_time in simulations:
        print(f"\nPreparing simulation for {sim_targets} target(s) and {sim_time} seconds")

        simc_file, profile_names = create_simc_file(character_content, profiles_content, profiles, config['General']['folder'], sim_targets, sim_time)

        html_output = generate_output_filename(config, sim_targets, sim_time)
        print(f"HTML output will be saved to: {html_output}")
        print(f"Starting SimC simulation...")
        results = run_simc(config['General']['simc'], simc_file, html_output, profile_names)

        if results:
            print("\nSimC Results:")
            print(results)
            print(f"HTML output saved to: {html_output}")
        else:
            print("\nSimC did not produce any results.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate and run SimulationCraft profiles')
    parser.add_argument('config', help='Path to configuration file')
    args = parser.parse_args()
    main(args.config)