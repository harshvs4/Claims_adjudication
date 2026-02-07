# 🏥 Claims Adjudication System

Multi-agent health insurance claims adjudication using AgentField with memory and vector search.

## 🎯 What This Does

Replaces rigid rule-based claims processing with intelligent AI agents that:
- **Medical Reviewer**: Evaluates medical necessity
- **Fraud Detector**: Identifies fraud patterns using vector search
- **Policy Agent**: Checks coverage compliance
- **Cost Analyzer**: Assesses cost reasonableness
- **Coordinator**: Synthesizes all inputs into final decision

**The Innovation:** Agents share findings via memory, use vector search to find similar historical claims, and reason through edge cases that would auto-deny in traditional systems.

## 📁 Project Structure

```
claims-adjudication/
├── main.py                       # Main agent entry point
├── config.py                     # Configuration
├── requirements.txt              # Python dependencies
├── .env                          # API keys (create from .env.template)
├── data/
│   └── synthetic_claims.json     # Test data
├── models/                       # Pydantic schemas
│   ├── claim.py                  # Claim data models
│   └── decision.py               # Decision models
├── reasoners/                    # AI-powered decision makers
│   ├── medical_reasoner.py       # Medical necessity
│   ├── fraud_detector.py         # Fraud detection
│   ├── policy_agent.py           # Policy compliance
│   ├── cost_analyzer.py          # Cost analysis
│   └── adjudication_coordinator.py  # Final decision
├── skills/                       # Deterministic functions
│   ├── data_extraction.py        # Load claims
│   ├── fraud_scoring.py          # Fraud scoring
│   ├── cost_benchmarks.py        # Cost benchmarks
│   └── medical_codes.py          # ICD-10/CPT lookups
└── utils/                        # Helper functions
    └── helpers.py
```

## 🚀 Quick Start

### 1. Install AgentField

```bash
curl -sSf https://agentfield.ai/get | sh
source ~/.zshrc
af --version
```

### 2. Setup Project

```bash
# Clone/download project files
cd claims-adjudication

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env from template
cp .env.template .env
# Edit .env and add your API key
```

### 3. Add Your Data

```bash
# Copy your synthetic claims data
cp /path/to/synthetic_claims.json data/
```

### 4. Start AgentField Control Plane

```bash
# In a separate terminal
af server
```

### 5. Run the Agent

```bash
# In your project directory
python main.py
```

You should see:
```
═══════════════════════════════════════════════════════════
🏥 CLAIMS ADJUDICATION SYSTEM
═══════════════════════════════════════════════════════════

Agent: claims-adjudicator
...
Starting agent...
```

## 🧪 Testing

### Process a Single Claim

```bash
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.adjudicate_claim \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}' | jq
```

### Test Different Claim Types

```bash
# Clean claim (should approve)
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.adjudicate_claim \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Fraud claim (should deny)
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.adjudicate_claim \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10048"}}'

# Edge case (should approve with review)
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.adjudicate_claim \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10067"}}'
```

### Test Individual Agents

```bash
# Medical assessment only
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.assess_medical_necessity \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10001"}}'

# Fraud detection only
curl -X POST http://localhost:8080/api/v1/execute/claims-adjudicator.analyze_fraud_risk \
  -H "Content-Type: application/json" \
  -d '{"input": {"claim_id": "CLM10048"}}'
```

## 🎬 Demo Flow

**3-Minute Demo Script:**

1. **Clean Claim (30 sec)**: Show quick approval for legitimate case
2. **Fraud Claim (60 sec)**: Show fraud detection with vector search finding similar fraud
3. **Edge Case (60 sec)**: **THE WINNER** - Show reasoning through complex case that rules would deny
4. **Closing (30 sec)**: Emphasize "No Redis, No Kafka, just reasoning"

## 🏗️ Architecture

### Reasoners vs Skills

**Reasoners** (AI-powered):
- Use `@app.reasoner()` decorator
- Make decisions requiring judgment
- Call `await app.ai()` for inference
- Store results in memory

**Skills** (Deterministic):
- Use `@app.skill()` decorator
- Execute predictable logic
- Database queries, calculations
- Fast and reliable

### Memory Flow

```python
# Medical agent stores findings
await app.memory.set(f"claim:{claim_id}:medical", result)

# Fraud agent retrieves them
medical_data = await app.memory.get(f"claim:{claim_id}:medical")

# No Redis, no config - it just works!
```

### Vector Search

```python
# Store claim with embedding
await app.memory.set_vector(
    id=claim_id,
    embedding=claim_description,
    metadata={...}
)

# Find similar claims
similar = await app.memory.similarity_search(query=..., top_k=5)

# No Pinecone, no setup - built in!
```

## 🔧 Configuration

Edit `config.py` to customize:
- Cost benchmarks
- Fraud thresholds
- AI model settings
- Memory scopes

## 📊 Understanding the Response

```json
{
  "claim_id": "CLM10001",
  "final_decision": {
    "decision": "APPROVE",
    "approved_amount": 7750.15,
    "confidence": 0.95,
    "reasoning": "...",
    "key_factors": ["Medical necessity confirmed", "No fraud indicators", ...]
  },
  "medical_assessment": { ... },
  "fraud_assessment": { ... },
  "policy_assessment": { ... },
  "cost_assessment": { ... },
  "processing_time_ms": 3250
}
```

## 🐛 Troubleshooting

### Agent won't start
```bash
# Check control plane is running
curl http://localhost:8080/health

# Verify .env has API key
cat .env
```

### Claims not found
```bash
# Verify data file exists
ls -la data/synthetic_claims.json

# Check claim IDs
python -c "import json; print([c['claim_id'] for c in json.load(open('data/synthetic_claims.json'))[:5]])"
```

### Import errors
```bash
# Make sure you're in project root
pwd

# Reinstall dependencies
pip install -r requirements.txt
```

## 🏆 Why This Wins

1. **New Problem Space**: Claims haven't gone multi-agent
2. **Replaces Complexity**: No DAGs, no queues, just `@app.reasoner()`
3. **High Leverage**: Every claim = time/money saved
4. **Previously Impossible**: Edge case reasoning that rules can't handle
5. **Your Expertise**: Munich Re domain knowledge makes it credible

## 📝 License

Built for AgentField Hackathon

## 🙏 Acknowledgments

- AgentField for the infrastructure
- Munich Re for the real-world problem context
- Anthropic/OpenAI for the LLMs