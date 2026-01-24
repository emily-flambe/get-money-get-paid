-- Migration: Add cash column to algorithms table for virtual account tracking
-- This enables per-algorithm cash balance independent of positions

-- Add cash column with default starting balance of 1000
ALTER TABLE algorithms ADD COLUMN cash REAL NOT NULL DEFAULT 1000;

-- Store the default starting balance in system_state for reference
INSERT INTO system_state (key, value) VALUES ('default_starting_balance', '1000')
ON CONFLICT(key) DO NOTHING;

-- Update existing algorithms: cash = starting_balance - sum(position value)
-- Position value = quantity * avg_entry_price
-- Minimum cash is 0 (can't go negative from this migration)
UPDATE algorithms
SET cash = MAX(0, 1000 - COALESCE(
    (SELECT SUM(quantity * avg_entry_price) FROM positions WHERE positions.algorithm_id = algorithms.id),
    0
));
