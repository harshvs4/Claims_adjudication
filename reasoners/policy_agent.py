"""
Policy Agent - AI-powered policy compliance checking
"""

from agentfield import Agent
from models.claim import Claim
from models.decision import PolicyAssessment


async def verify_policy_coverage(app: Agent, claim: Claim) -> PolicyAssessment:
    """
    Verify policy coverage and check for exclusions.
    
    Args:
        app: AgentField Agent instance
        claim: Claim object to evaluate
        
    Returns:
        PolicyAssessment with coverage analysis
    """
    
    prompt = f"""You are a policy compliance specialist reviewing claim {claim.claim_id}.

POLICY INFORMATION:
- Policy Type: {claim.policyholder.policy_type}
- Coverage Limit: ${claim.policyholder.coverage_limit:,}
- Claimed Amount: ${claim.total_claimed_amount:,.2f}
- Policy Start Date: {claim.policyholder.policy_start_date}

CLAIM DETAILS:
- Diagnosis: {claim.diagnosis_name}
- Treatment: {', '.join([p.name for p in claim.procedures[:5]])}
- Provider Type: {claim.provider.type}
- Incident Date: {claim.incident_date}

EVALUATE:
1. Is this diagnosis/treatment covered under a {claim.policyholder.policy_type} plan?
2. Are there any exclusions that apply?
   - Pre-existing conditions
   - Experimental treatments
   - Cosmetic procedures
   - Out-of-network providers (if applicable)
3. Does the claimed amount exceed policy limits?
4. Any waiting periods or other policy restrictions?

Common Coverage Rules:
- Gold plans: Comprehensive coverage, low exclusions
- Silver plans: Standard coverage, some exclusions
- Bronze plans: Basic coverage, more exclusions

Provide detailed reasoning for coverage determination.
"""
    
    result = await app.ai(
        prompt=prompt,
        schema=PolicyAssessment
    )
    
    result.claim_id = claim.claim_id
    
    # Store in shared memory
    await app.memory.set(
        key=f"claim:{claim.claim_id}:policy_assessment",
        value=result.model_dump()
    )
    
    await app.note(
        f"📋 Policy check complete: "
        f"{'COVERED' if result.covered_under_policy else 'NOT COVERED'}"
    )
    
    return result