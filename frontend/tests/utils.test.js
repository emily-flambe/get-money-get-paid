import { describe, it, expect } from 'vitest';
import {
    getColor,
    formatCurrency,
    formatPercentage,
    parseSnapshotsForChart,
    calculateReturnFromSnapshots,
    sortAlgorithmsByMetric,
    getBestAndWorst,
} from '../js/utils.js';

describe('getColor', () => {
    it('returns first color for index 0', () => {
        expect(getColor(0)).toBe('#3b82f6');
    });

    it('returns different colors for different indices', () => {
        expect(getColor(0)).not.toBe(getColor(1));
        expect(getColor(1)).toBe('#10b981');
    });

    it('wraps around for indices beyond palette length', () => {
        expect(getColor(8)).toBe('#3b82f6'); // Same as index 0
        expect(getColor(9)).toBe('#10b981'); // Same as index 1
    });
});

describe('formatCurrency', () => {
    it('formats positive numbers', () => {
        expect(formatCurrency(1000)).toBe('$1,000.00');
    });

    it('formats decimal numbers', () => {
        expect(formatCurrency(1234.56)).toBe('$1,234.56');
    });

    it('formats zero', () => {
        expect(formatCurrency(0)).toBe('$0.00');
    });

    it('formats large numbers', () => {
        expect(formatCurrency(1000000)).toBe('$1,000,000.00');
    });
});

describe('formatPercentage', () => {
    it('formats positive percentages', () => {
        expect(formatPercentage(10.5)).toBe('10.50%');
    });

    it('formats negative percentages', () => {
        expect(formatPercentage(-5.25)).toBe('-5.25%');
    });

    it('formats zero', () => {
        expect(formatPercentage(0)).toBe('0.00%');
    });
});

describe('parseSnapshotsForChart', () => {
    it('converts snapshots to chart points', () => {
        const snapshots = [
            { snapshot_date: '2024-01-01', equity: 10000 },
            { snapshot_date: '2024-01-02', equity: 10500 },
        ];
        const result = parseSnapshotsForChart(snapshots);

        expect(result).toHaveLength(2);
        expect(result[0].y).toBe(10000);
        expect(result[1].y).toBe(10500);
        expect(result[0].x).toBeInstanceOf(Date);
    });

    it('handles empty array', () => {
        expect(parseSnapshotsForChart([])).toEqual([]);
    });
});

describe('calculateReturnFromSnapshots', () => {
    it('calculates positive return', () => {
        const snapshots = [
            { equity: 10000 },
            { equity: 10500 },
            { equity: 11000 },
        ];
        expect(calculateReturnFromSnapshots(snapshots)).toBe(10);
    });

    it('calculates negative return', () => {
        const snapshots = [
            { equity: 10000 },
            { equity: 9500 },
            { equity: 9000 },
        ];
        expect(calculateReturnFromSnapshots(snapshots)).toBe(-10);
    });

    it('returns 0 for empty or single snapshot', () => {
        expect(calculateReturnFromSnapshots([])).toBe(0);
        expect(calculateReturnFromSnapshots([{ equity: 10000 }])).toBe(0);
    });

    it('handles null/undefined', () => {
        expect(calculateReturnFromSnapshots(null)).toBe(0);
        expect(calculateReturnFromSnapshots(undefined)).toBe(0);
    });
});

describe('sortAlgorithmsByMetric', () => {
    const algorithms = [
        { name: 'A', total_return_pct: 5 },
        { name: 'B', total_return_pct: 15 },
        { name: 'C', total_return_pct: -3 },
    ];

    it('sorts descending by default', () => {
        const result = sortAlgorithmsByMetric(algorithms, 'total_return_pct');
        expect(result[0].name).toBe('B');
        expect(result[1].name).toBe('A');
        expect(result[2].name).toBe('C');
    });

    it('sorts ascending when specified', () => {
        const result = sortAlgorithmsByMetric(algorithms, 'total_return_pct', true);
        expect(result[0].name).toBe('C');
        expect(result[2].name).toBe('B');
    });

    it('does not mutate original array', () => {
        const original = [...algorithms];
        sortAlgorithmsByMetric(algorithms, 'total_return_pct');
        expect(algorithms).toEqual(original);
    });
});

describe('getBestAndWorst', () => {
    it('returns best and worst performers', () => {
        const comparison = [
            { name: 'A', total_return_pct: 5 },
            { name: 'B', total_return_pct: 15 },
            { name: 'C', total_return_pct: -3 },
        ];
        const result = getBestAndWorst(comparison);
        expect(result.best.name).toBe('B');
        expect(result.worst.name).toBe('C');
    });

    it('handles empty array', () => {
        const result = getBestAndWorst([]);
        expect(result.best).toBeNull();
        expect(result.worst).toBeNull();
    });

    it('handles null/undefined', () => {
        expect(getBestAndWorst(null).best).toBeNull();
        expect(getBestAndWorst(undefined).best).toBeNull();
    });
});
