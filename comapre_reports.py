import os
import re
import json
from collections import defaultdict

def extract_chart_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    match = re.search(r'{"series":\[{"name":"Damage per Second","data":\[(.*?)\]}', content, re.DOTALL)
    if not match:
        return None

    data_string = match.group(1)
    data_pattern = r'{"name":"(.*?)","reldiff":.*?,"y":([\d.]+)}'
    data_matches = re.findall(data_pattern, data_string)

    if not data_matches:
        return None

    result = {name: float(y) for name, y in data_matches}
    return result

def extract_filename_info(filename):
    match = re.search(r'(\d+)T_(\d+)s', filename)
    if match:
        targets = int(match.group(1))
        time = int(match.group(2))
        return f"{targets}T {time}s"
    return None

def parse_build_name(build_name):
    hero_match = re.search(r'\[(.*?)\]', build_name)
    class_match = re.search(r'\((.*?)\)', build_name)
    spec_match = build_name.split('-')[-1] if '-' in build_name else ''

    hero_talent = hero_match.group(1) if hero_match else ""
    class_talents = class_match.group(1).replace('_', ', ').split(', ') if class_match else []
    spec_talents = spec_match.split('_') if spec_match else []

    return {
        'hero_talent': hero_talent,
        'class_talents': class_talents,
        'spec_talents': spec_talents,
        'full_name': build_name
    }

def collect_data():
    data = defaultdict(lambda: defaultdict(dict))
    report_types = set()

    for filename in os.listdir('.'):
        if filename.endswith('.html'):
            file_path = os.path.join('.', filename)
            report_type = extract_filename_info(filename)
            if report_type:
                report_types.add(report_type)
                chart_data = extract_chart_data(file_path)
                if chart_data:
                    for build_name, value in chart_data.items():
                        build_info = parse_build_name(build_name)
                        data[build_info['full_name']][report_type] = value
                        data[build_info['full_name']].update(build_info)

    return data, sorted(report_types, key=lambda x: (int(x.split('T')[0]), int(x.split()[1][:-1])))

def calculate_overall_rank(data, report_types):
    overall_scores = {}
    for build, build_data in data.items():
        scores = [build_data.get(report_type, 0) for report_type in report_types]
        overall_scores[build] = sum(scores) / len(scores)

    sorted_builds = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
    overall_ranks = {build: rank + 1 for rank, (build, _) in enumerate(sorted_builds)}

    return overall_ranks

def generate_html(data, report_types):
    overall_ranks = calculate_overall_rank(data, report_types)

    json_data = []
    for build, build_data in data.items():
        entry = {
            'build': format_build_name(build),
            'hero_talent': build_data['hero_talent'],
            'class_talents': build_data['class_talents'],
            'spec_talents': build_data['spec_talents'],
            'overall_rank': overall_ranks[build],
            'metrics': {rt: round(build_data.get(rt, 0), 2) for rt in report_types}  # Round to 2 decimal places
        }
        json_data.append(entry)

    json_data.sort(key=lambda x: x['overall_rank'])

    table_headers = ''.join([f'<th onclick="sortTable({i+2})">{rt}</th>' for i, rt in enumerate(report_types)])

    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SimulationCraft Report Summary</title>
        <style>
            body {
                font-family: Arial, Helvetica, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #2c3e50;
                margin-bottom: 20px;
            }
            #filters {
                margin-bottom: 20px;
            }
            .filter-section {
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 10px;
            }
            button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 15px;
                cursor: pointer;
                border-radius: 4px;
            }
            button:hover {
                background-color: #2980b9;
            }
            .filter-content {
                display: none;
                margin-top: 10px;
            }
            .filter-content label {
                display: block;
                margin-bottom: 5px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                background-color: #fff;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            th, td {
                text-align: left;
                padding: 12px;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
                cursor: pointer;
            }
            th:hover {
                background-color: #e8e8e8;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SimulationCraft Report Summary</h1>
            <div id="filters"></div>
            <table id="dataTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">Build</th>
                        <th onclick="sortTable(1)">Overall Rank</th>
                        $TABLE_HEADERS
                    </tr>
                </thead>
                <tbody>
                    <!-- Table rows will be populated by the script -->
                </tbody>
            </table>
        </div>

        <script>
        const rawData = $JSON_DATA;
        const reportTypes = $REPORT_TYPES;

        function generateFilterHTML() {
            const filters = {
                heroTalent: new Set(rawData.map(d => d.hero_talent)),
                classTalents: new Set(rawData.flatMap(d => d.class_talents)),
                specTalents: new Set(rawData.flatMap(d => d.spec_talents))
            };

            const filterContainer = document.getElementById('filters');
            filterContainer.innerHTML = '';

            const filterNames = {
                heroTalent: 'Hero Talent',
                classTalents: 'Class Talents',
                specTalents: 'Spec Talents'
            };

            for (const [filterType, filterSet] of Object.entries(filters)) {
                const section = document.createElement('div');
                section.className = 'filter-section';
                section.innerHTML = `
                    <button onclick="toggleFilter('${filterType}-filter')">${filterNames[filterType]}</button>
                    <div id="${filterType}-filter" class="filter-content" style="display:none;">
                        ${Array.from(filterSet).map(value =>
                            `<label><input type="checkbox" checked onchange="applyFilters()" data-filter="${filterType}" value="${value}"> ${value}</label><br>`
                        ).join('')}
                    </div>
                `;
                filterContainer.appendChild(section);
            }
        }

        function toggleFilter(filterId) {
            const filter = document.getElementById(filterId);
            filter.style.display = filter.style.display === "none" ? "block" : "none";
        }

        function applyFilters() {
            const activeFilters = {
                heroTalent: new Set(),
                classTalents: new Set(),
                specTalents: new Set()
            };

            document.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
                const filterType = checkbox.getAttribute('data-filter');
                activeFilters[filterType].add(checkbox.value);
            });

            const filteredData = rawData.filter(row =>
                (activeFilters.heroTalent.size === 0 || activeFilters.heroTalent.has(row.hero_talent)) &&
                (activeFilters.classTalents.size === 0 || row.class_talents.every(talent => activeFilters.classTalents.has(talent))) &&
                (activeFilters.specTalents.size === 0 || row.spec_talents.every(talent => activeFilters.specTalents.has(talent)))
            );

            updateTable(filteredData);
        }

        function updateTable(data) {
            const tbody = document.querySelector('#dataTable tbody');
            tbody.innerHTML = '';

            data.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.build}</td>
                    <td data-value="${row.overall_rank}">${formatNumber(row.overall_rank)}</td>
                    ${reportTypes.map(type =>
                        `<td data-value="${row.metrics[type]}">${formatNumber(row.metrics[type])}</td>`
                    ).join('')}
                `;
                tbody.appendChild(tr);
            });

            updateColors(data);
        }

        function formatNumber(num) {
            if (num >= 1000000) {
                return (num / 1000000).toFixed(2) + 'M';
            } else if (num >= 1000) {
                return (num / 1000).toFixed(2) + 'K';
            }
            return num.toFixed(2);
        }

        function sortTable(n) {
            const sortedData = [...rawData].sort((a, b) => {
                if (n === 0) {
                    return a.build.localeCompare(b.build);
                } else if (n === 1) {
                    return a.overall_rank - b.overall_rank;
                } else {
                    const reportType = reportTypes[n - 2];
                    return b.metrics[reportType] - a.metrics[reportType];
                }
            });

            const table = document.getElementById("dataTable");
            if (table.getAttribute("data-sort-column") == n) {
                sortedData.reverse();
                table.removeAttribute("data-sort-column");
            } else {
                table.setAttribute("data-sort-column", n);
            }

            updateTable(sortedData);
        }

        function updateColors(data) {
            const table = document.getElementById("dataTable");
            const rows = table.getElementsByTagName("tr");
            const cols = rows[0].getElementsByTagName("th").length;

            for (let col = 2; col < cols; col++) {
                const reportType = reportTypes[col - 2];
                const allValues = rawData.map(row => row.metrics[reportType]);
                const min = Math.min(...allValues);
                const max = Math.max(...allValues);

                for (let i = 1; i < rows.length; i++) {
                    const cell = rows[i].cells[col];
                    const value = parseFloat(cell.getAttribute("data-value"));
                    cell.style.backgroundColor = getColor(value, min, max);
                }
            }
        }

        function getColor(value, min, max) {
            const ratio = (value - min) / (max - min);
            const hue = ratio * 120;
            return `hsl(${hue}, 80%, 90%)`;
        }

        // Initialize
        window.onload = function() {
            generateFilterHTML();
            updateTable(rawData);
        };
        </script>
    </body>
    </html>
    '''

    json_data_str = json.dumps(json_data)
    report_types_str = json.dumps(report_types)
    html = html_template.replace('$JSON_DATA', json_data_str).replace('$REPORT_TYPES', report_types_str).replace('$TABLE_HEADERS', table_headers)
    return html

def format_build_name(build):
    # Split the build name into parts
    parts = build.split('-')

    # Format the first part (hero and class talents)
    first_part = parts[0].replace('_', ', ')

    # Format the second part (spec talents)
    if len(parts) > 1:
        second_part = parts[1].replace('_', ', ')
        return f"{first_part} - {second_part}"
    else:
        return first_part

def main():
    data, report_types = collect_data()
    html = generate_html(data, report_types)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    main()