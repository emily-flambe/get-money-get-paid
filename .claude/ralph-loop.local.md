---
active: true
iteration: 1
max_iterations: 25
completion_promise: "SIGNAL"
started_at: "2026-01-17T05:56:21Z"
---

Merge frontend static files into dashboard-api worker to create a single unified worker. Source of truth is the deployed worker responding correctly.

Steps each iteration:
1. Run local tests: cd dashboard-api && python3 -m pytest tests/ -v
2. Run frontend tests: cd frontend && npm test
3. Test worker locally if possible: cd dashboard-api && npx wrangler dev --local (manual verification)
4. Push changes: git add -A && git commit -m 'feat: iteration N - merge frontend into worker' && git push
5. Check CI: gh run list --limit 1 --json status,conclusion
6. If CI passes, deploy: cd dashboard-api && npx wrangler deploy
7. Verify deployment: curl -s https://dashboard-api.emily-cogsdill.workers.dev/ | head -20
8. Verify API still works: curl -s https://dashboard-api.emily-cogsdill.workers.dev/api/algorithms | head -5
9. If both return expected content (HTML for /, JSON for /api/*), output SIGNAL
10. If errors, read output and fix

Implementation tasks:
1. Move frontend static assets into dashboard-api:
  - Copy frontend/index.html, frontend/css/, frontend/js/ into dashboard-api/static/
  - Do NOT copy node_modules, tests, package.json (keep those in frontend/ for testing)
2. Update dashboard-api/src/entry.py to serve static files:
  - For path / or /index.html: return index.html with Content-Type: text/html
  - For path /css/*: return CSS files with Content-Type: text/css
  - For path /js/*: return JS files with Content-Type: application/javascript
  - For path /api/*: existing API handlers (keep current logic)
  - For path /health: existing health check
3. Embed static files in the worker:
  - Option A: Use Cloudflare Workers Sites (wrangler.toml site config)
  - Option B: Inline assets as Python strings/bytes (simpler for small files)
  - Prefer Option A if it works with Python workers, else Option B
4. Update frontend/js/api.js:
  - Change API_BASE from absolute URL to relative: const API_BASE = '/api'
  - This allows same-origin requests
5. Update wrangler.toml if needed for static assets
6. Keep frontend/ directory for vitest tests (don't delete package.json/vitest)

Context:
- dashboard-api is a Python Worker using Pyodide
- Static files: index.html (~140 lines), styles.css (~6KB), 4 JS files
- Python Workers may not support Workers Sites - check docs, may need to inline assets
- D1 database binding must remain working
- CORS headers can be simplified since frontend/API are same origin

Key files:
- dashboard-api/src/entry.py (add static file serving)
- dashboard-api/wrangler.toml (may need site config)
- frontend/js/api.js (change to relative URL)
- New: dashboard-api/static/* (copied assets)

CRITICAL: Worker must serve both HTML at / AND JSON at /api/algorithms. Both must work after deployment. Verify with curl.

Output SIGNAL when:
- curl https://dashboard-api.emily-cogsdill.workers.dev/ returns HTML containing 'Paper Trading Dashboard'
- curl https://dashboard-api.emily-cogsdill.workers.dev/api/algorithms returns JSON with 'algorithms' key
- CI tests pass

If stuck after 3 attempts on Python Workers Sites config, fall back to inlining static assets as strings in Python code.
