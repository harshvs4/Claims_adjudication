"""
Claims Adjudication System - Main Entry Point
Multi-agent health insurance claims adjudication with memory and vector search
"""

from agentfield import Agent, AIConfig
from typing import List

# Import configuration
from config import (
    AGENTFIELD_SERVER,
    AGENT_NODE_ID,
    AGENT_VERSION,
    DEV_MODE,
    AI_MODEL,
    AI_TEMPERATURE
)

# Import models
from models.decision import AdjudicationResult

# Import skills (deterministic functions)
from skills.data_extraction import load_claim, extract_claim_summary
from skills.fraud_scoring import calculate_fraud_score
from skills.cost_benchmarks import get_cost_benchmarks

# Import reasoners (AI-powered decision makers)
from reasoners.medical_reasoner import evaluate_medical_necessity
from reasoners.fraud_detector import detect_fraud_patterns
from reasoners.policy_agent import verify_policy_coverage
from reasoners.cost_analyzer import evaluate_cost_reasonableness
from reasoners.adjudication_coordinator import coordinate_adjudication


# ==========================================
# AGENT SETUP
# ==========================================

app = Agent(
    node_id=AGENT_NODE_ID,
    agentfield_server=AGENTFIELD_SERVER,
    version=AGENT_VERSION,
    dev_mode=DEV_MODE,
    ai_config=AIConfig(
        model=AI_MODEL,
        temperature=AI_TEMPERATURE,
    ),
)


# ==========================================
# REGISTER SKILLS (Deterministic Functions)
# ==========================================

@app.skill(tags=["data", "extraction"])
def get_claim_data(claim_id: str) -> dict:
    """
    Load and extract claim summary.
    
    This is a deterministic function - no AI needed.
    """
    claim = load_claim(claim_id)
    return extract_claim_summary(claim)


@app.skill(tags=["fraud", "scoring"])
def get_fraud_indicators(claim_id: str) -> dict:
    """
    Calculate deterministic fraud indicators.
    
    Returns preliminary fraud score and flags.
    """
    claim = load_claim(claim_id)
    return calculate_fraud_score(claim)


@app.skill(tags=["cost", "benchmarks"])
def get_cost_benchmark(diagnosis_code: str, severity: str) -> dict:
    """
    Get cost benchmarks for diagnosis.
    
    Returns expected cost range.
    """
    return get_cost_benchmarks(diagnosis_code, severity)


# ==========================================
# REGISTER REASONERS (AI-Powered Functions)
# ==========================================

@app.reasoner(tags=["medical", "assessment"])
async def assess_medical_necessity(claim_id: str) -> dict:
    """
    AI-powered medical necessity evaluation.
    
    Evaluates if treatment is medically necessary and appropriate.
    Stores findings in shared memory for other agents.
    """
    claim = load_claim(claim_id)
    result = await evaluate_medical_necessity(app, claim)
    return result.model_dump()


@app.reasoner(tags=["fraud", "detection", "vector-search"])
async def analyze_fraud_risk(claim_id: str) -> dict:
    """
    AI-powered fraud detection with vector search.
    
    Uses:
    1. Deterministic fraud scoring
    2. Medical assessment from memory
    3. Vector search for similar historical claims
    4. AI pattern analysis
    """
    claim = load_claim(claim_id)
    result = await detect_fraud_patterns(app, claim)
    return result.model_dump()


@app.reasoner(tags=["policy", "compliance"])
async def check_policy_coverage(claim_id: str) -> dict:
    """
    AI-powered policy compliance check.
    
    Verifies coverage and checks for exclusions.
    """
    claim = load_claim(claim_id)
    result = await verify_policy_coverage(app, claim)
    return result.model_dump()


@app.reasoner(tags=["cost", "analysis"])
async def analyze_cost(claim_id: str) -> dict:
    """
    AI-powered cost reasonableness analysis.
    
    Assesses if costs are reasonable given context.
    """
    claim = load_claim(claim_id)
    result = await evaluate_cost_reasonableness(app, claim)
    return result.model_dump()


@app.reasoner(tags=["adjudication", "coordinator", "main"])
async def adjudicate_claim(claim_id: str) -> dict:
    """
    MAIN ENDPOINT: Complete claims adjudication.
    
    Orchestrates all specialist agents:
    1. Medical necessity evaluation
    2. Fraud pattern detection
    3. Policy compliance check
    4. Cost reasonableness analysis
    5. Final decision synthesis
    
    Returns complete adjudication with all assessments.
    
    This is your primary demo endpoint.
    """
    result = await coordinate_adjudication(
        app=app,
        claim_id=claim_id,
        medical_fn=evaluate_medical_necessity,
        fraud_fn=detect_fraud_patterns,
        policy_fn=verify_policy_coverage,
        cost_fn=evaluate_cost_reasonableness
    )
    
    return result.model_dump()


@app.reasoner(tags=["batch", "analytics"])
async def process_batch_claims(claim_ids: List[str]) -> dict:
    """
    Process multiple claims in batch.
    
    Returns analytics across all processed claims.
    """
    results = []
    
    for claim_id in claim_ids:
        try:
            result = await coordinate_adjudication(
                app=app,
                claim_id=claim_id,
                medical_fn=evaluate_medical_necessity,
                fraud_fn=detect_fraud_patterns,
                policy_fn=verify_policy_coverage,
                cost_fn=evaluate_cost_reasonableness
            )
            results.append(result.model_dump())
        except Exception as e:
            await app.note(f"❌ Error processing {claim_id}: {str(e)}")
    
    # Calculate analytics
    total = len(results)
    if total == 0:
        return {"total_processed": 0, "results": []}
    
    by_decision = {}
    for r in results:
        decision = r['final_decision']['decision']
        by_decision[decision] = by_decision.get(decision, 0) + 1
    
    avg_time = sum(r['processing_time_ms'] for r in results) / total
    
    return {
        'total_processed': total,
        'decisions_breakdown': by_decision,
        'avg_processing_time_ms': int(avg_time),
        'approval_rate': by_decision.get('APPROVE', 0) / total if total > 0 else 0,
        'results': results
    }


# ==========================================
# RUN AGENT
# ==========================================

if __name__ == "__main__":
    print("=" * 70)
    print("🏥 CLAIMS ADJUDICATION SYSTEM")
    print("=" * 70)
    print(f"\nAgent: {AGENT_NODE_ID}")
    print(f"Model: {AI_MODEL}")
    print(f"Temperature: {AI_TEMPERATURE}")
    print("\nFeatures:")
    print("  ✅ Memory-based agent coordination")
    print("  ✅ Vector search for fraud pattern detection")
    print("  ✅ Multi-agent reasoning (medical, fraud, policy, cost)")
    print("  ✅ Structured outputs via Pydantic schemas")
    print("  ✅ Modular architecture (skills + reasoners)")
    print("\nRegistered Endpoints:")
    print("  Skills (Deterministic):")
    print("    - get_claim_data")
    print("    - get_fraud_indicators")
    print("    - get_cost_benchmark")
    print("\n  Reasoners (AI-Powered):")
    print("    - assess_medical_necessity")
    print("    - analyze_fraud_risk")
    print("    - check_policy_coverage")
    print("    - analyze_cost")
    print("    - adjudicate_claim ⭐ MAIN DEMO ENDPOINT")
    print("    - process_batch_claims")
    print("\n" + "=" * 70)
    print("Starting agent...\n")
    
    app.run()