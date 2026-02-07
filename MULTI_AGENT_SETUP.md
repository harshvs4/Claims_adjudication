# Multi-Agent Architecture Setup Guide

This system now uses **5 independent agents** that work together to adjudicate claims.

## Architecture Overview

```
User Request
     ↓
┌─────────────────────────┐
│  Claims Orchestrator    │ ← Main entry point
│  (claims-orchestrator)  │
└───────────┬─────────────┘
            │
    ┌───────┼───────┬───────┬───────┐
    ↓       ↓       ↓       ↓       ↓
┌────────┐ ┌────┐ ┌──────┐ ┌──────┐
│Medical │ │Fraud│ │Policy│ │ Cost │
│Reasoner│ │Det. │ │Check │ │Analyz│
└────────┘ └────┘ └──────┘ └──────┘
```

## The 5 Agents

| Agent ID | Purpose | Endpoint |
|----------|---------|----------|
| `medical-reasoner` | Evaluates medical necessity | `evaluate_medical_necessity` |
| `fraud-detector` | Detects fraud with vector search | `detect_fraud_patterns` |
| `policy-checker` | Verifies policy coverage | `verify_policy_coverage` |
| `cost-analyzer` | Assesses cost reasonableness | `evaluate_cost_reasonableness` |
| `claims-orchestrator` | Coordinates all agents | `adjudicate_claim` ⭐ |

## Quick Start

### Option 1: Launch All Agents (Recommended)

```bash
# Terminal 1: Start AgentField control plane
af server

# Terminal 2: Launch all agents
./launch_agents.sh all
```

This will:
- ✅ Start all 5 agents in the background
- ✅ Create log files in `logs/` directory
- ✅ Save PID files for easy management
- ✅ Show you the test command

**You should see 5 agents in the AgentField UI!** 🎉

---

### Option 2: Launch Agents Manually

If you want more control, launch each agent in a separate terminal:

```bash
# Terminal 1: AgentField server
af server

# Terminal 2: Medical Reasoner
python agents/medical_agent.py

# Terminal 3: Fraud Detector
python agents/fraud_agent.py

# Terminal 4: Policy Checker
python agents/policy_agent.py

# Terminal 5: Cost Analyzer
python agents/cost_agent.py

# Terminal 6: Orchestrator (MUST start last)
python agents/orchestrator_agent.py
```

---

## Testing the System

### Test the Full Workflow

Call the orchestrator, which will call all specialist agents:

```bash
curl -X POST http://localhost:8080/api/v1/execute/claims-orchestrator.adjudicate_claim \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}' | jq
```

**What happens:**
1. Orchestrator receives request
2. Calls `medical-reasoner` → medical assessment
3. Calls `fraud-detector` → fraud analysis (reads medical from memory)
4. Calls `policy-checker` → coverage check
5. Calls `cost-analyzer` → cost evaluation (reads medical + fraud)
6. Synthesizes final decision
7. Returns complete `AdjudicationResult`

---

### Test Individual Agents

You can also call specialist agents directly:

```bash
# Medical reasoner only
curl -X POST http://localhost:8080/api/v1/execute/medical-reasoner.evaluate_medical_necessity \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Fraud detector only
curl -X POST http://localhost:8080/api/v1/execute/fraud-detector.detect_fraud_patterns \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Policy checker only
curl -X POST http://localhost:8080/api/v1/execute/policy-checker.verify_policy_coverage \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Cost analyzer only
curl -X POST http://localhost:8080/api/v1/execute/cost-analyzer.evaluate_cost_reasonableness \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'
```

---

## Managing Agents

### Check Agent Status

```bash
./launch_agents.sh status
```

Output:
```
📊 Agent Status:
-----------------------------------
✅ medical-reasoner: RUNNING (PID: 12345)
✅ fraud-detector: RUNNING (PID: 12346)
✅ policy-checker: RUNNING (PID: 12347)
✅ cost-analyzer: RUNNING (PID: 12348)
✅ orchestrator: RUNNING (PID: 12349)
```

### Stop All Agents

```bash
./launch_agents.sh stop
```

### View Agent Logs

```bash
# View all logs
tail -f logs/*.log

# View specific agent
tail -f logs/medical-reasoner.log
tail -f logs/fraud-detector.log
tail -f logs/orchestrator.log
```

### Restart Agents

```bash
# Stop all
./launch_agents.sh stop

# Start all
./launch_agents.sh all
```

---

## AgentField UI

Open http://localhost:8080 in your browser to see:

✅ **5 separate agents** listed:
- claims-orchestrator
- medical-reasoner
- fraud-detector
- policy-checker
- cost-analyzer

✅ **Execution history** for each agent

✅ **Agent details** and endpoints

---

## How Multi-Agent Communication Works

### 1. HTTP Communication

Agents call each other via AgentField's HTTP API:

```python
# Orchestrator calling medical agent
url = "http://localhost:8080/api/v1/execute/medical-reasoner.evaluate_medical_necessity"
response = await client.post(url, json={"input": {"claim_id": "CLM10001"}})
result = response.json()["result"]
```

### 2. Shared Memory Coordination

Agents share data through AgentField's memory system:

```python
# Medical agent stores assessment
await medical_agent.memory.set(
    key="claim:CLM10001:medical_assessment",
    data=medical_result
)

# Fraud agent reads it later
medical_data = await fraud_agent.memory.get("claim:CLM10001:medical_assessment")
```

**Key insight:** Memory is shared across all agents on the same AgentField server!

### 3. Sequential Processing

The orchestrator calls agents in order:
1. **Medical** (needs claim data only)
2. **Fraud** (reads medical from memory)
3. **Policy** (independent check)
4. **Cost** (reads medical + fraud from memory)

This ensures downstream agents have context from upstream agents.

---

## Data Flow Example

```
User → Orchestrator
        ↓
        Medical Agent
        ↓ (stores in memory)
        ↓
        Fraud Agent
        ↓ (reads medical, stores fraud)
        ↓
        Policy Agent
        ↓ (stores policy)
        ↓
        Cost Agent
        ↓ (reads medical + fraud, stores cost)
        ↓
        Orchestrator
        ↓ (synthesizes final decision)
        ↓
User ← Final Result
```

---

## Troubleshooting

### "Agent not found" error

**Problem:** One or more agents not running

**Solution:**
```bash
./launch_agents.sh status  # Check which agents are missing
./launch_agents.sh all     # Restart all agents
```

---

### "Connection refused" on port 8080

**Problem:** AgentField server not running

**Solution:**
```bash
# Terminal 1
af server
```

---

### Agent crashed/stopped

**Check the logs:**
```bash
cat logs/medical-reasoner.log
cat logs/fraud-detector.log
# etc.
```

**Restart specific agent:**
```bash
python agents/medical_agent.py
```

---

### Orchestrator can't reach specialist agents

**Ensure specialists started before orchestrator:**
```bash
# Stop all
./launch_agents.sh stop

# Start in order (specialists first, orchestrator last)
./launch_agents.sh all
```

---

### Memory not shared between agents

**Check agents are connected to same AgentField server:**
```bash
# All agents should use same AGENTFIELD_SERVER in config.py
# Default: http://localhost:8080
```

---

## Performance Notes

### Parallel vs Sequential

**Current implementation:** Sequential (one agent at a time)
- Medical → Fraud → Policy → Cost
- Total time: ~12-15 seconds

**Potential optimization:** Parallel execution
- Medical + Policy run in parallel
- Then Fraud + Cost run in parallel (need medical context)
- Total time: ~6-8 seconds

To implement parallel execution, modify `orchestrator_agent.py`:

```python
import asyncio

# Run medical and policy in parallel
medical_task = call_specialist_agent("medical-reasoner", "evaluate_medical_necessity", claim_id)
policy_task = call_specialist_agent("policy-checker", "verify_policy_coverage", claim_id)
medical, policy = await asyncio.gather(medical_task, policy_task)

# Then run fraud and cost in parallel (they both need medical)
fraud_task = call_specialist_agent("fraud-detector", "detect_fraud_patterns", claim_id)
cost_task = call_specialist_agent("cost-analyzer", "evaluate_cost_reasonableness", claim_id)
fraud, cost = await asyncio.gather(fraud_task, cost_task)
```

---

## Advantages of Multi-Agent Architecture

✅ **Visual Separation** - Each agent visible in AgentField UI

✅ **Independent Scaling** - Scale specific agents based on load

✅ **Fault Isolation** - One agent failure doesn't crash others

✅ **Clear Responsibilities** - Each agent has single purpose

✅ **Easy Testing** - Test each agent independently

✅ **Flexible Deployment** - Can deploy agents on different machines

✅ **Better Monitoring** - Track performance per agent

---

## Migration from Single-Agent

If you had the old `main.py` single-agent architecture:

**Old:**
- 1 agent with multiple `@app.reasoner` endpoints
- All functions in one process

**New:**
- 5 independent agents
- Each agent in separate process
- Orchestrator coordinates via HTTP

**Migration steps:**
1. ✅ Keep old `main.py` for reference
2. ✅ Use new `agents/` directory structure
3. ✅ Launch with `./launch_agents.sh all`
4. ✅ Update API calls to use `claims-orchestrator.adjudicate_claim`

---

## Next Steps

1. ✅ Launch all agents: `./launch_agents.sh all`
2. ✅ Check AgentField UI: http://localhost:8080
3. ✅ Test the system: `curl -X POST ...`
4. ✅ View logs: `tail -f logs/*.log`
5. ✅ Add your own claims data to `data/synthetic_claims.json`

**Congratulations! You now have a true multi-agent system! 🎉**
