"""
Cost Analyzer - AI-powered cost reasonableness assessment
"""

from agentfield import Agent
from models.claim import Claim
from models.decision import CostAssessment
from skills.cost_benchmarks import get_cost_benchmarks, calculate_cost_variance


async def evaluate_cost_reasonableness(app: Agent, claim: Claim) -> CostAssessment:
    """
    Assess if claimed costs are reasonable.
    
    Args:
        app: AgentField Agent instance
        claim: Claim object to evaluate
        
    Returns:
        CostAssessment with cost analysis
    """
    
    # Get cost benchmarks
    benchmarks = get_cost_benchmarks(claim.diagnosis_code, claim.severity)
    variance = calculate_cost_variance(claim.total_claimed_amount, benchmarks['typical'])
    
    # Retrieve medical and fraud assessments from memory
    medical_data = await app.memory.get(f"claim:{claim.claim_id}:medical_assessment")
    fraud_data = await app.memory.get(f"claim:{claim.claim_id}:fraud_assessment")
    
    prompt = f"""You are a cost analyst evaluating claim {claim.claim_id}.

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
    
    result = await app.ai(
        prompt=prompt,
        schema=CostAssessment
    )
    
    result.claim_id = claim.claim_id
    result.expected_range_min = benchmarks['min']
    result.expected_range_max = benchmarks['max']
    result.variance_percentage = variance
    
    # Store in shared memory
    await app.memory.set(
        key=f"claim:{claim.claim_id}:cost_assessment",
        value=result.model_dump()
    )
    
    await app.note(
        f"💰 Cost analysis complete: "
        f"{'REASONABLE' if result.cost_reasonable else 'QUESTIONABLE'}"
    )
    
    return result