// const rawData = $JSON_DATA;
// const reportTypes = $REPORT_TYPES;

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
  if (!rawData || !Array.isArray(rawData)) {
        console.error('Raw data is not available or is not an array');
        return;
    }
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

    updateTable(filteredData);
}

function updateTable(data) {
    const tbody = document.querySelector('#dataTable tbody');
    tbody.innerHTML = '';

    data.forEach(row => {
        if (!row || typeof row !== 'object') {
            console.error('Invalid row data:', row);
            return;
        }

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
            const topValue = Math.max(...data.filter(r => r && r.metrics && r.metrics[type]).map(r => r.metrics[type]));
            const percentage = topValue > 0 ? ((topValue - value) / topValue * 100).toFixed(2) : '0.00';
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

    const heroTalent = row.hero_talent ? `<span class="chip chip-hero" title="Hero Talent: ${row.hero_talent}">${row.hero_talent}</span>` : '';
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

    rows.sort((a, b) => {
        let aValue, bValue;
        if (n === 0) {
            aValue = a.cells[n].textContent;
            bValue = b.cells[n].textContent;
        } else {
            aValue = parseFloat(a.cells[n].getAttribute('data-value'));
            bValue = parseFloat(b.cells[n].getAttribute('data-value'));
        }

        if (aValue < bValue) return isAscending ? -1 : 1;
        if (aValue > bValue) return isAscending ? 1 : -1;
        return 0;
    });

    rows.forEach(row => tbody.appendChild(row));

    // Update all icons
    table.querySelectorAll('.sort-icon').forEach(i => i.textContent = 'arrow_downward');
    icon.textContent = isAscending ? 'arrow_downward' : 'arrow_upward';
}

// Initialize
window.onload = function() {
    generateFilterHTML();
    updateTable(rawData);

    // Add change event listeners to checkboxes
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', applyFilters);
    });
};