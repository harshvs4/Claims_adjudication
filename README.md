# Claims Adjudication System

A multi-agent health insurance claims adjudication system built on [AgentField](https://agentfield.ai). Five specialized AI agents collaborate through shared memory and vector similarity search to evaluate medical necessity, detect fraud, verify policy compliance, analyze costs, and deliver transparent, auditable decisions.

**NEW:** 🎨 **Real-time Web UI** with AG-UI protocol integration - Watch the multi-agent workflow execute live in your browser!

## Architecture

```
                         adjudicate_claim(claim_id)
                                  |
                      +-----------+-----------+
                      |   Coordinator Agent   |
                      +-----------+-----------+
                                  |
              +-------------------+-------------------+
              |          |             |               |
      +-------+--+ +----+-----+ +----+------+ +------+----+
      | Medical  | |  Fraud   | |  Policy   | |   Cost    |
      | Reasoner | | Detector | |   Agent   | | Analyzer  |
      +----+-----+ +----+-----+ +----+------+ +-----+-----+
           |             |            |              |
           +------+------+------+----+-----+--------+
                  |             |          |
            app.memory     app.ai()   Skills (deterministic)
         (shared state)   (Claude)    (scoring, benchmarks)
```

**How it works:** The coordinator loads a claim and runs each specialist agent sequentially. Each agent stores its findings in shared memory so downstream agents can cross-reference. The fraud detector additionally indexes claims as vector embeddings for similarity search against historical patterns. Finally, the coordinator synthesizes all assessments into a decision: APPROVE, APPROVE_WITH_REVIEW, INVESTIGATE, or DENY.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | [AgentField](https://agentfield.ai) (SDK + control plane) |
| LLM | Claude Sonnet via [LiteLLM](https://github.com/BerriAI/litellm) |
| Embeddings | [FastEmbed](https://github.com/qdrant/fastembed) (BAAI/bge-small-en-v1.5, 384-dim, local) |
| Vector Search | AgentField built-in vector memory |
| Structured Output | [Pydantic](https://docs.pydantic.dev/) schema validation |
| Data Models | ICD-10 diagnosis codes, CPT procedure codes |

## Project Structure

```
claims-adjudication/
├── main.py                            # Agent setup, endpoint registration, entry point
├── config.py                          # Cost benchmarks, fraud thresholds, model config
├── data/
│   └── synthetic_claims.json          # 100+ test claims (CLEAN, FRAUD, EDGE_CASE)
├── models/
│   ├── claim.py                       # Claim, Policyholder, Provider, Procedure
│   └── decision.py                    # MedicalAssessment, FraudAssessment, PolicyAssessment,
│                                      # CostAssessment, FinalDecision, AdjudicationResult
├── reasoners/                         # AI-powered agents (async, use app.ai())
│   ├── medical_reasoner.py            # Medical necessity evaluation
│   ├── fraud_detector.py              # Fraud detection + vector similarity search
│   ├── policy_agent.py                # Policy coverage verification
│   ├── cost_analyzer.py               # Cost reasonableness analysis
│   └── adjudication_coordinator.py    # Orchestration + final decision synthesis
├── skills/                            # Deterministic functions (no AI)
│   ├── data_extraction.py             # Claim loading and summarization
│   ├── fraud_scoring.py               # Rule-based fraud scoring
│   ├── cost_benchmarks.py             # Cost range lookups by diagnosis + severity
│   └── medical_codes.py               # ICD-10/CPT code reference data
└── utils/
    └── helpers.py                     # Formatting utilities
```

## 🎨 Web UI (AG-UI Integration)

This system includes a **beautiful real-time web interface** built with AG-UI protocol for live workflow visualization.

![AG-UI Demo](docs/agui-demo.png)

### Features
- 🔄 **Real-time WebSocket updates** - Watch agents work in real-time
- 📊 **Visual workflow progress** - See each stage as it completes
- 🎯 **Detailed assessment cards** - View all specialist agent results
- ✅ **Final decision display** - Clear adjudication outcome with reasoning
- 📱 **Responsive design** - Works on desktop, tablet, and mobile

### Quick Start with UI

**Option 1: Automated startup (recommended)**

```bash
./start_system.sh all
```

This single command starts all 4 components:
1. AgentField server (port 8080)
2. All 5 agent instances
3. AG-UI adapter server (port 8000)
4. Next.js frontend UI (port 3000)

Then open [http://localhost:3000](http://localhost:3000) in your browser!

**Option 2: Manual startup**

```bash
# Terminal 1: AgentField server
agentfield server start

# Terminal 2: All agents
python launch_all_agents.py

# Terminal 3: AG-UI adapter
cd ag-ui-adapter && python server.py

# Terminal 4: Frontend
cd frontend && npm install && npm run dev
```

📖 **Full setup guide:** See [AG_UI_SETUP.md](AG_UI_SETUP.md) for detailed instructions.

## Quick Start (API Only)

### Prerequisites

- Python 3.10+
- [AgentField CLI](https://agentfield.ai)
- Anthropic API key
- Node.js 18+ (for web UI)

### Setup

```bash
# Install AgentField CLI
curl -sSf https://agentfield.ai/get | sh
source ~/.zshrc

# Clone the repo
git clone https://github.com/harshvs4/Claims_adjudication.git
cd Claims_adjudication

# Create and activate environment
conda create -n agentfield python=3.10 -y
conda activate agentfield

# Install Python dependencies
pip install agentfield fastembed python-dotenv pydantic httpx fastapi uvicorn

# Install frontend dependencies (for UI)
cd frontend && npm install && cd ..

# Configure API key
echo 'ANTHROPIC_API_KEY=your-key-here' > .env
```

### Run (Multi-Agent Mode)

```bash
# Terminal 1: Start AgentField control plane
agentfield server start

# Terminal 2: Start all agents
python launch_all_agents.py
```

Then use the API or web UI to process claims.

## API Endpoints

All endpoints are accessed through the AgentField control plane at `http://localhost:8080`.

### Main Endpoint

**Adjudicate a claim** (runs all 5 agents):

```bash
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.adjudicate_claim \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}' | jq
```

### Individual Agent Endpoints

```bash
# Medical necessity assessment
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.assess_medical_necessity \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Fraud risk analysis
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.analyze_fraud_risk \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Policy compliance check
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.check_policy_coverage \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Cost reasonableness analysis
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.analyze_cost \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'
```

### Deterministic Skills

```bash
# Get claim data (no AI)
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.get_claim_data \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Get fraud indicators (rule-based)
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.get_fraud_indicators \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Get cost benchmark
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.get_cost_benchmark \
  -H "Content-Type: application/json" \
  -d '{"input": {"diagnosis_code": "J18.9", "severity": "moderate"}}'
```

### Batch Processing

```bash
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.process_batch_claims \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_ids": ["CLM10001", "CLM10040", "CLM10048"]}}'
```

## Response Format

```json
{
  "execution_id": "exec_...",
  "status": "succeeded",
  "result": {
    "claim_id": "CLM10001",
    "final_decision": {
      "decision": "APPROVE | DENY | INVESTIGATE | APPROVE_WITH_REVIEW",
      "approved_amount": 7750.15,
      "confidence": 0.95,
      "investigation_required": false,
      "denial_reason": null,
      "reasoning": "Detailed explanation of the decision...",
      "key_factors": ["Factor 1", "Factor 2", "..."]
    },
    "medical_assessment": {
      "is_medically_necessary": true,
      "treatment_appropriate": true,
      "over_treatment_detected": false,
      "confidence": 0.95,
      "reasoning": "..."
    },
    "fraud_assessment": {
      "fraud_risk_score": 0.15,
      "red_flags": [],
      "similar_fraud_cases_found": 0,
      "pattern_analysis": "LOW PATTERN RISK: No similar fraud cases found",
      "recommendation": "APPROVE",
      "reasoning": "..."
    },
    "policy_assessment": {
      "covered_under_policy": true,
      "exclusions_apply": [],
      "coverage_limits_exceeded": false,
      "reasoning": "..."
    },
    "cost_assessment": {
      "cost_reasonable": true,
      "expected_range_min": 5600.0,
      "expected_range_max": 10400.0,
      "variance_percentage": -3.1,
      "reasoning": "..."
    },
    "processing_time_ms": 46299,
    "agents_consulted": ["medical", "fraud", "policy", "cost", "coordinator"]
  },
  "duration_ms": 46330
}
```

## Key Features

### Reasoners vs Skills

The system separates AI-powered reasoning from deterministic logic:

- **Reasoners** (`@app.reasoner`) — Async functions that call `app.ai()` with Pydantic schemas for structured output. Handle subjective decisions requiring judgment (medical necessity, fraud patterns, final adjudication).

- **Skills** (`@app.skill`) — Synchronous functions for predictable computations. Cost benchmarking, fraud score calculation, ICD-10/CPT code lookups. Fast, reliable, no LLM costs.

### Shared Memory for Agent Coordination

Agents pass findings to each other through AgentField's built-in memory, without external infrastructure:

```python
# Medical agent stores its assessment
await app.memory.set(key=f"claim:{claim_id}:medical_assessment", data=result.model_dump())

# Fraud detector reads it to cross-reference
medical_data = await app.memory.get(f"claim:{claim_id}:medical_assessment")
```

### Vector Similarity Search for Fraud Detection

The fraud detector generates embeddings from claim descriptions using FastEmbed (BAAI/bge-small-en-v1.5), indexes them in AgentField's vector memory, and searches for similar historical claims to detect fraud patterns:

```python
from fastembed import TextEmbedding

model = TextEmbedding("BAAI/bge-small-en-v1.5")
embedding = list(model.embed([claim_description]))[0].tolist()

await app.memory.set_vector(key=claim_id, embedding=embedding, metadata={...})
similar = await app.memory.similarity_search(query_embedding=embedding, top_k=5)
```

As more claims are processed, the system builds a growing knowledge base of patterns. Claims similar to previously flagged fraud cases are automatically surfaced.

### Deterministic Fraud Scoring

Rule-based checks run before AI analysis:

- Provider reputation flags
- Cost inflation detection (claimed vs. typical by severity)
- Claim frequency anomalies (>5 prior claims)
- Filing speed analysis (same-day submission)

### Decision Framework

The coordinator follows a structured decision framework:

| Decision | Criteria |
|----------|----------|
| APPROVE | All assessments positive, low fraud risk (<0.3), medically necessary, policy covered, cost reasonable |
| APPROVE_WITH_REVIEW | Borderline case, moderate concerns but not disqualifying |
| INVESTIGATE | Fraud risk 0.5-0.7, unclear medical necessity, significant cost variance |
| DENY | High fraud risk (>0.7), not medically necessary, policy exclusions apply |

## Configuration

Edit `config.py` to customize:

```python
# Cost benchmarks by ICD-10 code
COST_BENCHMARKS = {
    'J18.9': 8000,      # Pneumonia
    'I21.9': 45000,     # Acute MI
    'E11.9': 3000,      # Type 2 Diabetes
    # ...
}

# Severity multipliers
SEVERITY_MULTIPLIERS = {'mild': 0.7, 'moderate': 1.0, 'severe': 1.5}

# Fraud score thresholds
FRAUD_SCORE_THRESHOLDS = {'low': 0.3, 'medium': 0.5, 'high': 0.7}

# AI model (LiteLLM format)
AI_MODEL = "anthropic/claude-sonnet-4-20250514"
```

## Supported Diagnoses

| ICD-10 Code | Diagnosis | Typical Cost |
|-------------|-----------|-------------|
| J18.9 | Pneumonia | $8,000 |
| I21.9 | Acute Myocardial Infarction | $45,000 |
| S72.001A | Femur Fracture | $35,000 |
| M54.5 | Low Back Pain | $2,500 |
| K80.20 | Gallstone | $15,000 |
| E11.9 | Type 2 Diabetes | $3,000 |
| J45.909 | Asthma | $1,500 |
| N18.3 | Chronic Kidney Disease | $25,000 |
| C50.919 | Breast Cancer | $85,000 |
| M17.11 | Knee Osteoarthritis | $18,000 |

## License

Built for the AgentField Hackathon.
