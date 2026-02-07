"""
Adjudication Coordinator - Final decision synthesis
"""

from agentfield import Agent
from models.claim import Claim
from models.decision import (
    MedicalAssessment,
    FraudAssessment,
    PolicyAssessment,
    CostAssessment,
    FinalDecision,
    AdjudicationResult,
    DecisionType
)
import time


async def make_final_decision(
    app: Agent,
    claim: Claim,
    medical: MedicalAssessment,
    fraud: FraudAssessment,
    policy: PolicyAssessment,
    cost: CostAssessment
) -> FinalDecision:
    """
    Synthesize all agent assessments into final adjudication decision.
    
    Args:
        app: AgentField Agent instance
        claim: Claim object
        medical: Medical assessment
        fraud: Fraud assessment
        policy: Policy assessment
        cost: Cost assessment
        
    Returns:
        FinalDecision with adjudication outcome
    """
    
    prompt = f"""You are the claims adjudication coordinator making the FINAL DECISION.

CLAIM OVERVIEW:
- Claim ID: {claim.claim_id}
- Patient: {claim.policyholder.age} years old
- Diagnosis: {claim.diagnosis_name} ({claim.severity})
- Provider: {claim.provider.name}
- Amount: ${claim.total_claimed_amount:,.2f}

═══════════════════════════════════════════════════════════

SPECIALIST ASSESSMENTS:

🏥 MEDICAL ASSESSMENT:
- Medically Necessary: {medical.is_medically_necessary}
- Treatment Appropriate: {medical.treatment_appropriate}
- Confidence: {medical.confidence:.2f}
- Reasoning: {medical.reasoning}

🔍 FRAUD ASSESSMENT:
- Risk Score: {fraud.fraud_risk_score:.2f}
- Red Flags: {', '.join(fraud.red_flags)}
- Similar Fraud Cases: {fraud.similar_fraud_cases_found}
- Pattern Analysis: {fraud.pattern_analysis}
- Recommendation: {fraud.recommendation}
- Reasoning: {fraud.reasoning}

📄 POLICY ASSESSMENT:
- Covered: {policy.covered_under_policy}
- Exclusions: {', '.join(policy.exclusions_apply) if policy.exclusions_apply else 'None'}
- Limits Exceeded: {policy.coverage_limits_exceeded}
- Reasoning: {policy.reasoning}

💰 COST ASSESSMENT:
- Cost Reasonable: {cost.cost_reasonable}
- Expected Range: ${cost.expected_range_min:,.2f} - ${cost.expected_range_max:,.2f}
- Variance: {cost.variance_percentage:.1f}%
- Reasoning: {cost.reasoning}

═══════════════════════════════════════════════════════════

DECISION FRAMEWORK:

✅ APPROVE:
- All assessments positive
- Low fraud risk (<0.3)
- Medically necessary
- Policy covered
- Cost reasonable

⚠️ APPROVE_WITH_REVIEW:
- Borderline case
- Moderate concerns but not disqualifying
- Approve but flag for human review
- Examples: High cost but justified, minor red flags but legitimate need

🔍 INVESTIGATE:
- Fraud risk 0.5-0.7
- Medical necessity unclear
- Significant cost variance without explanation
- Needs deeper review before decision

❌ DENY:
- High fraud risk (>0.7)
- Not medically necessary
- Policy exclusions apply
- Clear evidence of impropriety

═══════════════════════════════════════════════════════════

YOUR TASK:

Make the final decision by:
1. Choosing: APPROVE, APPROVE_WITH_REVIEW, INVESTIGATE, or DENY
2. Specifying approved amount (may be less than claimed if partial approval)
3. Providing denial reason if denying
4. Setting investigation_required flag if needed
5. Listing 3-5 KEY FACTORS that influenced your decision
6. Providing detailed reasoning that:
   - Explains how you weighted each specialist's input
   - Shows why this decision is fair to the patient
   - Demonstrates protection against fraud
   - Would withstand regulatory scrutiny

CRITICAL GUIDELINES:
- Patient wellbeing comes first for legitimate medical needs
- Fraud prevention is essential for system sustainability
- Policy compliance must be respected
- Decisions must be defensible and transparent

This decision will be stored in an immutable audit trail.
"""
    
    decision = await app.ai(
        prompt=prompt,
        schema=FinalDecision
    )
    
    decision.claim_id = claim.claim_id
    
    return decision


async def coordinate_adjudication(
    app: Agent,
    claim_id: str,
    medical_fn,
    fraud_fn,
    policy_fn,
    cost_fn
) -> AdjudicationResult:
    """
    Orchestrate all specialist agents and make final decision.
    
    Args:
        app: AgentField Agent instance
        claim_id: Claim ID to process
        medical_fn: Medical reasoner function
        fraud_fn: Fraud detector function
        policy_fn: Policy agent function
        cost_fn: Cost analyzer function
        
    Returns:
        Complete AdjudicationResult
    """
    start_time = time.time()
    
    await app.note(f"🎯 Starting adjudication for {claim_id}")
    
    # Load claim
    from skills.data_extraction import load_claim
    claim = load_claim(claim_id)
    
    # Trigger all specialist agents
    medical = await medical_fn(app, claim)
    fraud = await fraud_fn(app, claim)
    policy = await policy_fn(app, claim)
    cost = await cost_fn(app, claim)
    
    # Make final decision
    decision = await make_final_decision(app, claim, medical, fraud, policy, cost)
    
    # Calculate processing time
    processing_time = int((time.time() - start_time) * 1000)
    
    # Create complete result
    result = AdjudicationResult(
        claim_id=claim_id,
        final_decision=decision,
        medical_assessment=medical,
        fraud_assessment=fraud,
        policy_assessment=policy,
        cost_assessment=cost,
        processing_time_ms=processing_time,
        agents_consulted=['medical', 'fraud', 'policy', 'cost', 'coordinator']
    )
    
    # Store in global memory for audit trail
    await app.memory.set(
        key=f"adjudication:{claim_id}:final",
        value=result.model_dump(),
        scope="global"
    )
    
    await app.note(
        f"✅ ADJUDICATION COMPLETE: {decision.decision} "
        f"(confidence: {decision.confidence:.2f}, time: {processing_time}ms)"
    )
    
    return result