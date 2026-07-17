# Deployment

## Start server

```bash
cd /home/nicholas/workspace/agents/sat_stat
python3 analysis.py &
```

Server listens on **`http://localhost:15001`** (Cheroot, 10 threads).

First run auto-downloads active satellite TLE from Celestrak and caches to `tle_data.json`.

## Access

Because the server runs inside WSL and Windows has an HTTP proxy at `127.0.0.1:15256`, the browser may fail to load `localhost:15001` (the proxy intercepts the request and can't reach WSL).

**Use the WSL IP instead:**

```
http://192.168.100.159:15001/
```

This is a non-localhost address so the browser bypasses the proxy.

If WSL IP changes, check it with:

```bash
ip addr show eth0 | grep -oP 'inet \K[\d.]+'
```

## Stop

```bash
pkill -f analysis.py
```

## Verification

### Playwright (headless, uses Chromium in WSL)

```bash
python3 test_workflow.py
```

### Edge CDP (uses real Windows Edge via remote debugging)

Requires Edge already running with CDP on port 9222:

```bash
# Launch Edge with CDP (run from Windows)
msedge --guest --remote-debugging-port=9222

# Or from WSL:
powershell.exe -NoProfile -Command "Start-Process 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' -ArgumentList '--guest','--remote-debugging-port=9222'"

# Run test
node test_edge.mjs
```

### Manual

Open `http://192.168.100.159:15001/` in browser. The page should load with:
- Left sidebar listing ~39 constellations (Starlink checked by default)
- "Analyze" button, bin width selector, bin height input
- Histogram chart after clicking Analyze
- TLE epoch displayed next to "Update" button

## Dependencies

- Python 3 with `bottle` and `cheroot`
- Playwright (`npm install playwright` or `pip install playwright`)
- Node.js (for Edge CDP verification test)
