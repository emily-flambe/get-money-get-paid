// Chart utilities for Paper Trading Dashboard

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
