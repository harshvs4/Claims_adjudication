# AG-UI Integration Setup Guide

Complete guide for running the Claims Adjudication system with the AG-UI real-time web interface.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                              │
│                    http://localhost:3000                          │
│                                                                    │
│   ┌────────────────────────────────────────────────────────┐    │
│   │          Next.js React Application                      │    │
│   │  • Real-time workflow visualization                     │    │
│   │  • Assessment result displays                           │    │
│   │  • Final decision card                                  │    │
│   └───────────────────┬────────────────────────────────────┘    │
└───────────────────────┼─────────────────────────────────────────┘
                        │
                        │ WebSocket (AG-UI Protocol)
                        │ ws://localhost:8000/ws/{session_id}
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                   AG-UI ADAPTER SERVER                           │
│                    localhost:8000                                │
│                                                                   │
│   ┌────────────────────────────────────────────────────────┐   │
│   │       FastAPI WebSocket Server                          │   │
│   │  • Converts AgentField REST → AG-UI events             │   │
│   │  • Streams workflow progress                            │   │
│   │  • Manages WebSocket connections                        │   │
│   └───────────────────┬────────────────────────────────────┘   │
└───────────────────────┼─────────────────────────────────────────┘
                        │
                        │ HTTP REST API
                        │ http://localhost:8080/api/v1
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                   AGENTFIELD SERVER                              │
│                    localhost:8080                                │
│                                                                   │
│   ┌────────────────────────────────────────────────────────┐   │
│   │          Multi-Agent Orchestration                      │   │
│   │                                                          │   │
│   │  ┌──────────────────────────────────────────────────┐  │   │
│   │  │  workflow-orchestrator (Main Coordinator)        │  │   │
│   │  │  • Calls specialist agents via app.call()        │  │   │
│   │  │  • Synthesizes final decision                    │  │   │
│   │  └──────────────┬───────────────────────────────────┘  │   │
│   │                 │                                        │   │
│   │     ┌───────────┼──────────┬──────────┬──────────┐     │   │
│   │     │           │          │          │          │     │   │
│   │  ┌──▼───┐  ┌───▼──┐  ┌───▼───┐  ┌──▼─────┐  ┌──▼──┐  │   │
│   │  │Medical│  │Fraud │  │Policy │  │  Cost  │  │Final│  │   │
│   │  │ Agent │  │Agent │  │ Agent │  │ Agent  │  │ AI  │  │   │
│   │  └───────┘  └──────┘  └───────┘  └────────┘  └─────┘  │   │
│   │                                                          │   │
│   └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## System Components

### 1. AgentField Server (Port 8080)
- Multi-agent orchestration platform
- Manages agent lifecycle and communication
- Provides REST API for agent execution
- Web UI for monitoring agents

### 2. Multi-Agent System
Five specialized agents running as separate instances:
- **workflow-orchestrator** - Main coordinator
- **medical-reasoner** - Medical necessity evaluation
- **fraud-detector** - Fraud pattern detection with vector search
- **policy-checker** - Policy coverage verification
- **cost-analyzer** - Cost reasonableness analysis

### 3. AG-UI Adapter Server (Port 8000)
- Converts AgentField REST API to AG-UI WebSocket protocol
- Streams real-time progress events
- Manages WebSocket connections per session

### 4. Next.js Frontend (Port 3000)
- Real-time UI for claims adjudication
- WebSocket client for live updates
- Beautiful visualization of workflow progress
- Detailed assessment displays

## Complete Setup Instructions

### Step 1: Start AgentField Server

```bash
# In terminal 1
agentfield server start
```

**Verify:** Open http://localhost:8080 - you should see the AgentField UI

### Step 2: Start All Agent Instances

```bash
# In terminal 2 - from project root
python launch_all_agents.py
```

**Expected Output:**
```
======================================================================
🏥 CLAIMS ADJUDICATION - MULTI-AGENT LAUNCHER
======================================================================

Starting all agents:
  1. medical-reasoner
  2. fraud-detector
  3. policy-checker
  4. cost-analyzer
  5. workflow-orchestrator

======================================================================
Press Ctrl+C to stop all agents
======================================================================

🚀 Starting medical-reasoner...
🚀 Starting fraud-detector...
🚀 Starting policy-checker...
🚀 Starting cost-analyzer...

⏳ Waiting for specialist agents to initialize...

🚀 Starting workflow-orchestrator...

======================================================================
✅ ALL AGENTS RUNNING!
======================================================================

📊 AgentField UI: http://localhost:8080
```

**Verify:**
- Go to http://localhost:8080
- You should see 5 agents listed:
  - medical-reasoner
  - fraud-detector
  - policy-checker
  - cost-analyzer
  - workflow-orchestrator

### Step 3: Start AG-UI Adapter Server

```bash
# In terminal 3
cd ag-ui-adapter
python server.py
```

**Expected Output:**
```
======================================================================
🔌 AG-UI ADAPTER SERVER
======================================================================

Starting AG-UI adapter for Claims Adjudication...

Endpoints:
  WebSocket: ws://localhost:8000/ws/{session_id}
  REST API:  http://localhost:8000/adjudicate
  Health:    http://localhost:8000/health

CORS enabled for: http://localhost:3000
======================================================================

INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"ag-ui-adapter"}
```

### Step 4: Start the Frontend UI

```bash
# In terminal 4
cd frontend
npm install  # First time only
npm run dev
```

**Expected Output:**
```
   ▲ Next.js 14.0.4
   - Local:        http://localhost:3000

 ✓ Ready in 2.3s
```

**Verify:** Open http://localhost:3000 - you should see the Claims Adjudication UI

## Using the System

### 1. Open the Web UI

Navigate to http://localhost:3000

### 2. Check Connection Status

Top-right corner should show:
- 🟢 **Connected** (green) - Ready to use
- 🔴 **Disconnected** (red) - Check AG-UI adapter

### 3. Start an Adjudication

1. Enter a Claim ID (e.g., `CLM10001`)
2. Click **"Start Adjudication"**
3. Watch the real-time progress:

```
┌─────────────────────────────────────────────────┐
│  WORKFLOW PROGRESS                               │
├─────────────────────────────────────────────────┤
│  [✓] Medical         - Completed                 │
│  [⟳] Fraud Detection - In Progress...            │
│  [○] Policy Check    - Pending                   │
│  [○] Cost Analysis   - Pending                   │
│  [○] Final Decision  - Pending                   │
└─────────────────────────────────────────────────┘
```

### 4. View Results

As each agent completes, you'll see:

- **Medical Assessment Card**
  - Medically necessary: Yes/No
  - Treatment appropriate
  - Documentation adequate
  - Confidence score
  - Reasoning

- **Fraud Assessment Card**
  - Risk score (0.0 - 1.0)
  - Red flags detected
  - Similar fraud cases found
  - Pattern analysis
  - Recommendation

- **Policy Assessment Card**
  - Coverage status
  - Exclusions
  - Prior authorization
  - Reasoning

- **Cost Assessment Card**
  - Cost reasonableness
  - Expected range
  - Variance percentage
  - Reasoning

### 5. Final Decision

When all assessments complete, you'll see the **Final Decision Card**:

```
┌────────────────────────────────────────────────┐
│  ✅ APPROVED                   Confidence: 87% │
├────────────────────────────────────────────────┤
│  Approved Amount: $12,500                      │
│                                                 │
│  Key Decision Factors:                         │
│  1. Treatment medically necessary              │
│  2. Low fraud risk (0.15)                      │
│  3. Covered under policy                       │
│  4. Cost within expected range                 │
│  5. Strong supporting documentation            │
│                                                 │
│  Detailed Reasoning:                           │
│  Based on comprehensive evaluation from all    │
│  specialist agents, this claim is approved...  │
└────────────────────────────────────────────────┘
```

## Test Claims

Try these pre-configured claim IDs:

| Claim ID   | Expected Result      | Why                                    |
|------------|---------------------|----------------------------------------|
| CLM10001   | ✅ APPROVE          | Routine appendectomy, all checks pass  |
| CLM10002   | ⚠️ APPROVE_WITH_REVIEW | Expensive but necessary treatment   |
| CLM10003   | 🔍 INVESTIGATE      | Fraud risk flags detected              |
| CLM10004   | ✅ APPROVE          | Standard covered procedure             |
| CLM10005   | ❌ DENY             | Policy exclusion applies               |

## AG-UI Protocol Events

The system uses these event types for real-time communication:

### From Frontend → Adapter

```json
{
  "type": "start_adjudication",
  "claim_id": "CLM10001"
}
```

### From Adapter → Frontend

**Session Started**
```json
{
  "type": "session_started",
  "session_id": "session-123",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "claim_id": "CLM10001",
    "message": "Starting claims adjudication workflow"
  }
}
```

**Workflow Started**
```json
{
  "type": "workflow_started",
  "data": {
    "claim_id": "CLM10001",
    "workflow": "claims_adjudication",
    "stages": ["medical", "fraud", "policy", "cost", "decision"]
  }
}
```

**Stage Started**
```json
{
  "type": "stage_started",
  "data": {
    "stage": "medical",
    "agent": "medical-reasoner",
    "message": "Evaluating medical necessity..."
  }
}
```

**Stage Completed**
```json
{
  "type": "stage_completed",
  "data": {
    "stage": "medical",
    "assessment": {
      "is_medically_necessary": true,
      "confidence": 0.92,
      "reasoning": "..."
    }
  }
}
```

**Workflow Completed**
```json
{
  "type": "workflow_completed",
  "data": {
    "claim_id": "CLM10001",
    "decision": "APPROVE",
    "approved_amount": 12500,
    "confidence": 0.87,
    "reasoning": "...",
    "key_factors": ["...", "..."],
    "full_result": { /* Complete adjudication result */ }
  }
}
```

## Troubleshooting

### Issue: WebSocket Connection Failed

**Symptoms:** Red "Disconnected" indicator in UI

**Solutions:**
1. Check AG-UI adapter is running on port 8000
2. Verify no firewall blocking WebSocket connections
3. Check browser console for errors

### Issue: No Agents Showing in AgentField UI

**Symptoms:** AgentField UI shows 0 agents

**Solutions:**
1. Ensure `launch_all_agents.py` is running
2. Check agent logs for errors
3. Verify AgentField server started successfully

### Issue: Workflow Stuck on "In Progress"

**Symptoms:** Stage indicators stay blue (in progress) forever

**Solutions:**
1. Check agent logs in terminal 2
2. Verify the specific agent is running (e.g., medical-reasoner)
3. Check AgentField server logs
4. Try restarting agents

### Issue: "Agent not found" Error

**Symptoms:** Error message in adapter logs

**Solutions:**
1. Ensure all agents have registered with AgentField
2. Wait 5 seconds after starting agents before testing
3. Check agent names match exactly (e.g., "workflow-orchestrator")

## Terminal Summary

You need **4 terminals** running:

| Terminal | Command | Port | Status Check |
|----------|---------|------|--------------|
| 1 | `agentfield server start` | 8080 | http://localhost:8080 |
| 2 | `python launch_all_agents.py` | - | Should see 5 agents in AgentField UI |
| 3 | `cd ag-ui-adapter && python server.py` | 8000 | `curl localhost:8000/health` |
| 4 | `cd frontend && npm run dev` | 3000 | http://localhost:3000 |

## Next Steps

- **Customize UI:** Edit `frontend/src/components/*` for custom styling
- **Add More Claims:** Add test data in `data/claims.csv`
- **Enhance Agents:** Modify agent logic in `agents/*_agent.py`
- **Deploy:** Build frontend with `npm run build` and deploy

## Resources

- **AgentField Docs:** https://docs.agentfield.ai
- **AG-UI Docs:** https://docs.ag-ui.com
- **Next.js Docs:** https://nextjs.org/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
