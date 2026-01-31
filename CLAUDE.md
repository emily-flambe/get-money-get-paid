# Claude Guidelines

## Deployment

```bash
cd dashboard-api && npm run deploy
```

Worker: `get-money-get-paid` at https://stonks.emilycogsdill.com

## Key Constraints

- **Python Workers**: No pip packages in Pyodide - use built-ins or inline code
- **Static assets**: Inlined in `static_assets.py` (no Workers Sites for Python)
- **D1 queries**: Use `js_to_py()` helper to convert JsProxy objects
- **Frontend API**: Uses relative URLs (`/api`) - same origin as worker

## Testing

```bash
cd dashboard-api && python3 -m pytest tests/ -v  # API tests
cd frontend && npm test                           # Frontend tests
```

## Files to Update Together

When changing frontend:
1. `frontend/index.html` + `frontend/css/styles.css` + `frontend/js/*.js`
2. `dashboard-api/src/static_assets.py` (sync inlined copies)

## PC Access

SSH to the PC is available. Check `~/.zshrc` for the `pc` alias command.
- Windows 11 + WSL2 Ubuntu
- Dagster instance running at http://pceus:3000
- Python 3.12 available in WSL

## Real-time Trading Engine

WebSocket-based trading in `realtime/` - runs on the PC, not Cloudflare.

```bash
# Setup (run from WSL2)
cd /mnt/c/Users/emily/Documents/GitHub/get-money-get-paid/realtime
./scripts/setup.sh

# Run as service
sudo systemctl start trading-engine
sudo journalctl -u trading-engine -f
```

- Strategies defined in `realtime/config/strategies.yaml`
- Add new strategy types in `realtime/src/strategies/`
- Dagster monitors health and syncs data to D1
