// Utility functions for Paper Trading Dashboard

/**
 * Get a color from the color palette by index
 * @param {number} index - Index into the color palette
 * @returns {string} Hex color code
 */
export function getColor(index) {
    const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];
    return COLORS[index % COLORS.length];
}

/**
 * Format a number as currency
 * @param {number} value - Value to format
 * @returns {string} Formatted currency string
 */
export function formatCurrency(value) {
    return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/**
 * Format a number as percentage
 * @param {number} value - Value to format
 * @returns {string} Formatted percentage string
 */
export function formatPercentage(value) {
    return value.toFixed(2) + '%';
}

/**
 * Parse snapshots data for charting
 * @param {Array} snapshots - Array of snapshot objects
 * @returns {Array} Array of {x, y} points for charting
 */
export function parseSnapshotsForChart(snapshots) {
    return snapshots.map(s => ({
        x: new Date(s.snapshot_date),
        y: s.equity
    }));
}

/**
 * Calculate the total return from snapshots
 * @param {Array} snapshots - Array of snapshot objects with equity
 * @returns {number} Total return as percentage
 */
export function calculateReturnFromSnapshots(snapshots) {
    if (!snapshots || snapshots.length < 2) {
        return 0;
    }
    const initial = snapshots[0].equity;
    const final = snapshots[snapshots.length - 1].equity;
    if (initial === 0) return 0;
    return ((final - initial) / initial) * 100;
}

/**
 * Sort algorithms by performance metric
 * @param {Array} algorithms - Array of algorithm objects with performance data
 * @param {string} metric - Metric to sort by (e.g., 'total_return_pct', 'sharpe_ratio')
 * @param {boolean} ascending - Sort direction
 * @returns {Array} Sorted array
 */
export function sortAlgorithmsByMetric(algorithms, metric, ascending = false) {
    return [...algorithms].sort((a, b) => {
        const diff = (a[metric] || 0) - (b[metric] || 0);
        return ascending ? diff : -diff;
    });
}

/**
 * Get best and worst performing algorithms
 * @param {Array} comparison - Array of comparison data
 * @returns {Object} Object with best and worst algorithms
 */
export function getBestAndWorst(comparison) {
    if (!comparison || comparison.length === 0) {
        return { best: null, worst: null };
    }
    const sorted = sortAlgorithmsByMetric(comparison, 'total_return_pct');
    return {
        best: sorted[0],
        worst: sorted[sorted.length - 1]
    };
}
