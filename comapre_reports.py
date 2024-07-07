import os
import re
from collections import defaultdict

def format_number(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return f"{num:.1f}"

def extract_chart_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    print(f"Processing file: {file_path}")

    match = re.search(r'{"series":\[{"name":"Damage per Second","data":\[(.*?)\]}', content, re.DOTALL)
    if not match:
        print("No matching data found")
        return None

    data_string = match.group(1)

    data_pattern = r'{"name":"(.*?)","reldiff":.*?,"y":([\d.]+)}'
    data_matches = re.findall(data_pattern, data_string)

    if not data_matches:
        print("Failed to extract data from the matched string")
        return None

    result = {name: float(y) for name, y in data_matches}

    print(f"Extracted data: {result}")
    return result

def extract_filename_info(filename):
    match = re.search(r'targets(\d+)_time(\d+)', filename)
    if match:
        targets = int(match.group(1))
        time = int(match.group(2))
        return f"{targets}T {time}s", targets
    print(f"Warning: Couldn't extract target and time info from filename: {filename}")
    return None, None

def get_color(value, min_val, max_val):
    ratio = (value - min_val) / (max_val - min_val)
    colors = [
        "#f0f9f0", "#e1f3e1", "#d2eed2", "#c3e8c3", "#b4e2b4",
        "#a5dca5", "#96d696", "#87d087", "#78ca78", "#69c469"
    ]
    index = min(int(ratio * (len(colors) - 1)), len(colors) - 1)
    return colors[index]

def calculate_ranks(summaries):
    ranks = defaultdict(dict)
    all_profiles = set()
    for summary in summaries.values():
        all_profiles.update(summary["data"].keys())

    valid_profiles = set()
    for profile in all_profiles:
        if all(profile in summary["data"] for summary in summaries.values()):
            valid_profiles.add(profile)

    for target_count in summaries:
        sorted_profiles = sorted(
            [(profile, summaries[target_count]["data"][profile]) for profile in valid_profiles],
            key=lambda x: x[1],
            reverse=True
        )
        for rank, (profile, _) in enumerate(sorted_profiles, 1):
            ranks[profile][target_count] = rank

    return ranks, valid_profiles

def calculate_average_rank(ranks):
    return {profile: sum(ranks[profile].values()) / len(ranks[profile]) for profile in ranks}

def compare_chart_data():
    summaries = {}
    for filename in os.listdir('.'):
        if filename.endswith('.html'):
            file_path = os.path.join('.', filename)
            summary = extract_chart_data(file_path)
            if summary:
                column_name, target_count = extract_filename_info(filename)
                if column_name and target_count:
                    if target_count not in summaries or os.path.getmtime(file_path) > summaries[target_count]["date"]:
                        summaries[target_count] = {"data": summary, "column_name": column_name, "date": os.path.getmtime(file_path)}

    if not summaries:
        print("No data extracted from any files")
        return None

    sorted_columns = sorted(summaries.keys())

    ranks, valid_profiles = calculate_ranks(summaries)
    avg_ranks = calculate_average_rank(ranks)

    html = ['''
    <style>
        body { font-family: 'Roboto', 'Helvetica', 'Arial', sans-serif; background-color: #f5f5f5; }
        table { border-collapse: separate; border-spacing: 0; width: 100%; max-width: 1000px; margin: 20px auto; box-shadow: 0 1px 3px rgba(0,0,0,0.2); background-color: #ffffff; }
        th, td { text-align: right; padding: 12px; border-bottom: 1px solid #e0e0e0; }
        th { background-color: #f5f5f5; color: #333333; font-weight: 500; position: sticky; top: 0; }
        td { color: #212121; }
        th:first-child, td:first-child { text-align: left; position: sticky; left: 0; background-color: #ffffff; }
        tr:nth-child(even) { background-color: #fafafa; }
        tr:hover { background-color: #f1f8e9; }
        th:hover { cursor: pointer; background-color: #e8e8e8; }
    </style>
    <table id="dataTable">
    <tr><th onclick="sortTable(0)">Profile</th>
    ''']

    for i, target_count in enumerate(sorted_columns, 1):
        html.append(f'<th onclick="sortTable({i})">{summaries[target_count]["column_name"]}</th>')
    html.append('<th onclick="sortTable({})" style="background-color: #e8f5e9;">Avg Rank</th>'.format(len(sorted_columns) + 1))
    html.append('</tr>')

    column_stats = {target_count: {'min': min(summaries[target_count]["data"].values()), 'max': max(summaries[target_count]["data"].values())}
                    for target_count in sorted_columns}

    for profile in sorted(valid_profiles):
        html.append(f'<tr><td>{profile}</td>')
        for target_count in sorted_columns:
            value = summaries[target_count]["data"].get(profile, 'N/A')
            if isinstance(value, float):
                formatted_value = format_number(value)
                color = get_color(value, column_stats[target_count]['min'], column_stats[target_count]['max'])
                rank = ranks[profile][target_count]
                html.append(f'<td data-value="{rank}" style="background-color: {color};">{formatted_value}<br><small>(Rank: {rank})</small></td>')
            else:
                html.append(f'<td data-value="0">N/A</td>')

        # Add average rank column
        avg_rank = avg_ranks[profile]
        html.append(f'<td data-value="{avg_rank}" style="background-color: #e8f5e9;">{format_number(avg_rank)}</td>')

        html.append('</tr>')

    html.append('</table>')

    # Add JavaScript for sorting (unchanged)
    html.append('''
    <script>
    function sortTable(n) {
        var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
        table = document.getElementById("dataTable");
        switching = true;
        dir = "asc";
        while (switching) {
            switching = false;
            rows = table.rows;
            for (i = 1; i < (rows.length - 1); i++) {
                shouldSwitch = false;
                x = rows[i].getElementsByTagName("TD")[n];
                y = rows[i + 1].getElementsByTagName("TD")[n];
                if (dir == "asc") {
                    if ((n == 0 && x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) ||
                        (n != 0 && parseFloat(x.getAttribute("data-value")) > parseFloat(y.getAttribute("data-value")))) {
                        shouldSwitch = true;
                        break;
                    }
                } else if (dir == "desc") {
                    if ((n == 0 && x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) ||
                        (n != 0 && parseFloat(x.getAttribute("data-value")) < parseFloat(y.getAttribute("data-value")))) {
                        shouldSwitch = true;
                        break;
                    }
                }
            }
            if (shouldSwitch) {
                rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                switching = true;
                switchcount++;
            } else {
                if (switchcount == 0 && dir == "asc") {
                    dir = "desc";
                    switching = true;
                }
            }
        }
    }
    </script>
    ''')

    return ''.join(html)

def main():
    html_table = compare_chart_data()

    if html_table:
        with open('chart_data_comparison.html', 'w', encoding='utf-8') as f:
            f.write('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Chart Data Comparison</title>\n</head>\n<body>\n')
            f.write(html_table)
            f.write('\n</body>\n</html>')

        print("Comparison table has been saved to 'chart_data_comparison.html'")
    else:
        print("No comparison table generated due to lack of data.")

if __name__ == "__main__":
    main()