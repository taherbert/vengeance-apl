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

## Usage
```
python generate_sims.py --simc <path_to_simc> --folder <path_to_simc_files> [options]
```

### Required Arguments
- `--simc`: Path to the SimulationCraft executable
- `--folder`: Path to the folder containing character.simc and profile_templates.simc

### Optional Arguments
- `--targets`: Number of targets for the simulation (overrides character.simc)
- `--time`: Fight duration in seconds (overrides character.simc)
- `--hero`: Hero talents to include (default: all)
- `--class`: Class talents to include (default: all)
- `--spec`: Spec talents to include (default: all)

## Examples
Run all talent combinations:

```
python generate_sims.py --simc /path/to/simc --folder /path/to/simc_files
```

Run specific talent combinations:

```
python generate_sims.py --simc /path/to/simc --folder /path/to/simc_files --hero "spb dgb" --class "fot" --spec "fb"
```

Change fight parameters:

```
python generate_sims.py --simc /path/to/simc --folder /path/to/simc_files --targets 3 --time 180
```

## Output
The script generates an HTML file with simulation results in the current directory. The filename includes a timestamp and the simulation parameters.

![CLI output](example-output.png "Example CLI output")

## Adapting for Different Specs
To use this script for a different spec:

1. Replace the contents of vengeance folder file with one for your desired spec. Possible to rename the folder to match your spec, but need to update generate_sims.py accordingly.
2. Update the profile_templates.simc file with the appropriate talent options for your spec.
3. Ensure the talent names in the --hero, --class, and --spec arguments match those in your profile_templates.simc file.

No changes to the Python script itself are necessary unless your spec requires unique handling of certain parameters.

## Notes
- The script assumes a specific structure for the profile_templates.simc file. Ensure your file follows the expected format with sections for Hero, Class, and Spec talents (denoted by the comment `#` symbols).
- Talent filtering is case-insensitive and requires all specified terms to be present in a talent name.
- The script creates a temporary .simc file for the simulation, which is not automatically deleted after execution.