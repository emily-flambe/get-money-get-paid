---
active: true
iteration: 1
max_iterations: 25
completion_promise: "SIGNAL"
started_at: "2026-01-17T05:38:37Z"
---

Set up full-stack test suite for paper trading platform
   with GitHub Actions CI. Source of truth is GitHub Actions.                      
                                                                                   
  Steps each iteration:                                                            
  1. Run pytest trading-engine/ dashboard-api/ -v for Python tests                 
  2. Run cd frontend && npm test for JS tests (after package.json exists)          
  3. Push changes: git add -A && git commit -m 'test: iteration N' && git push     
  4. Check CI status: gh run list --limit 1 --json status,conclusion,name | head   
  -20                                                                              
  5. If CI shows conclusion='success', output SIGNAL                               
  6. If tests fail locally, read error output and fix                              
  7. If CI fails, run gh run view --log-failed to get CI error details             
  8. Fix based on CI output (takes precedence over local)                          
                                                                                   
  Setup tasks (first iteration):                                                   
  - Create trading-engine/tests/ with pytest config and conftest.py                
  - Create dashboard-api/tests/ with pytest config and conftest.py                 
  - Add pytest to both pyproject.toml files                                        
  - Create frontend/package.json with vitest for JS testing                        
  - Create frontend/tests/ directory with test files                               
  - Create .github/workflows/test.yml for CI                                       
  - Mock Cloudflare APIs: D1 database, fetch, Headers, Response, Request           
                                                                                   
  Test targets:                                                                    
  - trading-engine: calculate_rsi, run_sma_crossover logic, run_rsi_strategy logic,
   run_momentum_strategy logic                                                     
  - dashboard-api: Performance calculation (Sharpe ratio, max drawdown), CRUD route
   handlers                                                                        
  - frontend: api.js fetch functions, charts.js helper functions                   
                                                                                   
  Context:                                                                         
  - Python Workers use Pyodide - test pure logic, mock js imports and env object   
  - D1 queries use env.DB.prepare().bind().all/first/run() pattern                 
  - Frontend is vanilla JS, no React - use vitest with jsdom                       
  - Alpaca API calls should be mocked, not hit real endpoints                      
  - CI environment: ubuntu-latest, Python 3.12, Node 20                            
                                                                                   
  Key files:                                                                       
  - trading-engine/src/entry.py (strategies, RSI calculation)                      
  - dashboard-api/src/entry.py (API routes, performance metrics)                   
  - frontend/js/api.js, frontend/js/charts.js                                      
  - .github/workflows/test.yml                                                     
                                                                                   
  CRITICAL: GitHub Actions 'test' workflow must show green check. Local passing is 
  not sufficient. CI is the source of truth.                                       
                                                                                   
  Output SIGNAL when:                                                              
  - gh run list --limit 1 shows conclusion='success' for the test workflow         
  - At least 5 Python tests and 3 JS tests exist and pass                          
                                                                                   
  If stuck after 5 attempts on same error, try alternative approach or simplify    
  test scope.
