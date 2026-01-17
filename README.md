# Get Money Get Paid

Paper trading platform for comparing algorithmic trading strategies.

**Live**: https://stonks.emilycogsdill.com

## Stack

- **Runtime**: Cloudflare Workers (Python via Pyodide)
- **Database**: Cloudflare D1 (SQLite)
- **Frontend**: Vanilla JS with Chart.js

## Structure

```
dashboard-api/     # Unified worker serving frontend + API
  src/entry.py     # Request handler
  src/static_assets.py  # Inlined HTML/CSS/JS
frontend/          # Source files for frontend (tests here)
trading-engine/    # Cron worker for executing trades
```

## Development

```bash
cd dashboard-api
npm install
npm run dev        # Local dev server
npm run deploy     # Deploy to Cloudflare
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/algorithms` | List all algorithms |
| `POST /api/algorithms` | Create algorithm |
| `GET /api/algorithms/:id/performance` | Get metrics |
| `GET /api/comparison` | Compare all algorithms |
