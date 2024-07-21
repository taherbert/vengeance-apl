import re
from collections import defaultdict

OFFENSIVE_TALENTS = {
    "ascending_flame:1": "AF",
    "spirit_bomb:1": "SpB",
    "bulk_extraction:1": "BE",
    "burning_blood:1": "BB",
    "soul_furnace:1": "SF",
    "focused_cleave:1": "FC",
    "chains_of_anger:1": "CoA",
    "volatile_flameblood:1": "VF",
    "fiery_demise:1": "FD",
    "fiery_demise:2": "FD",
    "stoke_the_flames:1": "StF",
    "cycle_of_binding:1": "CoB",
    "burning_alive:1": "BA",
    "charred_flesh:1": "CF",
    "charred_flesh:2": "CF",
    "darkglare_boon:1": "DGB",
    "soul_carver:1": "SC",
    "soulcrush:1": "Crush",
    "illuminated_sigils:1": "IS",
    "down_in_flames:1": "DiF",
}

DEFENSIVE_TALENTS = {
    "calcified_spikes:1": "CS",
    "extended_spikes:1": "ES",
    "fel_flame_fortification:1": "FFF",
    "void_reaver:1": "VR",
    "painbringer:1": "PB",
    "painbringer:2": "PB",
    "feed_the_demon:1": "FtD",
    "feed_the_demon:2": "FtD",
    "last_resort:1": "LR"
}

ABSENCE_INDICATORS = {
    "spirit_bomb:1": "NoSpB",
}

def create_unique_id(talents):
    offensive_parts = []
    defensive_parts = []
    for talent, abbrev in OFFENSIVE_TALENTS.items():
        if talent in talents:
            offensive_parts.append(abbrev)
        elif talent in ABSENCE_INDICATORS:
            offensive_parts.append(ABSENCE_INDICATORS[talent])
    for talent, abbrev in DEFENSIVE_TALENTS.items():
        if talent in talents:
            defensive_parts.append(abbrev)
        elif talent in ABSENCE_INDICATORS:
            defensive_parts.append(ABSENCE_INDICATORS[talent])

    offensive_id = "_".join(offensive_parts) or "Base"
    defensive_id = "_".join(defensive_parts) or "NoDefensive"

    return f"{offensive_id}__{defensive_id}"

def convert_profilesets(input_file, output_file):
    template_dict = {}

    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            match = re.match(r'profileset\."([^"]+)"\+="spec_talents=(.+)"', line.strip())
            if match:
                talents = match.group(2)
                unique_id = create_unique_id(talents)
                if unique_id not in template_dict:
                    template_dict[unique_id] = talents
                    template_string = f'$({unique_id})="{talents}"\n'
                    outfile.write(template_string)

    return [id for id, talents in template_dict.items() if list(template_dict.values()).count(talents) > 1]
# Usage
input_file = 'new-profileset.simc'
output_file = 'converted_profile_templates.simc'
duplicate_templates = convert_profilesets(input_file, output_file)

if duplicate_templates:
    print("The following templates had truly identical talent combinations:")
    for template in duplicate_templates:
        print(f"- {template}")
else:
    print("No duplicate templates were found.")