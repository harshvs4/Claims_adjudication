"""
Orchestrator Agent - Main coordinator that calls specialist agents and synthesizes results
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import time
from agentfield import Agent, AIConfig
from config import AGENTFIELD_SERVER, AI_MODEL, AI_TEMPERATURE, DEV_MODE
from models.decision import (
    MedicalAssessment,
    FraudAssessment,
    PolicyAssessment,
    CostAssessment,
    FinalDecision,
    AdjudicationResult,
    DecisionType
)
from skills.data_extraction import load_claim

# Create orchestrator agent
orchestrator = Agent(
    node_id="claims-orchestrator",
    agentfield_server=AGENTFIELD_SERVER,
    version="1.0.0",
    dev_mode=DEV_MODE,
    ai_config=AIConfig(
        model=AI_MODEL,
        temperature=AI_TEMPERATURE,
    ),
)


async def call_specialist_agent(agent_id: str, endpoint: str, claim_id: str) -> dict:
    """
    Call a specialist agent via HTTP.

    Args:
        agent_id: The agent node ID
        endpoint: The endpoint name
        claim_id: The claim ID to process

    Returns:
        Agent response result
    """
    url = f"{AGENTFIELD_SERVER}/api/v1/execute/{agent_id}.{endpoint}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            url,
            json={"input": {"claim_id": claim_id}}
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "succeeded":
            raise Exception(f"Agent {agent_id} failed: {data.get('error', 'Unknown error')}")

        return data["result"]


@orchestrator.reasoner(tags=["orchestrator", "coordinator", "main"])
async def adjudicate_claim(claim_id: str) -> dict:
    """
    MAIN ORCHESTRATION ENDPOINT

    Coordinates all specialist agents to make final adjudication decision.

    Flow:
    1. Call medical agent → medical necessity
    2. Call fraud agent → fraud detection (reads medical from memory)
    3. Call policy agent → coverage verification
    4. Call cost agent → cost analysis (reads medical + fraud from memory)
    5. Synthesize final decision

    Args:
        claim_id: The claim ID to adjudicate

    Returns:
        Complete AdjudicationResult
    """
    start_time = time.time()

    orchestrator.note(f"🎯 Orchestrator starting adjudication for {claim_id}")

    # Load claim for context
    claim = load_claim(claim_id)

    # Step 1: Call Medical Reasoner
    orchestrator.note("📞 Calling medical-reasoner agent...")
    medical_result = await call_specialist_agent(
        agent_id="medical-reasoner",
        endpoint="evaluate_medical_necessity",
        claim_id=claim_id
    )
    medical = MedicalAssessment(**medical_result)
    orchestrator.note(f"✅ Medical: Necessary={medical.is_medically_necessary}")

    # Step 2: Call Fraud Detector (reads medical from memory)
    orchestrator.note("📞 Calling fraud-detector agent...")
    fraud_result = await call_specialist_agent(
        agent_id="fraud-detector",
        endpoint="detect_fraud_patterns",
        claim_id=claim_id
    )
    fraud = FraudAssessment(**fraud_result)
    orchestrator.note(f"✅ Fraud: Risk={fraud.fraud_risk_score:.2f}")

    # Step 3: Call Policy Checker
    orchestrator.note("📞 Calling policy-checker agent...")
    policy_result = await call_specialist_agent(
        agent_id="policy-checker",
        endpoint="verify_policy_coverage",
        claim_id=claim_id
    )
    policy = PolicyAssessment(**policy_result)
    orchestrator.note(f"✅ Policy: Covered={policy.covered_under_policy}")

    # Step 4: Call Cost Analyzer (reads medical + fraud from memory)
    orchestrator.note("📞 Calling cost-analyzer agent...")
    cost_result = await call_specialist_agent(
        agent_id="cost-analyzer",
        endpoint="evaluate_cost_reasonableness",
        claim_id=claim_id
    )
    cost = CostAssessment(**cost_result)
    orchestrator.note(f"✅ Cost: Reasonable={cost.cost_reasonable}")

    # Step 5: Synthesize Final Decision
    orchestrator.note("🤔 Synthesizing final decision...")

    prompt = f"""You are the claims adjudication coordinator making the FINAL DECISION.

CLAIM OVERVIEW:
- Claim ID: {claim_id}
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
- Red Flags: {', '.join(fraud.red_flags) if fraud.red_flags else 'None'}
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

    decision = await orchestrator.ai(
        prompt,
        schema=FinalDecision
    )

    decision.claim_id = claim_id

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
        agents_consulted=['medical-reasoner', 'fraud-detector', 'policy-checker', 'cost-analyzer', 'orchestrator']
    )

    # Store in global memory for audit trail
    await orchestrator.memory.global_scope.set(
        key=f"adjudication:{claim_id}:final",
        data=result.model_dump()
    )

    orchestrator.note(
        f"✅ ADJUDICATION COMPLETE: {decision.decision} "
        f"(confidence: {decision.confidence:.2f}, time: {processing_time}ms)"
    )

    return result.model_dump()


if __name__ == "__main__":
    print("=" * 70)
    print("🎯 CLAIMS ORCHESTRATOR AGENT")
    print("=" * 70)
    print(f"\nAgent ID: claims-orchestrator")
    print(f"Model: {AI_MODEL}")
    print(f"Server: {AGENTFIELD_SERVER}")
    print("\nOrchestrates:")
    print("  1. medical-reasoner → Medical necessity")
    print("  2. fraud-detector → Fraud detection")
    print("  3. policy-checker → Policy coverage")
    print("  4. cost-analyzer → Cost analysis")
    print("  5. Final decision synthesis")
    print("\nEndpoints:")
    print("  - adjudicate_claim ⭐ MAIN ENDPOINT")
    print("\n" + "=" * 70)
    print("Starting orchestrator agent...\n")

    orchestrator.run()
