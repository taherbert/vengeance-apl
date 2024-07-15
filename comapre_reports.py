import os
import re
import json
from collections import defaultdict
from typing import Dict, List, Tuple

def extract_chart_data(file_path: str) -> Dict[str, float]:
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    match = re.search(r'{"series":\[{"name":"Damage per Second","data":\[(.*?)\]}', content, re.DOTALL)
    if not match:
        return {}

    data_string = match.group(1)
    data_pattern = r'{"name":"(.*?)","reldiff":.*?,"y":([\d.]+)}'
    data_matches = re.findall(data_pattern, data_string)

    return {name: float(y) for name, y in data_matches}

def extract_filename_info(filename: str) -> str:
    match = re.search(r'(\d+)T_(\d+)s', filename)
    return f"{match.group(1)}T {match.group(2)}s" if match else ""

def parse_build_name(build_name: str) -> Dict[str, str]:
    hero_match = re.search(r'\[(.*?)\]', build_name)
    class_match = re.search(r'\((.*?)\)', build_name)
    spec_match = build_name.split('-')[-1] if '-' in build_name else ''

    return {
        'hero_talent': hero_match.group(1) if hero_match else "",
        'class_talents': class_match.group(1).replace('_', ', ').split(', ') if class_match else [],
        'spec_talents': spec_match.split('_') if spec_match else [],
        'full_name': build_name
    }

def collect_data() -> Tuple[Dict[str, Dict[str, Dict]], List[str]]:
    data = defaultdict(lambda: defaultdict(dict))
    report_types = set()

    for filename in os.listdir('.'):
        if filename.endswith('.html') and 'all' in filename.lower():
            file_path = os.path.join('.', filename)
            report_type = extract_filename_info(filename)
            if report_type:
                report_types.add(report_type)
                chart_data = extract_chart_data(file_path)
                for build_name, value in chart_data.items():
                    build_info = parse_build_name(build_name)
                    data[build_info['full_name']][report_type] = value
                    data[build_info['full_name']].update(build_info)

    return dict(data), sorted(report_types, key=lambda x: (int(x.split('T')[0]), int(x.split()[1][:-1])))

def calculate_overall_rank(data: Dict[str, Dict[str, Dict]], report_types: List[str]) -> Dict[str, int]:
    overall_scores = {build: sum(build_data.get(rt, 0) for rt in report_types) / len(report_types)
                      for build, build_data in data.items()}
    sorted_builds = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
    return {build: rank + 1 for rank, (build, _) in enumerate(sorted_builds)}

def format_build_name(build: str) -> str:
    parts = build.split('-')
    hero_talent = re.search(r'\[(.*?)\]', parts[0]).group(1)
    class_talents = re.search(r'\((.*?)\)', parts[0]).group(1).replace('_', '/')
    spec_talents = parts[1].replace('_', '/')
    return f"{hero_talent} | {class_talents} | {spec_talents}"

def generate_html(data: Dict[str, Dict[str, Dict]], report_types: List[str]) -> str:
    overall_ranks = calculate_overall_rank(data, report_types)

    json_data = [{
        'build': format_build_name(build),
        'hero_talent': build_data['hero_talent'],
        'class_talents': build_data['class_talents'],
        'spec_talents': build_data['spec_talents'],
        'overall_rank': overall_ranks[build],
        'metrics': {rt: round(build_data.get(rt, 0), 2) for rt in report_types}
    } for build, build_data in data.items()]

    json_data.sort(key=lambda x: x['overall_rank'])

    st_report = min(report_types, key=lambda x: int(x.split('T')[0]))
    aoe_report = max(report_types, key=lambda x: int(x.split('T')[0]))
    top_st = max(json_data, key=lambda x: x['metrics'][st_report])
    top_aoe = max(json_data, key=lambda x: x['metrics'][aoe_report])

    table_headers = ''.join([f'<th class="mdc-data-table__header-cell" role="columnheader" scope="col" onclick="sortTable({i+2})">{rt} <i class="material-icons sort-icon">arrow_downward</i></th>' for i, rt in enumerate(report_types)])

    with open('template.html', 'r', encoding='utf-8') as f:
        html_template = f.read()

    with open('styles.css', 'r', encoding='utf-8') as f:
        css_content = f.read()

    with open('script.js', 'r', encoding='utf-8') as f:
        js_content = f.read()

    json_data_str = json.dumps(json_data)
    if not json_data_str or json_data_str == '[]':
        print("Warning: json_data is empty or invalid")

    js_with_data = f"""
    // Data injected by Python script
    const rawData = {json_data_str};
    const reportTypes = {json.dumps(report_types)};

    {js_content}
    """

    html = html_template.replace('$STYLES', css_content)
    html = html.replace('$SCRIPT', js_with_data)
    html = html.replace('$TABLE_HEADERS', table_headers)

    return html

def main():
    data, report_types = collect_data()
    html = generate_html(data, report_types)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    main()