# 🚀 Quick Start - Multi-Agent Setup

## TL;DR - Get Running in 2 Minutes

```bash
# 1. Start AgentField server (Terminal 1)
af server

# 2. Launch all agents (Terminal 2)
cd /Users/shekharsomani/Desktop/projects/Claims_adjudication
./launch_agents.sh all

# 3. Test it (Terminal 3)
curl -X POST http://localhost:8080/api/v1/execute/claims-orchestrator.adjudicate_claim \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'
```

## What You'll See

### In AgentField UI (http://localhost:8080)

**5 Independent Agents:**
1. 🎯 **claims-orchestrator** - Main coordinator
2. 🏥 **medical-reasoner** - Medical necessity
3. 🔍 **fraud-detector** - Fraud detection
4. 📄 **policy-checker** - Policy coverage
5. 💰 **cost-analyzer** - Cost analysis

### In Terminal Output

```
═══════════════════════════════════════════════════════════
   CLAIMS ADJUDICATION MULTI-AGENT SYSTEM
═══════════════════════════════════════════════════════════

✅ AgentField server is running

🚀 Launching medical-reasoner...
✅ medical-reasoner started (PID: 12345)
   Log: logs/medical-reasoner.log

🚀 Launching fraud-detector...
✅ fraud-detector started (PID: 12346)
   Log: logs/fraud-detector.log

🚀 Launching policy-checker...
✅ policy-checker started (PID: 12347)
   Log: logs/policy-checker.log

🚀 Launching cost-analyzer...
✅ cost-analyzer started (PID: 12348)
   Log: logs/cost-analyzer.log

🚀 Launching orchestrator...
✅ orchestrator started (PID: 12349)
   Log: logs/orchestrator.log

═══════════════════════════════════════════════════════════
✅ All agents launched successfully!
═══════════════════════════════════════════════════════════
```

## Key Commands

```bash
# Check agent status
./launch_agents.sh status

# Stop all agents
./launch_agents.sh stop

# View logs
tail -f logs/*.log

# Restart everything
./launch_agents.sh stop && ./launch_agents.sh all
```

## Test Individual Agents

```bash
# Medical reasoner
curl -X POST http://localhost:8080/api/v1/execute/medical-reasoner.evaluate_medical_necessity \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Fraud detector
curl -X POST http://localhost:8080/api/v1/execute/fraud-detector.detect_fraud_patterns \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Policy checker
curl -X POST http://localhost:8080/api/v1/execute/policy-checker.verify_policy_coverage \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Cost analyzer
curl -X POST http://localhost:8080/api/v1/execute/cost-analyzer.evaluate_cost_reasonableness \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'
```

## Project Structure

```
Claims_adjudication/
├── agents/                          # 🆕 Independent agent instances
│   ├── medical_agent.py            # Medical reasoner agent
│   ├── fraud_agent.py              # Fraud detector agent
│   ├── policy_agent.py             # Policy checker agent
│   ├── cost_agent.py               # Cost analyzer agent
│   └── orchestrator_agent.py       # Main orchestrator
├── launch_agents.sh                # 🆕 Convenience launcher
├── logs/                           # 🆕 Agent logs (created on first run)
│   ├── medical-reasoner.log
│   ├── fraud-detector.log
│   ├── policy-checker.log
│   ├── cost-analyzer.log
│   └── orchestrator.log
├── reasoners/                      # Original reasoner functions (kept for reference)
├── skills/                         # Deterministic functions
├── models/                         # Pydantic schemas
├── data/                           # Claims data
├── config.py                       # Configuration
└── main.py                         # Legacy single-agent (deprecated)
```

## Workflow

```
User Request
     ↓
claims-orchestrator.adjudicate_claim
     ↓
     ├─→ medical-reasoner.evaluate_medical_necessity
     │   ↓ (stores medical assessment in memory)
     │
     ├─→ fraud-detector.detect_fraud_patterns
     │   ↓ (reads medical, stores fraud assessment)
     │
     ├─→ policy-checker.verify_policy_coverage
     │   ↓ (stores policy assessment)
     │
     └─→ cost-analyzer.evaluate_cost_reasonableness
         ↓ (reads medical + fraud, stores cost assessment)
         ↓
    orchestrator synthesizes final decision
         ↓
    Complete AdjudicationResult
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Only 1 agent in UI | Make sure you launched with `./launch_agents.sh all`, not `python main.py` |
| "Agent not found" | Check `./launch_agents.sh status` - restart missing agents |
| Connection refused | Start AgentField server: `af server` |
| Agent crashed | Check logs: `cat logs/[agent-name].log` |

## Next Steps

📖 **Detailed guide:** [MULTI_AGENT_SETUP.md](MULTI_AGENT_SETUP.md)

📊 **Architecture diagram:** [architecture_diagram.drawio](architecture_diagram.drawio)

📚 **Architecture deep-dive:** [ARCHITECTURE.md](ARCHITECTURE.md)

🎯 **Ready to test!** Open http://localhost:8080 and see your 5 agents running!
