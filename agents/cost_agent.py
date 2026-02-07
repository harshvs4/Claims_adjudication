"""
Cost Analyzer Agent - Independent agent for cost reasonableness assessment
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentfield import Agent, AIConfig
from config import AGENTFIELD_SERVER, AI_MODEL, AI_TEMPERATURE, DEV_MODE
from models.claim import Claim
from models.decision import CostAssessment
from skills.data_extraction import load_claim
from skills.cost_benchmarks import get_cost_benchmarks, calculate_cost_variance

# Create independent cost agent
cost_agent = Agent(
    node_id="cost-analyzer",
    agentfield_server=AGENTFIELD_SERVER,
    version="1.0.0",
    dev_mode=DEV_MODE,
    ai_config=AIConfig(
        model=AI_MODEL,
        temperature=AI_TEMPERATURE,
    ),
)


@cost_agent.reasoner(tags=["cost", "analysis"])
async def evaluate_cost_reasonableness(claim_id: str) -> dict:
    """
    Assess if claimed costs are reasonable.

    Args:
        claim_id: The claim ID to evaluate

    Returns:
        CostAssessment as dict
    """
    cost_agent.note(f"💰 Cost analyzer evaluating {claim_id}")

    # Load claim
    claim = load_claim(claim_id)

    # Get cost benchmarks
    benchmarks = get_cost_benchmarks(claim.diagnosis_code, claim.severity)
    variance = calculate_cost_variance(claim.total_claimed_amount, benchmarks['typical'])

    # Retrieve medical and fraud assessments from memory
    medical_data = await cost_agent.memory.get(f"claim:{claim_id}:medical_assessment")
    fraud_data = await cost_agent.memory.get(f"claim:{claim_id}:fraud_assessment")

    prompt = f"""You are a cost analyst evaluating claim {claim_id}.

COST INFORMATION:
- Claimed Amount: ${claim.total_claimed_amount:,.2f}
- Expected Range: ${benchmarks['min']:,.2f} - ${benchmarks['max']:,.2f}
- Typical Cost: ${benchmarks['typical']:,.2f}
- Variance: {variance:.1f}%

PROCEDURES PERFORMED:
{chr(10).join([f"- {p.name}: ${p.cost:,.2f}" for p in claim.procedures])}

PROVIDER:
- Name: {claim.provider.name}
- Type: {claim.provider.type}
- Reputation: {claim.provider.reputation}

CONTEXT FROM OTHER AGENTS:
Medical Assessment:
{f"  - Medically Necessary: {medical_data.get('is_medically_necessary')}" if medical_data else "  - Pending"}
{f"  - Reasoning: {medical_data.get('reasoning', 'N/A')[:200]}" if medical_data else ""}

Fraud Risk:
{f"  - Risk Score: {fraud_data.get('fraud_risk_score')}" if fraud_data else "  - Pending"}
{f"  - Red Flags: {', '.join(fraud_data.get('red_flags', [])[:3])}" if fraud_data else ""}

EVALUATE:
1. Is the cost reasonable given the diagnosis, severity, and procedures?
2. Does provider reputation explain any cost variance?
   - Excellent providers may charge 10-20% more
   - Academic medical centers may have higher costs
   - Suspicious providers with inflated costs are red flags
3. Are there legitimate reasons for costs above typical range?
   - Complex cases
   - Complications
   - Specialized care
   - Geographic factors
4. Does medical necessity support the cost level?

Provide detailed reasoning for cost assessment.
"""

    result = await cost_agent.ai(
        prompt,
        schema=CostAssessment
    )

    result.claim_id = claim_id
    result.expected_range_min = benchmarks['min']
    result.expected_range_max = benchmarks['max']
    result.variance_percentage = variance

    # Store in shared memory
    await cost_agent.memory.set(
        key=f"claim:{claim_id}:cost_assessment",
        data=result.model_dump()
    )

    cost_agent.note(
        f"✅ Cost analysis complete: "
        f"{'REASONABLE' if result.cost_reasonable else 'QUESTIONABLE'}"
    )

    return result.model_dump()


if __name__ == "__main__":
    print("=" * 70)
    print("💰 COST ANALYZER AGENT")
    print("=" * 70)
    print(f"\nAgent ID: cost-analyzer")
    print(f"Model: {AI_MODEL}")
    print(f"Server: {AGENTFIELD_SERVER}")
    print("\nEndpoints:")
    print("  - evaluate_cost_reasonableness")
    print("\n" + "=" * 70)
    print("Starting cost agent...\n")

    cost_agent.run()
