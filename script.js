// const rawData = $JSON_DATA;
// const reportTypes = $REPORT_TYPES;

let globalTopValues = {};
let globalPercentages = {};
let currentSortColumn = 1; // Default to sorting by rank (assuming rank is the second column)
let currentSortDirection = 'asc'; // Default to ascending order
let bestAldrachi = {};
let bestFelscarred = {};
const bestBuilds = {};

function findBestBuilds(data, metric) {
    console.log(`Finding best builds for ${metric}:`, data);

    const aldrachiBuilds = data.filter(row => row.hero_talent.toLowerCase().includes('aldrachi'));
    const felscarredBuilds = data.filter(row =>
        row.hero_talent.toLowerCase().includes('felscarred') ||
        row.hero_talent.toLowerCase().includes('student') ||
        row.hero_talent.toLowerCase().includes('flamebound')
    );

    console.log("Aldrachi builds:", aldrachiBuilds);
    console.log("Felscarred builds:", felscarredBuilds);

    bestAldrachi = aldrachiBuilds.length > 0
        ? aldrachiBuilds.reduce((best, current) =>
            (current.metrics[metric] > best.metrics[metric]) ? current : best
        )
        : null;

    bestFelscarred = felscarredBuilds.length > 0
        ? felscarredBuilds.reduce((best, current) =>
            (current.metrics[metric] > best.metrics[metric]) ? current : best
        )
        : null;

    console.log(`Best Aldrachi build for ${metric}:`, bestAldrachi);
    console.log(`Best Felscarred build for ${metric}:`, bestFelscarred);

    return { bestAldrachi, bestFelscarred };
}

function createComparisonViz(metric) {
    const { bestAldrachi, bestFelscarred } = bestBuilds[metric];

    if (!bestAldrachi || !bestFelscarred) {
        return '<div class="comparison-viz"><span>Insufficient data</span></div>';
    }

    const aldrachiValue = bestAldrachi.metrics[metric] || 0;
    const felscarredValue = bestFelscarred.metrics[metric] || 0;

    if (aldrachiValue === 0 && felscarredValue === 0) {
        return '<div class="comparison-viz"><span>No data for this metric</span></div>';
    }

    let topBuild, bottomBuild, topValue, bottomValue;
    if (aldrachiValue > felscarredValue) {
        topBuild = 'Aldrachi';
        bottomBuild = 'Felscarred';
        topValue = aldrachiValue;
        bottomValue = felscarredValue;
    } else {
        topBuild = 'Felscarred';
        bottomBuild = 'Aldrachi';
        topValue = felscarredValue;
        bottomValue = aldrachiValue;
    }

    const percentageDiff = ((topValue - bottomValue) / bottomValue * 100).toFixed(2);
    const felscarredType = bestFelscarred.hero_talent.includes('Student') ? 'Student' : 'Flamebound';

    return `
        <div class="comparison-viz" title="Aldrachi: ${aldrachiValue.toFixed(2)}, Felscarred (${felscarredType}): ${felscarredValue.toFixed(2)}">
            <div class="viz-better ${topBuild.toLowerCase()}">${topBuild}${topBuild === 'Felscarred' ? ` (${felscarredType})` : ''}</div>
            <div class="viz-diff">does ${percentageDiff}% more damage</div>
            <div class="viz-worse">than ${bottomBuild}${bottomBuild === 'Felscarred' ? ` (${felscarredType})` : ''}</div>
        </div>
    `;
}

function updateComparisonViz(metric) {
    const vizContainer = document.querySelector(`th[data-metric="${metric}"] .comparison-viz`);
    if (vizContainer) {
        vizContainer.outerHTML = createComparisonViz(metric);
    }
}

// Add this function to calculate global top values and percentages
function calculateGlobalValues(data) {
    reportTypes.forEach(type => {
        const values = data.filter(r => r && r.metrics && r.metrics[type]).map(r => r.metrics[type]);
        globalTopValues[type] = Math.max(...values);
    });

    data.forEach(row => {
        if (row && row.metrics) {
            row.percentages = {};
            reportTypes.forEach(type => {
                const value = row.metrics[type] || 0;
                row.percentages[type] = globalTopValues[type] > 0
                    ? ((globalTopValues[type] - value) / globalTopValues[type] * 100).toFixed(2)
                    : '0.00';
            });
        }
    });
}

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
        let filterHTML = `<h3>${filterNames[filterType]}</h3><div class="filter-options ${filterType === 'specTalents' ? 'two-column' : ''}">`;

        Array.from(filterSet).forEach(value => {
            filterHTML += `
                <label class="mdc-checkbox">
                    <input type="checkbox" class="mdc-checkbox__native-control" checked data-filter="${filterType}" value="${value}"/>
                    <span class="mdc-checkbox__label">${value}</span>
                </label>`;
        });

        filterHTML += '</div>';
        section.innerHTML = filterHTML;
        filterContainer.appendChild(section);
    }
}

function applyFilters() {
    const activeFilters = {
        heroTalent: new Set(),
        classTalents: new Set(),
        specTalents: new Set()
    };

    document.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
        const filterType = checkbox.getAttribute('data-filter');
        if (activeFilters[filterType]) {
            activeFilters[filterType].add(checkbox.value);
        }
    });

    const filteredData = rawData.filter(row =>
        (activeFilters.heroTalent.size === 0 || activeFilters.heroTalent.has(row.hero_talent)) &&
        (activeFilters.classTalents.size === 0 || row.class_talents.every(talent => activeFilters.classTalents.has(talent))) &&
        (activeFilters.specTalents.size === 0 || row.spec_talents.every(talent => activeFilters.specTalents.has(talent)))
    );

    const sortedData = sortData(filteredData);
    updateTable(sortedData);
}

function updateTable(data) {
    const table = document.getElementById("dataTable");
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');

    // Clear existing header and body
    thead.innerHTML = '';
    tbody.innerHTML = '';

    // Create header row
    const headerRow = document.createElement('tr');
    headerRow.className = 'mdc-data-table__header-row';

    // Add Build and Rank headers
    headerRow.innerHTML = `
        <th class="mdc-data-table__header-cell build-name" role="columnheader" scope="col">Build</th>
        <th class="mdc-data-table__header-cell rank" role="columnheader" scope="col" onclick="sortTable(1)">
            Rank <i class="material-icons sort-icon">arrow_downward</i>
        </th>
    `;

    // Add metric headers with comparison viz
    reportTypes.forEach((type, index) => {
        const th = document.createElement('th');
        th.className = 'mdc-data-table__header-cell';
        th.setAttribute('role', 'columnheader');
        th.setAttribute('scope', 'col');
        th.setAttribute('onclick', `sortTable(${index + 2})`);
        th.setAttribute('data-metric', type);
        th.innerHTML = `
            ${type}
            <i class="material-icons sort-icon">arrow_downward</i>
            ${createComparisonViz(type)}
        `;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);

    // Create table body
    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.className = 'mdc-data-table__row';

        // Build name column
        const buildNameCell = document.createElement('td');
        buildNameCell.className = 'mdc-data-table__cell build-name';
        buildNameCell.innerHTML = formatBuildName(row);
        tr.appendChild(buildNameCell);

        // Rank column
        const rankCell = document.createElement('td');
        rankCell.className = 'mdc-data-table__cell rank';
        rankCell.setAttribute('data-value', row.overall_rank || '');
        rankCell.textContent = row.overall_rank || 'N/A';
        tr.appendChild(rankCell);

        // Metric columns
        reportTypes.forEach(type => {
            const value = row.metrics && row.metrics[type] ? row.metrics[type] : 0;
            const percentage = row.percentages[type];
            const barColor = getBarColor(parseFloat(percentage));

            const metricCell = document.createElement('td');
            metricCell.className = 'mdc-data-table__cell';
            metricCell.setAttribute('data-value', value);
            metricCell.innerHTML = `
                <div class="metric-container">
                    <span class="metric-value">${formatNumber(value)}</span>
                    <span class="metric-diff">(-${percentage}%)</span>
                </div>
                <div class="linear-progress">
                    <div class="linear-progress-bar" style="width: ${100 - parseFloat(percentage)}%; background-color: ${barColor};"></div>
                </div>
            `;
            tr.appendChild(metricCell);
        });

        tbody.appendChild(tr);
    });

    // Update sort indicators
    table.querySelectorAll('.sort-icon').forEach((icon, index) => {
        if (index === currentSortColumn) {
            icon.textContent = currentSortDirection === 'asc' ? 'arrow_upward' : 'arrow_downward';
        } else {
            icon.textContent = 'arrow_downward';
        }
    });
}

function toggleExpand(row) {
    const buildNameContainer = row.querySelector('.build-name-container');
    const expandIcon = row.querySelector('.expand-button i');

    if (buildNameContainer.classList.contains('collapsed')) {
        buildNameContainer.classList.remove('collapsed');
        buildNameContainer.classList.add('expanded');
        expandIcon.textContent = 'expand_more';
    } else {
        buildNameContainer.classList.remove('expanded');
        buildNameContainer.classList.add('collapsed');
        expandIcon.textContent = 'chevron_right';
    }
}

function formatBuildName(row) {
    if (!row) return '';

    const heroTalent = row.hero_talent ? `<span class="chip chip-hero ${row.hero_talent.toLowerCase().includes('aldrachi') ? 'aldrachi' : 'felscarred'}" title="Hero Talent: ${row.hero_talent}">${row.hero_talent}</span>` : '';
    const classTalents = row.class_talents && Array.isArray(row.class_talents) ? row.class_talents.map(talent =>
        `<span class="chip chip-class" title="Class Talent: ${talent}">${talent}</span>`
    ).join('') : '';
    const specTalents = row.spec_talents && Array.isArray(row.spec_talents) ? row.spec_talents.map(talent =>
        `<span class="chip chip-spec" title="Spec Talent: ${talent}">${talent}</span>`
    ).join('') : '';

    return `
        <div class="build-name-container">
            <div class="build-name-line">${heroTalent}${classTalents}</div>
            <div class="build-name-line">${specTalents}</div>
        </div>
    `;
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(2) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(2) + 'K';
    }
    return num.toFixed(2);
}

function getBarColor(percentage) {
    // Define color stops using Material Design colors
    const colorStops = [
        { percent: 0, color: '#4CAF50' },   // Material Green 500
        { percent: 2, color: '#8BC34A' },   // Material Light Green 500
        { percent: 5, color: '#CDDC39' },   // Material Lime 500
        { percent: 10, color: '#FFEB3B' },  // Material Yellow 500
        { percent: 15, color: '#FFC107' },  // Material Amber 500
        { percent: 20, color: '#FF9800' },  // Material Orange 500
        { percent: 30, color: '#FF5722' },  // Material Deep Orange 500
        { percent: 100, color: '#F44336' }  // Material Red 500
    ];

    // Find the appropriate color stop
    for (let i = 0; i < colorStops.length - 1; i++) {
        if (percentage <= colorStops[i + 1].percent) {
            const t = (percentage - colorStops[i].percent) / (colorStops[i + 1].percent - colorStops[i].percent);
            return interpolateColor(colorStops[i].color, colorStops[i + 1].color, t);
        }
    }

    // If percentage is greater than 100, return the last color
    return colorStops[colorStops.length - 1].color;
}

function interpolateColor(color1, color2, t) {
    const r1 = parseInt(color1.slice(1, 3), 16);
    const g1 = parseInt(color1.slice(3, 5), 16);
    const b1 = parseInt(color1.slice(5, 7), 16);

    const r2 = parseInt(color2.slice(1, 3), 16);
    const g2 = parseInt(color2.slice(3, 5), 16);
    const b2 = parseInt(color2.slice(5, 7), 16);

    const r = Math.round(r1 * (1 - t) + r2 * t);
    const g = Math.round(g1 * (1 - t) + g2 * t);
    const b = Math.round(b1 * (1 - t) + b2 * t);

    return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, '0')}`;
}

function sortTable(n) {
    const table = document.getElementById("dataTable");
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const th = table.querySelectorAll('th')[n];
    const icon = th.querySelector('.sort-icon');

    const isAscending = icon.textContent === 'arrow_upward';
    const newDirection = isAscending ? 'desc' : 'asc';

    rows.sort((a, b) => {
        let aValue, bValue;
        if (n === 0) {
            aValue = a.cells[n].textContent;
            bValue = b.cells[n].textContent;
        } else {
            aValue = parseFloat(a.cells[n].getAttribute('data-value'));
            bValue = parseFloat(b.cells[n].getAttribute('data-value'));
        }

        if (aValue < bValue) return newDirection === 'asc' ? -1 : 1;
        if (aValue > bValue) return newDirection === 'asc' ? 1 : -1;
        return 0;
    });

    rows.forEach(row => tbody.appendChild(row));

    updateSortIndicator(n, newDirection);
}

function sortData(data) {
    return data.sort((a, b) => {
        let aValue, bValue;
        if (currentSortColumn === 0) {
            aValue = a.full_name;
            bValue = b.full_name;
        } else if (currentSortColumn === 1) {
            aValue = a.overall_rank || Infinity;
            bValue = b.overall_rank || Infinity;
        } else {
            const metricType = reportTypes[currentSortColumn - 2];
            aValue = a.metrics[metricType] || 0;
            bValue = b.metrics[metricType] || 0;
        }

        if (aValue < bValue) return currentSortDirection === 'asc' ? -1 : 1;
        if (aValue > bValue) return currentSortDirection === 'asc' ? 1 : -1;
        return 0;
    });
}
function updateSortIndicator(columnIndex, direction) {
    const headers = document.querySelectorAll('.mdc-data-table__header-cell');
    headers.forEach((header, index) => {
        const icon = header.querySelector('.sort-icon');
        if (icon) {
            if (index === columnIndex) {
                icon.textContent = direction === 'asc' ? 'arrow_upward' : 'arrow_downward';
                icon.classList.add('active');
            } else {
                icon.textContent = 'arrow_downward';
                icon.classList.remove('active');
            }
        }
    });
}

// Initialize

function initializeData(rawData) {
    console.log("Initializing data with:", rawData);
    if (!Array.isArray(rawData) || rawData.length === 0) {
        console.error("rawData is empty or not an array");
        return;
    }
    calculateGlobalValues(rawData);

    // Find best builds for each metric
    reportTypes.forEach(metric => {
        bestBuilds[metric] = findBestBuilds(rawData, metric);
    });

    // Sort the data by 1T 300s descending
    rawData.sort((a, b) => b.metrics['1T 300s'] - a.metrics['1T 300s']);

    updateTable(rawData);

    // Add change event listeners to checkboxes
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', applyFilters);
    });

    // Update sort indicator for 1T 300s
    updateSortIndicator(reportTypes.indexOf('1T 300s') + 2, 'desc');
}

window.onload = function() {
    generateFilterHTML();
    initializeData(rawData);

    // Add change event listeners to checkboxes
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', applyFilters);
    });
};