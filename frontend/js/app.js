// Main application logic for Paper Trading Dashboard

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initHamburgerMenu();
    initModal();
    initAlgorithmForm();
    loadDashboard();
});

// Navigation
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            showPage(page);

            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // Close mobile menu on navigation
            const hamburger = document.querySelector('.hamburger');
            const navLinksContainer = document.querySelector('.nav-links');
            if (hamburger && navLinksContainer) {
                hamburger.classList.remove('active');
                hamburger.setAttribute('aria-expanded', 'false');
                navLinksContainer.classList.remove('active');
            }
        });
    });
}

// Hamburger Menu
function initHamburgerMenu() {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');

    if (hamburger && navLinks) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navLinks.classList.toggle('active');
            const isExpanded = hamburger.classList.contains('active');
            hamburger.setAttribute('aria-expanded', isExpanded);
        });
    }
}

function showPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${pageName}`).classList.add('active');

    if (pageName === 'dashboard') {
        loadDashboard();
    } else if (pageName === 'algorithms') {
        loadAlgorithms();
    } else if (pageName === 'comparison') {
        loadComparison();
    }
}

// Safe text setter to avoid XSS
function setTextContent(element, text) {
    if (element) element.textContent = text;
}

// Dashboard
async function loadDashboard() {
    try {
        const [algosResponse, comparisonResponse] = await Promise.all([
            api.getAlgorithms(),
            api.getComparison()
        ]);

        const algorithms = algosResponse.algorithms || [];
        const comparison = comparisonResponse.comparison || [];

        // Update stats
        setTextContent(document.getElementById('total-algorithms'), algorithms.length);

        if (comparison.length > 0) {
            const best = comparison[0];
            const worst = comparison[comparison.length - 1];
            setTextContent(
                document.getElementById('best-performer'),
                `${best.name} (${best.total_return_pct > 0 ? '+' : ''}${best.total_return_pct}%)`
            );
            setTextContent(
                document.getElementById('worst-performer'),
                `${worst.name} (${worst.total_return_pct > 0 ? '+' : ''}${worst.total_return_pct}%)`
            );

            const totalTrades = comparison.reduce((sum, a) => sum + (a.total_trades || 0), 0);
            setTextContent(document.getElementById('total-trades'), totalTrades);
        }

        // Load equity curves
        const algorithmsWithSnapshots = await Promise.all(
            algorithms.map(async (algo) => {
                const snapshots = await api.getAlgorithmSnapshots(algo.id);
                return {
                    name: algo.name,
                    snapshots: snapshots.snapshots || []
                };
            })
        );

        if (algorithmsWithSnapshots.some(a => a.snapshots.length > 0)) {
            renderEquityChart(algorithmsWithSnapshots.filter(a => a.snapshots.length > 0));
        }

        // Load recent trades
        await loadRecentTrades(algorithms);

    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

async function loadRecentTrades(algorithms) {
    const tbody = document.querySelector('#trades-table tbody');
    // Clear existing rows safely
    while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
    }

    const allTrades = [];

    for (const algo of algorithms) {
        try {
            const response = await api.getAlgorithmTrades(algo.id);
            const trades = (response.trades || []).map(t => ({ ...t, algorithmName: algo.name }));
            allTrades.push(...trades);
        } catch (error) {
            console.error(`Error loading trades for ${algo.name}:`, error);
        }
    }

    // Sort by time and take most recent 10
    allTrades.sort((a, b) => new Date(b.submitted_at) - new Date(a.submitted_at));
    const recentTrades = allTrades.slice(0, 10);

    for (const trade of recentTrades) {
        const row = document.createElement('tr');

        const timeCell = document.createElement('td');
        timeCell.textContent = formatDate(trade.submitted_at);
        row.appendChild(timeCell);

        const algoCell = document.createElement('td');
        algoCell.textContent = trade.algorithmName;
        row.appendChild(algoCell);

        const symbolCell = document.createElement('td');
        symbolCell.textContent = trade.symbol;
        row.appendChild(symbolCell);

        const sideCell = document.createElement('td');
        sideCell.textContent = trade.side.toUpperCase();
        sideCell.className = trade.side === 'buy' ? 'positive' : 'negative';
        row.appendChild(sideCell);

        const qtyCell = document.createElement('td');
        qtyCell.textContent = trade.quantity;
        row.appendChild(qtyCell);

        const statusCell = document.createElement('td');
        statusCell.textContent = trade.status;
        statusCell.className = `status-${trade.status}`;
        row.appendChild(statusCell);

        tbody.appendChild(row);
    }

    if (recentTrades.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 6;
        cell.style.textAlign = 'center';
        cell.style.color = 'var(--text-muted)';
        cell.textContent = 'No trades yet';
        row.appendChild(cell);
        tbody.appendChild(row);
    }
}

// Algorithms
async function loadAlgorithms() {
    try {
        const response = await api.getAlgorithms();
        const algorithms = response.algorithms || [];

        const container = document.getElementById('algorithms-list');
        // Clear existing content safely
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }

        if (algorithms.length === 0) {
            const p = document.createElement('p');
            p.style.color = 'var(--text-muted)';
            p.textContent = 'No algorithms yet. Create your first one!';
            container.appendChild(p);
            return;
        }

        for (const algo of algorithms) {
            const card = createAlgorithmCard(algo);
            container.appendChild(card);
        }
    } catch (error) {
        console.error('Error loading algorithms:', error);
    }
}

function createAlgorithmCard(algo) {
    const card = document.createElement('div');
    card.className = 'algorithm-card';

    // Header with name and toggle
    const header = document.createElement('h3');
    const nameSpan = document.createElement('span');
    nameSpan.textContent = algo.name;
    header.appendChild(nameSpan);

    const toggleDiv = document.createElement('div');
    toggleDiv.className = 'toggle-switch';

    const toggleInput = document.createElement('input');
    toggleInput.type = 'checkbox';
    toggleInput.id = `toggle-${algo.id}`;
    toggleInput.checked = algo.enabled;

    const toggleLabel = document.createElement('label');
    toggleLabel.htmlFor = `toggle-${algo.id}`;

    toggleDiv.appendChild(toggleInput);
    toggleDiv.appendChild(toggleLabel);
    header.appendChild(toggleDiv);
    card.appendChild(header);

    // Strategy type
    const strategyP = document.createElement('p');
    strategyP.className = 'strategy-type';
    strategyP.textContent = formatStrategyType(algo.strategy_type);
    card.appendChild(strategyP);

    // Symbols
    const symbolsDiv = document.createElement('div');
    symbolsDiv.className = 'symbols';
    (algo.symbols || []).forEach(s => {
        const span = document.createElement('span');
        span.className = 'symbol-tag';
        span.textContent = s;
        symbolsDiv.appendChild(span);
    });
    card.appendChild(symbolsDiv);

    // Description
    const descP = document.createElement('p');
    descP.style.color = 'var(--text-muted)';
    descP.style.fontSize = '0.875rem';
    descP.textContent = algo.description || 'No description';
    card.appendChild(descP);

    // Actions
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'actions';

    const editBtn = document.createElement('button');
    editBtn.className = 'btn btn-sm btn-secondary';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => editAlgorithm(algo.id));
    actionsDiv.appendChild(editBtn);

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn btn-sm btn-danger';
    deleteBtn.textContent = 'Delete';
    deleteBtn.addEventListener('click', () => deleteAlgorithm(algo.id));
    actionsDiv.appendChild(deleteBtn);

    card.appendChild(actionsDiv);

    // Toggle handler
    toggleInput.addEventListener('change', async () => {
        await api.updateAlgorithm(algo.id, { enabled: toggleInput.checked });
    });

    return card;
}

function formatStrategyType(type) {
    const types = {
        'sma_crossover': 'SMA Crossover',
        'rsi': 'RSI Mean Reversion',
        'momentum': 'Momentum',
        'buy_and_hold': 'Buy and Hold'
    };
    return types[type] || type;
}

// Comparison
async function loadComparison() {
    try {
        const response = await api.getComparison();
        const comparison = response.comparison || [];

        if (comparison.length > 0) {
            renderComparisonChart(comparison);
        }

        const tbody = document.querySelector('#comparison-table tbody');
        // Clear existing rows safely
        while (tbody.firstChild) {
            tbody.removeChild(tbody.firstChild);
        }

        comparison.forEach((algo, index) => {
            const row = document.createElement('tr');

            const rankCell = document.createElement('td');
            rankCell.textContent = index + 1;
            row.appendChild(rankCell);

            const nameCell = document.createElement('td');
            nameCell.textContent = algo.name;
            row.appendChild(nameCell);

            const returnCell = document.createElement('td');
            returnCell.textContent = `${algo.total_return_pct > 0 ? '+' : ''}${algo.total_return_pct}%`;
            returnCell.className = algo.total_return_pct >= 0 ? 'positive' : 'negative';
            row.appendChild(returnCell);

            const sharpeCell = document.createElement('td');
            sharpeCell.textContent = algo.sharpe_ratio;
            row.appendChild(sharpeCell);

            const ddCell = document.createElement('td');
            ddCell.textContent = `${algo.max_drawdown_pct}%`;
            ddCell.className = 'negative';
            row.appendChild(ddCell);

            const tradesCell = document.createElement('td');
            tradesCell.textContent = algo.total_trades;
            row.appendChild(tradesCell);

            const daysCell = document.createElement('td');
            daysCell.textContent = algo.days_active;
            row.appendChild(daysCell);

            tbody.appendChild(row);
        });

        if (comparison.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 7;
            cell.style.textAlign = 'center';
            cell.style.color = 'var(--text-muted)';
            cell.textContent = 'No algorithms to compare';
            row.appendChild(cell);
            tbody.appendChild(row);
        }
    } catch (error) {
        console.error('Error loading comparison:', error);
    }
}

// Modal
function initModal() {
    const modal = document.getElementById('modal-algorithm');
    const btnNew = document.getElementById('btn-new-algorithm');
    const btnCancel = document.getElementById('btn-cancel');
    const closeBtn = modal.querySelector('.close');

    btnNew.addEventListener('click', () => {
        document.getElementById('modal-title').textContent = 'New Algorithm';
        document.getElementById('algorithm-form').reset();
        document.getElementById('algo-id').value = '';
        updateStrategyConfig();
        modal.classList.add('active');
    });

    btnCancel.addEventListener('click', () => modal.classList.remove('active'));
    closeBtn.addEventListener('click', () => modal.classList.remove('active'));
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.remove('active');
    });
}

// Algorithm Form
function initAlgorithmForm() {
    const form = document.getElementById('algorithm-form');
    const strategySelect = document.getElementById('algo-strategy');

    strategySelect.addEventListener('change', updateStrategyConfig);
    updateStrategyConfig();

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const id = document.getElementById('algo-id').value;
        const data = {
            name: document.getElementById('algo-name').value,
            description: document.getElementById('algo-description').value,
            strategy_type: document.getElementById('algo-strategy').value,
            symbols: document.getElementById('algo-symbols').value.split(',').map(s => s.trim()).filter(s => s),
            config: getStrategyConfig()
        };

        try {
            if (id) {
                await api.updateAlgorithm(id, data);
            } else {
                await api.createAlgorithm(data);
            }

            document.getElementById('modal-algorithm').classList.remove('active');
            loadAlgorithms();
        } catch (error) {
            console.error('Error saving algorithm:', error);
            alert('Error saving algorithm');
        }
    });
}

function updateStrategyConfig() {
    const strategy = document.getElementById('algo-strategy').value;
    const container = document.getElementById('strategy-config');

    // Clear existing content safely
    while (container.firstChild) {
        container.removeChild(container.firstChild);
    }

    const createFormGroup = (labelText, inputId, inputValue, inputType = 'number', min = null, max = null) => {
        const group = document.createElement('div');
        group.className = 'form-group';

        const label = document.createElement('label');
        label.htmlFor = inputId;
        label.textContent = labelText;
        group.appendChild(label);

        const input = document.createElement('input');
        input.type = inputType;
        input.id = inputId;
        input.value = inputValue;
        if (min !== null) input.min = min;
        if (max !== null) input.max = max;
        group.appendChild(input);

        return group;
    };

    if (strategy === 'sma_crossover') {
        container.appendChild(createFormGroup('Short SMA Period', 'config-short-period', '10', 'number', 1));
        container.appendChild(createFormGroup('Long SMA Period', 'config-long-period', '50', 'number', 1));
        container.appendChild(createFormGroup('Position Size (%)', 'config-position-size', '10', 'number', 1, 100));
    } else if (strategy === 'rsi') {
        container.appendChild(createFormGroup('RSI Period', 'config-period', '14', 'number', 1));
        container.appendChild(createFormGroup('Oversold Threshold', 'config-oversold', '30', 'number', 0, 100));
        container.appendChild(createFormGroup('Overbought Threshold', 'config-overbought', '70', 'number', 0, 100));
        container.appendChild(createFormGroup('Position Size (%)', 'config-position-size', '10', 'number', 1, 100));
    } else if (strategy === 'momentum') {
        container.appendChild(createFormGroup('Lookback Days', 'config-lookback', '20', 'number', 1));
        container.appendChild(createFormGroup('Threshold (%)', 'config-threshold', '5', 'number', 0));
        container.appendChild(createFormGroup('Position Size (%)', 'config-position-size', '10', 'number', 1, 100));
    } else if (strategy === 'buy_and_hold') {
        container.appendChild(createFormGroup('Position Size (%)', 'config-position-size', '100', 'number', 1, 100));
    }
}

function getStrategyConfig() {
    const strategy = document.getElementById('algo-strategy').value;
    const positionSize = (parseFloat(document.getElementById('config-position-size')?.value) || 10) / 100;

    switch (strategy) {
        case 'sma_crossover':
            return {
                short_period: parseInt(document.getElementById('config-short-period').value) || 10,
                long_period: parseInt(document.getElementById('config-long-period').value) || 50,
                position_size_pct: positionSize
            };
        case 'rsi':
            return {
                period: parseInt(document.getElementById('config-period').value) || 14,
                oversold: parseInt(document.getElementById('config-oversold').value) || 30,
                overbought: parseInt(document.getElementById('config-overbought').value) || 70,
                position_size_pct: positionSize
            };
        case 'momentum':
            return {
                lookback_days: parseInt(document.getElementById('config-lookback').value) || 20,
                threshold_pct: parseInt(document.getElementById('config-threshold').value) || 5,
                position_size_pct: positionSize
            };
        case 'buy_and_hold':
            return {
                position_size_pct: positionSize
            };
        default:
            return { position_size_pct: positionSize };
    }
}

// Edit/Delete functions
async function editAlgorithm(id) {
    try {
        const algo = await api.getAlgorithm(id);

        document.getElementById('modal-title').textContent = 'Edit Algorithm';
        document.getElementById('algo-id').value = id;
        document.getElementById('algo-name').value = algo.name;
        document.getElementById('algo-description').value = algo.description || '';
        document.getElementById('algo-strategy').value = algo.strategy_type;
        document.getElementById('algo-symbols').value = (algo.symbols || []).join(', ');

        updateStrategyConfig();

        // Fill config values
        const config = algo.config || {};
        const shortPeriod = document.getElementById('config-short-period');
        const longPeriod = document.getElementById('config-long-period');
        const period = document.getElementById('config-period');
        const oversold = document.getElementById('config-oversold');
        const overbought = document.getElementById('config-overbought');
        const lookback = document.getElementById('config-lookback');
        const threshold = document.getElementById('config-threshold');
        const positionSize = document.getElementById('config-position-size');

        if (shortPeriod && config.short_period) shortPeriod.value = config.short_period;
        if (longPeriod && config.long_period) longPeriod.value = config.long_period;
        if (period && config.period) period.value = config.period;
        if (oversold && config.oversold) oversold.value = config.oversold;
        if (overbought && config.overbought) overbought.value = config.overbought;
        if (lookback && config.lookback_days) lookback.value = config.lookback_days;
        if (threshold && config.threshold_pct) threshold.value = config.threshold_pct;
        if (positionSize && config.position_size_pct) positionSize.value = config.position_size_pct * 100;

        document.getElementById('modal-algorithm').classList.add('active');
    } catch (error) {
        console.error('Error loading algorithm:', error);
        alert('Error loading algorithm');
    }
}

async function deleteAlgorithm(id) {
    if (!confirm('Are you sure you want to delete this algorithm?')) return;

    try {
        await api.deleteAlgorithm(id);
        loadAlgorithms();
    } catch (error) {
        console.error('Error deleting algorithm:', error);
        alert('Error deleting algorithm');
    }
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString();
}
