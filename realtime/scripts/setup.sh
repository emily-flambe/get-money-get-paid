#!/bin/bash
# Setup script for real-time trading engine on WSL2
# Run this from within WSL2 Ubuntu

set -e

echo "=== Real-time Trading Engine Setup ==="

# Check we're in WSL
if [ ! -f /proc/version ] || ! grep -qi microsoft /proc/version; then
    echo "This script should be run from WSL2 Ubuntu"
    exit 1
fi

# Variables
REPO_DIR="/mnt/c/Users/emily/Documents/GitHub/get-money-get-paid/realtime"
VENV="/opt/dagster/venv"
SERVICE_FILE="/etc/systemd/system/trading-engine.service"

# Install Python dependencies
echo "Installing Python dependencies..."
$VENV/bin/pip install websockets alpaca-py asyncpg pyyaml httpx orjson

# Create trading database in Postgres
echo "Creating trading database..."
sudo -u postgres psql -c "CREATE DATABASE trading OWNER dagster;" 2>/dev/null || echo "Database may already exist"

# Copy service file
echo "Installing systemd service..."
sudo cp "$REPO_DIR/scripts/trading-engine.service" "$SERVICE_FILE"

# Prompt for API keys
echo ""
echo "Enter your Alpaca API credentials (paper trading):"
read -p "API Key: " ALPACA_API_KEY
read -p "Secret Key: " ALPACA_SECRET_KEY

# Update service file with API keys
sudo sed -i "s/your_api_key_here/$ALPACA_API_KEY/" "$SERVICE_FILE"
sudo sed -i "s/your_secret_key_here/$ALPACA_SECRET_KEY/" "$SERVICE_FILE"

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable service (but don't start yet)
sudo systemctl enable trading-engine

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start the trading engine:"
echo "  sudo systemctl start trading-engine"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u trading-engine -f"
echo ""
echo "To test without systemd:"
echo "  cd $REPO_DIR"
echo "  ALPACA_API_KEY=xxx ALPACA_SECRET_KEY=xxx $VENV/bin/python -m src.main"
echo ""
