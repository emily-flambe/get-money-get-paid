"""
Static assets for the Paper Trading Dashboard.
Inlined as Python strings for Cloudflare Python Workers.
"""

INDEX_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paper Trading Dashboard</title>
    <link rel="stylesheet" href="css/styles.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
</head>
<body>
    <nav class="navbar">
        <h1>Paper Trading Dashboard</h1>
        <div class="nav-links">
            <a href="#" class="nav-link active" data-page="dashboard">Dashboard</a>
            <a href="#" class="nav-link" data-page="algorithms">Algorithms</a>
            <a href="#" class="nav-link" data-page="comparison">Comparison</a>
            <a href="https://github.com/emily-flambe/get-money-get-paid" target="_blank" rel="noopener noreferrer" class="github-link" aria-label="View on GitHub">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" aria-hidden="true">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
            </a>
        </div>
    </nav>

    <main class="container">
        <!-- Dashboard Page -->
        <div id="page-dashboard" class="page active">
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total Algorithms</h3>
                    <p id="total-algorithms">0</p>
                </div>
                <div class="stat-card">
                    <h3>Best Performer</h3>
                    <p id="best-performer">-</p>
                </div>
                <div class="stat-card">
                    <h3>Worst Performer</h3>
                    <p id="worst-performer">-</p>
                </div>
                <div class="stat-card">
                    <h3>Total Trades</h3>
                    <p id="total-trades">0</p>
                </div>
            </div>

            <div class="chart-container">
                <h2>Equity Curves</h2>
                <canvas id="equity-chart"></canvas>
            </div>

            <div class="recent-trades">
                <h2>Recent Trades</h2>
                <table id="trades-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Algorithm</th>
                            <th>Symbol</th>
                            <th>Side</th>
                            <th>Quantity</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>

        <!-- Algorithms Page -->
        <div id="page-algorithms" class="page">
            <div class="page-header">
                <h2>Algorithms</h2>
                <button id="btn-new-algorithm" class="btn btn-primary">+ New Algorithm</button>
            </div>

            <div id="algorithms-list" class="algorithms-grid"></div>

            <!-- New Algorithm Modal -->
            <div id="modal-algorithm" class="modal">
                <div class="modal-content">
                    <span class="close">&times;</span>
                    <h2 id="modal-title">New Algorithm</h2>
                    <form id="algorithm-form">
                        <input type="hidden" id="algo-id">
                        <div class="form-group">
                            <label for="algo-name">Name</label>
                            <input type="text" id="algo-name" required>
                        </div>
                        <div class="form-group">
                            <label for="algo-description">Description</label>
                            <textarea id="algo-description"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="algo-strategy">Strategy Type</label>
                            <select id="algo-strategy">
                                <option value="sma_crossover">SMA Crossover</option>
                                <option value="rsi">RSI Mean Reversion</option>
                                <option value="momentum">Momentum</option>
                                <option value="buy_and_hold">Buy and Hold</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="algo-symbols">Symbols (comma-separated)</label>
                            <input type="text" id="algo-symbols" placeholder="AAPL, GOOGL, MSFT">
                        </div>
                        <div id="strategy-config"></div>
                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">Save</button>
                            <button type="button" class="btn btn-secondary" id="btn-cancel">Cancel</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- Comparison Page -->
        <div id="page-comparison" class="page">
            <h2>Algorithm Comparison</h2>
            <div class="comparison-chart-container">
                <canvas id="comparison-chart"></canvas>
            </div>
            <table id="comparison-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Algorithm</th>
                        <th>Total Return</th>
                        <th>Sharpe Ratio</th>
                        <th>Max Drawdown</th>
                        <th>Trades</th>
                        <th>Days Active</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </main>

    <script src="js/api.js"></script>
    <script src="js/charts.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
'''

STYLES_CSS = '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    /* Forest Mint Dark Theme (default) */
    --primary: #10b981;
    --primary-dark: #059669;
    --secondary: #34d399;
    --accent: #a3e635;
    --success: #22c55e;
    --warning: #fbbf24;
    --danger: #f87171;
    --bg: #0f1a14;
    --bg-card: #1a2b22;
    --text: #ecfdf5;
    --text-muted: #86efac;
    --border: #2d4a3e;
}

[data-theme="light"] {
    /* Forest Mint Light Theme */
    --primary: #059669;
    --primary-dark: #047857;
    --secondary: #10b981;
    --accent: #65a30d;
    --success: #16a34a;
    --warning: #d97706;
    --danger: #dc2626;
    --bg: #ecfdf5;
    --bg-card: #d1fae5;
    --text: #064e3b;
    --text-muted: #047857;
    --border: #a7f3d0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
}

.navbar {
    background: var(--bg-card);
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
}

.navbar h1 {
    font-size: 1.5rem;
    color: var(--primary);
}

.nav-links {
    display: flex;
    gap: 2rem;
}

.nav-link {
    color: var(--text-muted);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
}

.nav-link:hover,
.nav-link.active {
    color: var(--primary);
}

.github-link {
    color: var(--text-muted);
    transition: color 0.2s;
    display: flex;
    align-items: center;
}

.github-link:hover {
    color: var(--text);
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
}

.page {
    display: none;
}

.page.active {
    display: block;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: var(--bg-card);
    padding: 1.5rem;
    border-radius: 0.5rem;
    border: 1px solid var(--border);
}

.stat-card h3 {
    color: var(--text-muted);
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
}

.stat-card p {
    font-size: 2rem;
    font-weight: 700;
}

.chart-container {
    background: var(--bg-card);
    padding: 1.5rem;
    border-radius: 0.5rem;
    border: 1px solid var(--border);
    margin-bottom: 2rem;
    height: 400px;
    position: relative;
}

.chart-container canvas {
    max-height: 320px;
}

.chart-container h2 {
    margin-bottom: 1rem;
    font-size: 1.25rem;
}

.recent-trades {
    background: var(--bg-card);
    padding: 1.5rem;
    border-radius: 0.5rem;
    border: 1px solid var(--border);
}

.recent-trades h2 {
    margin-bottom: 1rem;
    font-size: 1.25rem;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
}

th {
    color: var(--text-muted);
    font-weight: 500;
    font-size: 0.875rem;
}

.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
}

.btn {
    padding: 0.75rem 1.5rem;
    border-radius: 0.375rem;
    border: none;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
}

.btn-primary {
    background: var(--primary);
    color: white;
}

.btn-primary:hover {
    background: var(--primary-dark);
}

.btn-secondary {
    background: var(--border);
    color: var(--text);
}

.btn-secondary:hover {
    background: var(--text-muted);
}

.btn-danger {
    background: var(--danger);
    color: white;
}

.btn-sm {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
}

.algorithms-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
}

.algorithm-card {
    background: var(--bg-card);
    padding: 1.5rem;
    border-radius: 0.5rem;
    border: 1px solid var(--border);
}

.algorithm-card h3 {
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.algorithm-card .strategy-type {
    color: var(--text-muted);
    font-size: 0.875rem;
    margin-bottom: 1rem;
}

.algorithm-card .symbols {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.symbol-tag {
    background: var(--border);
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
}

.algorithm-card .actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
}

.toggle-switch {
    position: relative;
    width: 48px;
    height: 24px;
}

.toggle-switch input {
    display: none;
}

.toggle-switch label {
    display: block;
    width: 100%;
    height: 100%;
    background: var(--border);
    border-radius: 12px;
    cursor: pointer;
    transition: background 0.2s;
}

.toggle-switch input:checked + label {
    background: var(--success);
}

.toggle-switch label::after {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    transition: transform 0.2s;
}

.toggle-switch input:checked + label::after {
    transform: translateX(24px);
}

.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal.active {
    display: flex;
}

.modal-content {
    background: var(--bg-card);
    padding: 2rem;
    border-radius: 0.5rem;
    width: 100%;
    max-width: 500px;
    max-height: 90vh;
    overflow-y: auto;
}

.modal-content h2 {
    margin-bottom: 1.5rem;
}

.close {
    float: right;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--text-muted);
}

.close:hover {
    color: var(--text);
}

.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    color: var(--text-muted);
    font-size: 0.875rem;
}

.form-group input,
.form-group textarea,
.form-group select {
    width: 100%;
    padding: 0.75rem;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 0.375rem;
    color: var(--text);
    font-size: 1rem;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
    outline: none;
    border-color: var(--primary);
}

.form-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
}

.comparison-chart-container {
    background: var(--bg-card);
    padding: 1.5rem;
    border-radius: 0.5rem;
    border: 1px solid var(--border);
    margin-bottom: 2rem;
}

#comparison-table {
    background: var(--bg-card);
    border-radius: 0.5rem;
    border: 1px solid var(--border);
    overflow: hidden;
}

.positive {
    color: var(--success);
}

.negative {
    color: var(--danger);
}

.status-filled {
    color: var(--success);
}

.status-submitted {
    color: var(--warning);
}

.status-canceled,
.status-rejected {
    color: var(--danger);
}

/* Mobile responsive styles */
@media (max-width: 768px) {
    .navbar {
        flex-direction: column;
        gap: 1rem;
        padding: 1rem;
    }

    .navbar h1 {
        font-size: 1.25rem;
    }

    .nav-links {
        gap: 1rem;
        flex-wrap: wrap;
        justify-content: center;
    }

    .container {
        padding: 1rem;
    }

    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 0.75rem;
    }

    .stat-card {
        padding: 1rem;
    }

    .stat-card p {
        font-size: 1.5rem;
    }

    .chart-container {
        padding: 1rem;
        height: 350px;
    }

    .chart-container canvas {
        max-height: 270px;
    }

    .chart-container h2 {
        font-size: 1rem;
    }

    .algorithms-grid {
        grid-template-columns: 1fr;
    }

    .modal-content {
        margin: 1rem;
        padding: 1.5rem;
        max-height: 85vh;
    }

    table {
        font-size: 0.875rem;
    }

    th, td {
        padding: 0.5rem;
    }

    .page-header {
        flex-direction: column;
        gap: 1rem;
        align-items: stretch;
    }

    .btn {
        width: 100%;
        text-align: center;
    }
}

@media (max-width: 480px) {
    .stats-grid {
        grid-template-columns: 1fr;
    }

    .nav-links {
        gap: 0.75rem;
    }

    .nav-link {
        font-size: 0.875rem;
    }
}
'''

API_JS = '''// API Client for Paper Trading Dashboard

const API_BASE = '/api';

const api = {
    // Algorithms
    async getAlgorithms() {
        const response = await fetch(`${API_BASE}/algorithms`);
        return response.json();
    },

    async getAlgorithm(id) {
        const response = await fetch(`${API_BASE}/algorithms/${id}`);
        return response.json();
    },

    async createAlgorithm(data) {
        const response = await fetch(`${API_BASE}/algorithms`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return response.json();
    },

    async updateAlgorithm(id, data) {
        const response = await fetch(`${API_BASE}/algorithms/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return response.json();
    },

    async deleteAlgorithm(id) {
        const response = await fetch(`${API_BASE}/algorithms/${id}`, {
            method: 'DELETE'
        });
        return response.json();
    },

    // Algorithm sub-resources
    async getAlgorithmTrades(id) {
        const response = await fetch(`${API_BASE}/algorithms/${id}/trades`);
        return response.json();
    },

    async getAlgorithmSnapshots(id) {
        const response = await fetch(`${API_BASE}/algorithms/${id}/snapshots`);
        return response.json();
    },

    async getAlgorithmPositions(id) {
        const response = await fetch(`${API_BASE}/algorithms/${id}/positions`);
        return response.json();
    },

    async getAlgorithmPerformance(id) {
        const response = await fetch(`${API_BASE}/algorithms/${id}/performance`);
        return response.json();
    },

    // Comparison
    async getComparison() {
        const response = await fetch(`${API_BASE}/comparison`);
        return response.json();
    },

    // Account
    async getAccount() {
        const response = await fetch(`${API_BASE}/account`);
        return response.json();
    }
};
'''

CHARTS_JS = '''// Chart utilities for Paper Trading Dashboard

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

let equityChart = null;
let comparisonChart = null;

function getColor(index) {
    return COLORS[index % COLORS.length];
}

function renderEquityChart(algorithmsData) {
    const ctx = document.getElementById('equity-chart');
    if (!ctx) return;

    if (equityChart) {
        equityChart.destroy();
    }

    const datasets = algorithmsData.map((algo, index) => ({
        label: algo.name,
        data: algo.snapshots.map(s => ({
            x: new Date(s.snapshot_date),
            y: s.equity
        })),
        borderColor: getColor(index),
        backgroundColor: getColor(index) + '20',
        fill: false,
        tension: 0.1,
        pointRadius: 2
    }));

    equityChart = new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#f8fafc'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day'
                    },
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                y: {
                    beginAtZero: false,
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#94a3b8',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

function renderComparisonChart(comparisonData) {
    const ctx = document.getElementById('comparison-chart');
    if (!ctx) return;

    if (comparisonChart) {
        comparisonChart.destroy();
    }

    const labels = comparisonData.map(a => a.name);
    const returns = comparisonData.map(a => a.total_return_pct);
    const sharpe = comparisonData.map(a => a.sharpe_ratio);

    comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Total Return (%)',
                    data: returns,
                    backgroundColor: returns.map(r => r >= 0 ? '#10b981' : '#ef4444'),
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Return: ${context.parsed.y.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                y: {
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#94a3b8',
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

function renderRiskReturnScatter(comparisonData) {
    // Could add a risk/return scatter plot here
    // X-axis: Sharpe ratio or max drawdown
    // Y-axis: Total return
}
'''

APP_JS = '''// Main application logic for Paper Trading Dashboard

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
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
        });
    });
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
'''
