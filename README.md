# SimulationCraft Profile Generator
This script generates and runs SimulationCraft profiles for World of Warcraft character optimization.

## Features
- Automatically generates profiles based on talent combinations
- Filters talent combinations based on user input
- Supports custom fight durations and target counts
- Generates an HTML output with simulation results

## Requirements
- Python 3.6+
- SimulationCraft executable
- `character.simc` and `profile_templates.simc` files for your character/spec
- `config.ini` file for configuration

## Usage
```
python generate_sims.py <path_to_config_file>
```


### Configuration File (config.ini)
The script now uses a configuration file (config.ini) instead of command-line arguments. Here's an example of the config.ini structure:

```ini
[General]
simc = /path/to/simc/executable
folder = /path/to/simc/files
single_sim = false
timestamp = true

[Simulations]
targets = 1
time = 300
targettime = 1,300 5,60

[TalentFilters]
hero_talents = all
hero_talents_exclude =
class_talents = all
class_talents_exclude =
spec_talents = all
spec_talents_exclude =
```

[General] Section
* simc: Path to the SimulationCraft executable
* folder: Path to the folder containing character.simc and profile_templates.simc
* single_sim: Set to true to run a single simulation with the talent string from character.simc
* timestamp: Set to true to include a timestamp in the output filename

[Simulations] Section
* targets: Default number of targets for the simulation
* time: Default fight duration in seconds
* targettime: List of target and time combinations for multiple simulations (overrides targets and time if specified)

[TalentFilters] Section
* hero_talents: Hero talents to include (default: all)
* hero_talents_exclude: Hero talents to exclude
* class_talents: Class talents to include (default: all)
* class_talents_exclude: Class talents to exclude
* spec_talents: Spec talents to include (default: all)
* spec_talents_exclude: Spec talents to exclude

## Examples
Run all talent combinations:

```ini
[TalentFilters]
hero_talents = all
class_talents = all
spec_talents = all
```

Run specific talent combinations:

```ini
[TalentFilters]
hero_talents = spb dgb
class_talents = fot
spec_talents = fb
```

Run multiple simulations with different target and time combinations:
```ini
[Simulations]
targettime = 1,300 6,60 10,60

[TalentFilters]
hero_talents = aldrachi
class_talents = hunt
spec_talents = nospb dgb
```

## Output
The script generates an HTML file with simulation results in the current directory. The filename includes the simulation parameters and optionally a timestamp.

## Adapting for Different Specs
To use this script for a different spec:
1. Replace the contents of the folder containing character.simc and profile_templates.simc with files for your desired spec.
2. Update the profile_templates.simc file with the appropriate talent options for your spec.
3. Ensure the talent names in the config.ini file match those in your profile_templates.simc file.

No changes to the Python script itself are necessary unless your spec requires unique handling of certain parameters.

## Notes
* The script assumes a specific structure for the profile_templates.simc file. Ensure your file follows the expected format with sections for Hero, Class, and Spec talents (denoted by the comment # symbols).
* Talent filtering is case-insensitive and requires all specified terms to be present in a talent name.
* The script creates a temporary .simc file for the simulation, which is deleted after execution.