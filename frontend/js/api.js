// API Client for Paper Trading Dashboard

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
