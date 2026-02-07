# Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: Frontend Shows "Disconnected" - Cannot Connect to Backend

**Symptoms:**
- Frontend UI shows red "Disconnected" indicator
- Chat interface says "Waiting for connection..."
- Browser console shows WebSocket connection errors

**Root Cause:** The AG-UI adapter server is not running or not accessible.

**Solution:**

1. **Check AG-UI Adapter is Running**
   ```bash
   # In a new terminal
   cd ag-ui-adapter
   python server.py
   ```

   You should see:
   ```
   ======================================================================
   🔌 AG-UI ADAPTER SERVER
   ======================================================================
   ...
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

2. **Verify Adapter Health**
   ```bash
   curl http://localhost:8000/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "service": "ag-ui-adapter",
     "agentfield": {
       "status": "connected",
       "url": "http://localhost:8080/api/v1",
       "agents": 5
     },
     "websocket_connections": 0
   }
   ```

   If `agentfield.status` is "disconnected":
   - AgentField server is not running → Start it with `agentfield server start`
   - If `agentfield.agents` is 0 → Agents are not running → Start with `python launch_all_agents.py`

3. **Check Browser Console**
   - Open browser DevTools (F12)
   - Go to Console tab
   - Look for WebSocket errors:
     ```
     WebSocket connection to 'ws://localhost:8000/ws/session-xxx' failed
     ```

   Common causes:
   - Adapter not running (see step 1)
   - Port 8000 blocked by firewall
   - Another service using port 8000

### Issue 2: Noisy Heartbeat Logs

**Symptoms:**
```
💓 Enhanced heartbeat sent - Status: ready
::1 - [Sun, 08 Feb 2026 03:29:38] "POST /api/v1/nodes/policy-checker/heartbeat HTTP/1.1 200
```

**Solution:**

The updated `launch_all_agents.py` now suppresses these logs automatically. If you still see them:

1. **Restart the agents**
   - Press Ctrl+C to stop current agents
   - Run: `python launch_all_agents.py`

2. **Set environment variable**
   ```bash
   export AGENTFIELD_LOG_LEVEL=WARNING
   python launch_all_agents.py
   ```

### Issue 3: Agents Not Showing in AgentField UI

**Symptoms:**
- AgentField UI (http://localhost:8080) shows 0 agents
- Adapter health check shows `"agents": 0`

**Solution:**

1. **Verify agents are running**
   ```bash
   # Should see output like:
   # 🚀 Starting medical-reasoner...
   # 🚀 Starting fraud-detector...
   # etc.
   ```

2. **Check agent logs for errors**
   - Look for error messages in the terminal running `launch_all_agents.py`
   - Common errors:
     - `ModuleNotFoundError` → Install missing dependencies
     - `Connection refused` → AgentField server not running
     - `API key not found` → Set ANTHROPIC_API_KEY in .env

3. **Wait 5 seconds after starting**
   - Agents take a few seconds to register with AgentField
   - Refresh the AgentField UI page

### Issue 4: Workflow Stuck on "In Progress"

**Symptoms:**
- Stage indicator shows blue spinner forever
- No error messages
- Workflow never completes

**Solution:**

1. **Check agent logs**
   - Look at the terminal running `launch_all_agents.py`
   - Look for errors from specific agents

2. **Check AgentField server logs**
   - Look at the terminal running `agentfield server start`
   - Look for API errors or timeouts

3. **Verify API key is set**
   ```bash
   # Check .env file
   cat .env | grep ANTHROPIC_API_KEY
   ```

4. **Test API key**
   ```bash
   curl https://api.anthropic.com/v1/messages \
     -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2023-06-01" \
     -H "content-type: application/json" \
     -d '{
       "model": "claude-sonnet-4-20250514",
       "max_tokens": 10,
       "messages": [{"role": "user", "content": "test"}]
     }'
   ```

### Issue 5: "Agent not found" Error

**Symptoms:**
```
Error: Agent workflow-orchestrator not found
```

**Solution:**

1. **Check agent name in API call**
   - Should be `workflow-orchestrator` (with hyphen)
   - NOT `claims-orchestrator`

2. **Verify orchestrator is running**
   ```bash
   curl http://localhost:8080/api/v1/nodes
   ```

   Should include:
   ```json
   {
     "node_id": "workflow-orchestrator",
     "status": "ready"
   }
   ```

### Issue 6: CORS Errors in Browser

**Symptoms:**
```
Access to XMLHttpRequest at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solution:**

The AG-UI adapter is configured to allow CORS from `http://localhost:3000`. If you're using a different frontend URL:

1. **Update CORS settings in ag-ui-adapter/server.py:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000", "http://your-url:port"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Restart the adapter server**

## Diagnostic Checklist

Run through this checklist to diagnose issues:

### 1. AgentField Server
```bash
# Check if running
curl http://localhost:8080/health

# Expected: 200 OK response

# View UI
open http://localhost:8080
```

### 2. Agents
```bash
# Check if registered
curl http://localhost:8080/api/v1/nodes | jq

# Expected: Array of 5 agents
# - medical-reasoner
# - fraud-detector
# - policy-checker
# - cost-analyzer
# - workflow-orchestrator
```

### 3. AG-UI Adapter
```bash
# Check if running
curl http://localhost:8000/health | jq

# Expected:
# {
#   "status": "healthy",
#   "agentfield": { "status": "connected", "agents": 5 }
# }
```

### 4. Frontend
```bash
# Check if running
curl http://localhost:3000

# Expected: HTML response

# Check WebSocket in browser console
# Should see: "🔌 Connecting to AG-UI adapter..."
```

### 5. Test Full Workflow
```bash
# Test via REST API (bypassing UI)
curl -X POST http://localhost:8000/adjudicate \
  -H "Content-Type: application/json" \
  -d '{"claim_id": "CLM10001"}' | jq

# Should return complete adjudication result
```

## Complete System Restart

If all else fails, restart everything:

```bash
# 1. Stop everything (Ctrl+C in all terminals)

# 2. Kill any hanging processes
pkill -f agentfield
pkill -f launch_all_agents
pkill -f "ag-ui-adapter"
pkill -f "next dev"

# 3. Start fresh
# Terminal 1:
agentfield server start

# Wait 3 seconds, then Terminal 2:
python launch_all_agents.py

# Wait 5 seconds, then Terminal 3:
cd ag-ui-adapter && python server.py

# Wait 2 seconds, then Terminal 4:
cd frontend && npm run dev

# 4. Open http://localhost:3000
```

## Getting Help

If you're still stuck:

1. **Check the logs**
   - AgentField server logs
   - Agent logs (from launch_all_agents.py)
   - Adapter logs (from server.py)
   - Browser console logs

2. **Test each component independently**
   - Can you access AgentField UI?
   - Can you curl the adapter /health endpoint?
   - Can you curl individual agent endpoints?

3. **Verify versions**
   ```bash
   python --version  # Should be 3.10+
   node --version    # Should be 18+
   agentfield --version
   ```

4. **Check dependencies**
   ```bash
   pip list | grep -E "agentfield|fastapi|httpx|pydantic"
   ```

5. **Environment variables**
   ```bash
   # Should be set
   echo $ANTHROPIC_API_KEY
   ```

## Quick Reference

### Port Assignments
- **8080** - AgentField server
- **8000** - AG-UI adapter (WebSocket + REST)
- **3000** - Next.js frontend

### Key URLs
- AgentField UI: http://localhost:8080
- Adapter Health: http://localhost:8000/health
- Frontend UI: http://localhost:3000
- WebSocket: ws://localhost:8000/ws/{session_id}

### Service Dependencies
```
Frontend (3000)
    ↓ WebSocket
AG-UI Adapter (8000)
    ↓ HTTP REST
AgentField Server (8080)
    ↓ Manages
5 Agent Instances
```

Each layer depends on the layer below it. Start from bottom (AgentField) and work up.
