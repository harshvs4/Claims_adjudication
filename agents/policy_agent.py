"""
Policy Agent - Independent agent for policy compliance checking
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentfield import Agent, AIConfig
from config import AGENTFIELD_SERVER, AI_MODEL, AI_TEMPERATURE, DEV_MODE
from models.claim import Claim
from models.decision import PolicyAssessment
from skills.data_extraction import load_claim

# Create independent policy agent
policy_agent = Agent(
    node_id="policy-checker",
    agentfield_server=AGENTFIELD_SERVER,
    version="1.0.0",
    dev_mode=DEV_MODE,
    ai_config=AIConfig(
        model=AI_MODEL,
        temperature=AI_TEMPERATURE,
    ),
)


@policy_agent.reasoner(tags=["policy", "compliance"])
async def verify_policy_coverage(claim_id: str) -> dict:
    """
    Verify policy coverage and check for exclusions.

    Args:
        claim_id: The claim ID to evaluate

    Returns:
        PolicyAssessment as dict
    """
    policy_agent.note(f"📄 Policy checker evaluating {claim_id}")

    # Load claim
    claim = load_claim(claim_id)

    prompt = f"""You are a policy compliance specialist reviewing claim {claim_id}.

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
- PPO plans: Comprehensive coverage, in-network preferred
- HMO plans: Requires network providers, referrals needed
- High-deductible plans: Coverage after deductible met

Provide detailed reasoning for coverage determination.
"""

    result = await policy_agent.ai(
        prompt,
        schema=PolicyAssessment
    )

    result.claim_id = claim_id

    # Store in shared memory
    await policy_agent.memory.set(
        key=f"claim:{claim_id}:policy_assessment",
        data=result.model_dump()
    )

    policy_agent.note(
        f"✅ Policy check complete: "
        f"{'COVERED' if result.covered_under_policy else 'NOT COVERED'}"
    )

    return result.model_dump()


if __name__ == "__main__":
    print("=" * 70)
    print("📄 POLICY CHECKER AGENT")
    print("=" * 70)
    print(f"\nAgent ID: policy-checker")
    print(f"Model: {AI_MODEL}")
    print(f"Server: {AGENTFIELD_SERVER}")
    print("\nEndpoints:")
    print("  - verify_policy_coverage")
    print("\n" + "=" * 70)
    print("Starting policy agent...\n")

    policy_agent.run()
