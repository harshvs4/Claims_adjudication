"""
Medical Reasoner Agent - Independent agent for medical necessity evaluation
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentfield import Agent, AIConfig
from config import AGENTFIELD_SERVER, AI_MODEL, AI_TEMPERATURE, DEV_MODE
from models.claim import Claim
from models.decision import MedicalAssessment
from skills.data_extraction import load_claim

# Create independent medical agent
medical_agent = Agent(
    node_id="medical-reasoner",
    agentfield_server=AGENTFIELD_SERVER,
    version="1.0.0",
    dev_mode=DEV_MODE,
    ai_config=AIConfig(
        model=AI_MODEL,
        temperature=AI_TEMPERATURE,
    ),
)


@medical_agent.reasoner(tags=["medical", "assessment"])
async def evaluate_medical_necessity(claim_id: str) -> dict:
    """
    Evaluate medical necessity for a claim.

    Args:
        claim_id: The claim ID to evaluate

    Returns:
        MedicalAssessment as dict
    """
    medical_agent.note(f"🏥 Medical reasoner evaluating {claim_id}")

    # Load claim
    claim = load_claim(claim_id)

    # Build AI prompt
    prompt = f"""You are a medical review specialist with expertise in evidence-based medicine.

CLAIM TO REVIEW: {claim.claim_id}

PATIENT INFORMATION:
- Age: {claim.policyholder.age} years
- Gender: {claim.policyholder.gender}
- Policy Type: {claim.policyholder.policy_type}
- Prior Claims: {claim.policyholder.prior_claims_count}

DIAGNOSIS:
- Code: {claim.diagnosis_code}
- Name: {claim.diagnosis_name}
- Severity: {claim.severity}

PROCEDURES REQUESTED:
{chr(10).join([f"  • {p.code}: {p.name} (${p.cost:,.2f})" for p in claim.procedures])}

TOTAL CLAIMED: ${claim.total_claimed_amount:,.2f}

MEDICAL NOTES:
{claim.medical_notes}

PROVIDER:
- Name: {claim.provider.name}
- Type: {claim.provider.type}
- Reputation: {claim.provider.reputation}

═══════════════════════════════════════════════════════════

EVALUATION CRITERIA:

1. **Medical Necessity**: Is this treatment necessary given the diagnosis?
2. **Treatment Appropriateness**: Are the procedures appropriate for this condition?
3. **Over-Treatment Detection**: Any signs of unnecessary procedures?

EVALUATE:
1. Is this treatment medically necessary?
2. Are the procedures appropriate for the diagnosis and severity?
3. Are there any signs of over-treatment or unnecessary care?
4. What is your confidence level (0-1)?
5. Provide detailed medical reasoning

Consider:
- Evidence-based treatment guidelines
- Severity of condition
- Standard of care for this diagnosis
- Patient age and comorbidity factors
- Provider reputation and past patterns
"""

    # Get AI assessment
    result = await medical_agent.ai(
        prompt,
        schema=MedicalAssessment
    )

    result.claim_id = claim_id

    # Store in shared memory for other agents
    await medical_agent.memory.set(
        key=f"claim:{claim_id}:medical_assessment",
        data=result.model_dump()
    )

    medical_agent.note(
        f"✅ Medical evaluation complete: "
        f"Necessary={result.is_medically_necessary}, "
        f"Appropriate={result.treatment_appropriate}, "
        f"Confidence={result.confidence:.2f}"
    )

    return result.model_dump()


if __name__ == "__main__":
    print("=" * 70)
    print("🏥 MEDICAL REASONER AGENT")
    print("=" * 70)
    print(f"\nAgent ID: medical-reasoner")
    print(f"Model: {AI_MODEL}")
    print(f"Server: {AGENTFIELD_SERVER}")
    print("\nEndpoints:")
    print("  - evaluate_medical_necessity")
    print("\n" + "=" * 70)
    print("Starting medical agent...\n")

    medical_agent.run()
