"""
Medical Reasoner - AI-powered medical necessity evaluation
"""

from agentfield import Agent
from models.claim import Claim
from models.decision import MedicalAssessment


async def evaluate_medical_necessity(app: Agent, claim: Claim) -> MedicalAssessment:
    """
    Evaluate if treatment is medically necessary using AI reasoning.
    
    Args:
        app: AgentField Agent instance
        claim: Claim object to evaluate
        
    Returns:
        MedicalAssessment with AI evaluation
    """
    
    prompt = f"""You are a board-certified medical reviewer with expertise in insurance claims.

PATIENT & DIAGNOSIS:
- Patient Age: {claim.policyholder.age} years
- Diagnosis: {claim.diagnosis_name} (ICD-10: {claim.diagnosis_code})
- Severity Level: {claim.severity}
- Prior Medical Claims: {claim.policyholder.prior_claims_count}

TREATMENT PROVIDED:
{chr(10).join([f"- {p.name} (CPT: {p.code}, Cost: ${p.cost:,.2f})" for p in claim.procedures])}

CLINICAL NOTES:
{claim.medical_notes}

PROVIDER CONTEXT:
- Facility: {claim.provider.name}
- Type: {claim.provider.type}
- Reputation: {claim.provider.reputation}

EVALUATE:
1. Is the treatment medically necessary for this specific diagnosis?
2. Are the specific procedures appropriate for this condition and severity?
3. Are there any procedures that seem unrelated or excessive?
4. What is your confidence level (0-1) in this assessment?

Provide detailed clinical reasoning that would withstand peer review.
Be thorough but fair - legitimate medical needs should be supported.
"""
    
    result = await app.ai(
        prompt=prompt,
        schema=MedicalAssessment
    )
    
    result.claim_id = claim.claim_id
    
    # Store in shared memory
    await app.memory.set(
        key=f"claim:{claim.claim_id}:medical_assessment",
        value=result.model_dump()
    )
    
    await app.note(
        f"✅ Medical assessment complete: "
        f"Necessary={result.is_medically_necessary}, "
        f"Confidence={result.confidence:.2f}"
    )
    
    return result