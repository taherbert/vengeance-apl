import argparse
import configparser
import functools
import os
import pickle
import re
import subprocess
import sys
import time
import json
from datetime import datetime
import multiprocessing
from functools import partial
from collections.abc import Iterable
from talenthasher import generate_talent_hash
import queue
from tqdm import tqdm


# Global caches
CACHE_FILE = "talent_hash_cache.pkl"
_profile_cache = None
_talent_filter_cache = {}

class ProgressTracker:
    def __init__(self, total_profiles, total_simulations):
        self.total_profiles = total_profiles
        self.total_simulations = total_simulations
        self.total_profiles_all_sims = total_profiles * total_simulations
        self.message_queue = queue.Queue()

        # Calculate the maximum width needed for the count
        max_count_width = len(str(self.total_profiles_all_sims))

        # Custom format for the right side of the progress bar
        r_bar_format = "{{n_fmt:>{0}s}}/{{total_fmt:>{0}s}} [{{elapsed}}<{{remaining}}, {{rate_fmt}}]".format(max_count_width)

        # Full format specification for the progress bar
        format_spec = "{{desc:<20}}|{{bar:50}}|{0}".format(r_bar_format)

        self.overall_bar = tqdm(total=self.total_profiles_all_sims, desc="Overall Progress",
                                position=0, unit="profile", bar_format=format_spec)
        self.current_bar = tqdm(total=self.total_profiles, desc="Current Simulation",
                                position=1, unit="profile", leave=False, bar_format=format_spec)

    def update(self, line):
        if "Generating Profileset:" in line or "Profilesets" in line:
            self.overall_bar.update(1)
            self.current_bar.update(1)

    def start_simulation(self, simulation_number):
        self.current_bar.reset()
        self.current_bar.set_description(f"Sim {simulation_number}/{self.total_simulations}")

    def queue_message(self, message):
        self.message_queue.put(message)

    def print_queued_messages(self):
        while not self.message_queue.empty():
            print(self.message_queue.get())

    def close(self):
        self.overall_bar.close()
        self.current_bar.close()

def ensure_output_directory(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"Created output directory: {directory}")
        except OSError as e:
            print(f"Error creating output directory {directory}: {e}")
            return False
    return True

def load_talent_hash_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        except:
            print("Error loading talent hash cache. Generating new cache.")
    return {}

def save_talent_hash_cache(cache):
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)

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

def update_json_with_hashes(json_file, talent_hashes):
    with open(json_file, 'r') as f:
        data = json.load(f)

    def extract_names(profile_name):
        match = re.match(r'\[(.*?)\] \((.*?)\) - (.*)', profile_name)
        if match:
            return match.groups()
        parts = re.split(r'[\[\](),-]', profile_name)
        parts = [part.strip() for part in parts if part.strip()]
        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]
        return None, None, None

    # Update the profilesets section
    if 'sim' in data and 'profilesets' in data['sim']:
        for result in data['sim']['profilesets']['results']:
            profile_name = result['name']
            if profile_name == "Base":
                continue

            hero_name, class_name, spec_name = extract_names(profile_name)
            if hero_name and class_name and spec_name:
                hash_key = f"{hero_name}_{class_name}_{spec_name}"
                talent_hash = talent_hashes.get(hash_key, "unknown_hash")
                result['talent_hash'] = talent_hash
            else:
                print(f"Warning: Could not parse profile name: {profile_name}")
                result['talent_hash'] = "unknown_hash"

    # Update the players section (optional, as it might not be needed)
    if 'players' in data['sim']:
        for profile in data['sim']['players']:
            profile_name = profile['name']
            if profile_name == "Base":
                continue

            hero_name, class_name, spec_name = extract_names(profile_name)
            if hero_name and class_name and spec_name:
                hash_key = f"{hero_name}_{class_name}_{spec_name}"
                talent_hash = talent_hashes.get(hash_key, "unknown_hash")
                profile['talent_hash'] = talent_hash
            else:
                print(f"Warning: Could not parse profile name: {profile_name}")
                profile['talent_hash'] = "unknown_hash"

    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)

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

    # Load cached talent hashes
    talent_hashes = load_talent_hash_cache()

    combinations = [
        (hero_name, class_name, spec_name, hero_talent, class_talent, spec_talent)
        for hero_name, hero_talent in talents['hero_talents'].items()
        for class_name, class_talent in talents['class_talents'].items()
        for spec_name, spec_talent in talents['spec_talents'].items()
    ]

    new_hashes = False
    print("Generating talent hashes...")

    with tqdm(total=len(combinations), desc="Talent Hash Progress", bar_format="{desc:<30}{percentage:3.0f}%|{bar:50}{r_bar}") as pbar:
        for hero_name, class_name, spec_name, hero_talent, class_talent, spec_talent in combinations:
            hash_key = f"{hero_name}_{class_name}_{spec_name}"
            if hash_key not in talent_hashes:
                try:
                    talent_hash = generate_talent_hash(hero_talent, class_talent, spec_talent)
                    talent_hashes[hash_key] = talent_hash
                    new_hashes = True
                except Exception as exc:
                    print(f'Talent hash generation failed for {hash_key}: {exc}')
            pbar.update(1)

    if new_hashes:
        save_talent_hash_cache(talent_hashes)

    print("Talent hash generation completed.")

    _profile_cache = (talents, talent_hashes)
    return talents, talent_hashes

@functools.lru_cache(maxsize=None)
def generate_simc_profile(hero_talents, class_talents, spec_talents):
    formatted_name = f"[{hero_talents}] ({class_talents}) - {spec_talents}"
    return '\n'.join([
        f'profileset."{formatted_name}"=talents=',
        f'profileset."{formatted_name}"+="hero_talents=$({hero_talents})"',
        f'profileset."{formatted_name}"+="class_talents=$({class_talents})"',
        f'profileset."{formatted_name}"+="spec_talents=$({spec_talents})"'
    ])

def create_simc_file(character_content, profiles_content, profiles, apl_folder, sim_targets, sim_time, iterations=None, target_error=None, json_output=False, html_output=True, output_path=None, talent_hashes=None):
    # Update character content with sim_targets and sim_time
    updated_character_content = update_character_simc(character_content, sim_targets, sim_time, iterations, target_error, json_output, html_output, output_path)

    used_templates = set(re.findall(r'\$\(([\w_]+)\)', '\n'.join(profiles)))
    filtered_profiles_content = [line for line in profiles_content.split('\n') if any(f'$({template})' in line for template in used_templates)]

    content = f"{updated_character_content}\n\n" + "\n".join(filtered_profiles_content) + "\n\n" + "\n\n".join(profiles)
    temp_file_path = os.path.join(apl_folder, "temp_simc_input.simc")
    with open(temp_file_path, 'w') as temp_file:
        temp_file.write(content)

    profiles_with_hashes = []
    for profile in profiles:
        match = re.search(r'profileset\."([^"]+)"', profile)
        if match:
            profile_name = match.group(1)
            hero_name, class_name, spec_name = profile_name.split('] (')[0][1:], profile_name.split('] (')[1].split(') - ')[0], profile_name.split(' - ')[1]
            hash_key = f"{hero_name}_{class_name}_{spec_name}"
            talent_hash = talent_hashes.get(hash_key, "unknown_hash")
            profile_with_hash = f"{profile}\n# talent_hash={talent_hash}"
            profiles_with_hashes.append(profile_with_hash)
        else:
            profiles_with_hashes.append(profile)

    content = f"{updated_character_content}\n\n" + "\n".join(filtered_profiles_content) + "\n\n" + "\n\n".join(profiles_with_hashes)

    profile_names = [re.search(r'profileset\."([^"]+)"', profile).group(1) for profile in profiles]
    return temp_file_path, profile_names

def run_simc(simc_path, simc_file, output_path, profile_names, json_output, html_output,
             total_profiles, total_simulations, simulation_number, progress_tracker):
    temp_file_deleted = False
    try:
        simc_path, simc_file = map(os.path.abspath, [simc_path, simc_file])
        output_path = os.path.abspath(output_path)
        output_dir = os.path.dirname(output_path)
        simc_dir = os.path.dirname(simc_file)
        original_dir = os.getcwd()
        os.chdir(simc_dir)

        if not os.access(output_dir, os.W_OK):
            progress_tracker.queue_message(f"Error: No write permission in the output directory: {output_dir}")
            return None, temp_file_deleted

        if not os.path.exists(simc_path):
            progress_tracker.queue_message(f"Error: SimC executable not found at {simc_path}")
            return None, temp_file_deleted

        command = [simc_path, os.path.basename(simc_file)]

        if html_output:
            command.append(f'html={output_path}')
        if json_output:
            json_file = output_path if not html_output else output_path.replace('.html', '.json')
            command.append(f'json2={json_file}')

        progress_tracker.start_simulation(simulation_number)

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   universal_newlines=True, bufsize=1)

        for line in iter(process.stdout.readline, ''):
            progress_tracker.update(line)

        stdout, stderr = process.communicate()

        rc = process.returncode
        if rc != 0:
            progress_tracker.queue_message(f"SimC process exited with return code {rc}")
            progress_tracker.queue_message(f"SimC stderr output: {stderr}")
            if "Failed to open JSON output file" in stderr:
                progress_tracker.queue_message("Error: Unable to create or write to JSON file. Please check permissions and available disk space.")
            return None, temp_file_deleted

        progress_tracker.queue_message("SimC completed successfully")
        return "SimC completed successfully", temp_file_deleted

    except Exception as e:
        progress_tracker.queue_message(f"Unexpected error occurred: {e}")
        return None, temp_file_deleted
    finally:
        os.chdir(original_dir)
        try:
            os.remove(simc_file)
            temp_file_deleted = True
        except OSError as e:
            progress_tracker.queue_message(f"Error deleting temporary file {simc_file}: {e}")

@functools.lru_cache(maxsize=None)
def filter_talents(talents_items, include_list, exclude_list, talent_type=''):
    talents = dict(talents_items)
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

    return filtered_talents

def generate_output_filename(config, sim_targets, sim_time):
    if config['Simulations'].getboolean('single_sim', fallback=False):
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

    iterations = config['Simulations'].get('iterations')
    if iterations:
        print(f"  Iterations: {iterations}")

    target_error = config['Simulations'].get('target_error')
    if target_error:
        print(f"  Target Error: {target_error}")

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

def update_character_simc(content, targets, time, iterations=None, target_error=None, json_output=False, html_output=True, output_path=None):
    content = re.sub(r'desired_targets=\d+', f'desired_targets={targets}', content)
    if 'desired_targets=' not in content:
        content += f'\ndesired_targets={targets}'

    content = re.sub(r'max_time=\d+', f'max_time={time}', content)
    if 'max_time=' not in content:
        content += f'\nmax_time={time}'

    if iterations is not None:
        content = re.sub(r'iterations=\d+', f'iterations={iterations}', content)
        if 'iterations=' not in content:
            content += f'\niterations={iterations}'

    if target_error is not None:
        content = re.sub(r'target_error=[\d.]+', f'target_error={target_error}', content)
        if 'target_error=' not in content:
            content += f'\ntarget_error={target_error}'

    # Add json2 parameter if json_output is True
    if json_output and output_path:
        json_file = output_path if not html_output else output_path.replace('.html', '.json')
        if 'json2=' in content:
            content = re.sub(r'json2=.*', f'json2={json_file}', content)
        else:
            content += f'\njson2={json_file}'

    # Add html parameter if html_output is True
    if html_output and output_path:
        if 'html=' in content:
            content = re.sub(r'html=.*', f'html={output_path}', content)
        else:
            content += f'\nhtml={output_path}'

    return content

def cleanup_files(files_to_delete):
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"File {file_path} deleted successfully.")
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}")

def run_additional_script(script_name, config_path=None):
    command = [sys.executable, script_name]
    if config_path:
        command.append(config_path)

    print(f"\nRunning {script_name}...")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    for line in process.stdout:
        print(line.strip())

    _, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error running {script_name}:")
        print(stderr)
    else:
        print(f"{script_name} completed successfully.")

def main(config_path):
    config = load_config(config_path)
    iterations = config['Simulations'].get('iterations', None)
    target_error = config['Simulations'].get('target_error', None)
    json_output = config['General'].getboolean('json_output', fallback=False)
    html_output = config['General'].getboolean('html_output', fallback=True)
    report_folder = config['General'].get('report_folder', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports'))

    if not ensure_output_directory(report_folder):
        print("Error: Unable to create or access the report folder. Exiting.")
        return

    try:
        character_file, profiles_file = find_simc_files(config['General']['apl_folder'])
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

    talents, talent_hashes = parse_profiles_simc(profiles_file)

    filtered_talents = {
        'hero_talents': filter_talents(
            tuple(talents['hero_talents'].items()),
            tuple(config['TalentFilters']['hero_talents'].split()),
            tuple(config['TalentFilters']['hero_talents_exclude'].split()),
            'hero_talents'
        ),
        'class_talents': filter_talents(
            tuple(talents['class_talents'].items()),
            tuple(config['TalentFilters']['class_talents'].split()),
            tuple(config['TalentFilters']['class_talents_exclude'].split()),
            'class_talents'
        ),
        'spec_talents': filter_talents(
            tuple(talents['spec_talents'].items()),
            tuple(config['TalentFilters']['spec_talents'].split()),
            tuple(config['TalentFilters']['spec_talents_exclude'].split()),
            'spec_talents'
        )
    }

    if not any(filtered_talents.values()):
        print("Error: No valid profiles generated. Please check your talent selections.")
        return

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
        targettime = config['Simulations']['targettime'].strip()
        if targettime:
            simulations = [tuple(map(int, combo.split(','))) for combo in targettime.split() if combo.strip()]
            if not simulations:
                print("Warning: No valid target-time combinations found in config. Using default values.")
                targets = config['Simulations'].getint('targets', fallback=1)
                time = config['Simulations'].getint('time', fallback=300)
                simulations = [(targets, time)]
        else:
            print("Warning: Empty targettime in config. Using default values.")
            targets = config['Simulations'].getint('targets', fallback=1)
            time = config['Simulations'].getint('time', fallback=300)
            simulations = [(targets, time)]
    else:
        targets = config['Simulations'].getint('targets', fallback=1)
        time = config['Simulations'].getint('time', fallback=300)
        simulations = [(targets, time)]

    print_summary(talents, filtered_talents, profiles, {
        'hero_talents': set(config['TalentFilters']['hero_talents'].split()),
        'hero_talents_exclude': set(config['TalentFilters']['hero_talents_exclude'].split()),
        'class_talents': set(config['TalentFilters']['class_talents'].split()),
        'class_talents_exclude': set(config['TalentFilters']['class_talents_exclude'].split()),
        'spec_talents': set(config['TalentFilters']['spec_talents'].split()),
        'spec_talents_exclude': set(config['TalentFilters']['spec_talents_exclude'].split())
    }, config, simulations)

    total_profiles = len(profiles)
    total_simulations = len(simulations)

    progress_tracker = ProgressTracker(total_profiles, total_simulations)

    try:
        for sim_index, (sim_targets, sim_time) in enumerate(simulations, 1):
            output_filename = generate_output_filename(config, sim_targets, sim_time)
            output_path = os.path.join(report_folder, output_filename)
            if not html_output:
                output_path = output_path.replace('.html', '.json')

            simc_file, profile_names = create_simc_file(character_content, profiles_content, profiles,
                                                        config['General']['apl_folder'], sim_targets, sim_time,
                                                        iterations, target_error, json_output, html_output,
                                                        output_path, talent_hashes)

            results, temp_file_deleted = run_simc(
                config['General']['simc'], simc_file, output_path, profile_names,
                json_output, html_output, total_profiles, total_simulations, sim_index,
                progress_tracker
            )

            if results:
                progress_tracker.queue_message("\nSimC Results:")
                progress_tracker.queue_message(results)
                if html_output:
                    progress_tracker.queue_message(f"HTML output saved to: {output_path}")
                if json_output:
                    json_path = output_path if not html_output else output_path.replace('.html', '.json')
                    if os.path.exists(json_path):
                        progress_tracker.queue_message(f"Updating JSON output with talent hashes...")
                        try:
                            update_json_with_hashes(json_path, talent_hashes)
                            progress_tracker.queue_message(f"JSON output updated and saved to: {json_path}")
                        except Exception as e:
                            progress_tracker.queue_message(f"Error updating JSON with talent hashes: {e}")
                    else:
                        progress_tracker.queue_message(f"Warning: JSON file not found at {json_path}")
            else:
                progress_tracker.queue_message("\nSimC did not produce any results.")

            if not temp_file_deleted:
                cleanup_files([simc_file])

    finally:
        progress_tracker.close()
        progress_tracker.print_queued_messages()

    print("\nAll simulations completed.")

    # Run combine.py
    run_additional_script("combine.py", config_path)

    # Run compare_reports.py
    run_additional_script("compare_reports.py")

    print("\nFull pipeline completed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate and run SimulationCraft profiles')
    parser.add_argument('config', help='Path to configuration file')
    args = parser.parse_args()
    main(args.config)