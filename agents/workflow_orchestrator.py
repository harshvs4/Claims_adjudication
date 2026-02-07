"""
Workflow Orchestrator Agent - Coordinates specialist agents using app.call()
Creates visual workflow with multiple boxes in AgentField UI
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from agentfield import Agent, AIConfig
from config import AGENTFIELD_SERVER, AI_MODEL, AI_TEMPERATURE, DEV_MODE
from models.decision import (
    MedicalAssessment,
    FraudAssessment,
    PolicyAssessment,
    CostAssessment,
    FinalDecision,
    AdjudicationResult
)
from skills.data_extraction import load_claim

# Create orchestrator agent
orchestrator = Agent(
    node_id="workflow-orchestrator",
    agentfield_server=AGENTFIELD_SERVER,
    version="1.0.0",
    dev_mode=DEV_MODE,
    ai_config=AIConfig(
        model=AI_MODEL,
        temperature=AI_TEMPERATURE,
    ),
)


@orchestrator.reasoner(tags=["orchestrator", "coordinator", "main"])
async def adjudicate_claim(claim_id: str) -> dict:
    """
    MAIN WORKFLOW ENDPOINT

    Coordinates all specialist agents using app.call() to create
    a visual workflow in AgentField UI with multiple boxes.

    Workflow:
    orchestrator (parent)
    ├── medical-reasoner.evaluate_medical_necessity
    ├── fraud-detector.detect_fraud_patterns
    ├── policy-checker.verify_policy_coverage
    ├── cost-analyzer.evaluate_cost_reasonableness
    └── final decision synthesis

    Args:
        claim_id: The claim ID to adjudicate

    Returns:
        Complete AdjudicationResult with all assessments
    """
    start_time = time.time()

    orchestrator.note(f"🎯 Starting workflow adjudication for {claim_id}")

    # Load claim for context
    claim = load_claim(claim_id)

    # Step 1: Call Medical Reasoner Agent
    orchestrator.note("📞 Step 1/4: Calling medical-reasoner...")
    medical_result = await orchestrator.call(
        "medical-reasoner.evaluate_medical_necessity",
        claim_id=claim_id
    )
    medical = MedicalAssessment(**medical_result)
    orchestrator.note(f"✅ Medical: Necessary={medical.is_medically_necessary}")

    # Step 2: Call Fraud Detector Agent (reads medical from memory)
    orchestrator.note("📞 Step 2/4: Calling fraud-detector...")
    fraud_result = await orchestrator.call(
        "fraud-detector.detect_fraud_patterns",
        claim_id=claim_id
    )
    fraud = FraudAssessment(**fraud_result)
    orchestrator.note(f"✅ Fraud: Risk={fraud.fraud_risk_score:.2f}")

    # Step 3: Call Policy Checker Agent
    orchestrator.note("📞 Step 3/4: Calling policy-checker...")
    policy_result = await orchestrator.call(
        "policy-checker.verify_policy_coverage",
        claim_id=claim_id
    )
    policy = PolicyAssessment(**policy_result)
    orchestrator.note(f"✅ Policy: Covered={policy.covered_under_policy}")

    # Step 4: Call Cost Analyzer Agent (reads medical + fraud from memory)
    orchestrator.note("📞 Step 4/4: Calling cost-analyzer...")
    cost_result = await orchestrator.call(
        "cost-analyzer.evaluate_cost_reasonableness",
        claim_id=claim_id
    )
    cost = CostAssessment(**cost_result)
    orchestrator.note(f"✅ Cost: Reasonable={cost.cost_reasonable}")

    # Step 5: Synthesize Final Decision
    orchestrator.note("🤔 Synthesizing final decision...")

    decision_prompt = f"""You are the claims adjudication coordinator making the FINAL DECISION.

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

✅ APPROVE: All positive, low fraud risk (<0.3), medically necessary, covered, reasonable cost
⚠️ APPROVE_WITH_REVIEW: Borderline case, approve but flag for review
🔍 INVESTIGATE: Fraud risk 0.5-0.7, unclear necessity, needs deeper review
❌ DENY: High fraud risk (>0.7), not necessary, policy exclusions apply

═══════════════════════════════════════════════════════════

Make the final decision:
1. Choose: APPROVE, APPROVE_WITH_REVIEW, INVESTIGATE, or DENY
2. Specify approved amount (may be partial)
3. Provide denial reason if denying
4. Set investigation_required flag if needed
5. List 3-5 KEY FACTORS influencing decision
6. Provide detailed reasoning

CRITICAL: Patient wellbeing first for legitimate needs. Fraud prevention essential. Policy compliance required.
"""

    decision = await orchestrator.ai(
        decision_prompt,
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
        f"✅ WORKFLOW COMPLETE: {decision.decision} "
        f"(confidence: {decision.confidence:.2f}, time: {processing_time}ms)"
    )

    return result.model_dump()


if __name__ == "__main__":
    print("=" * 70)
    print("🎯 WORKFLOW ORCHESTRATOR AGENT")
    print("=" * 70)
    print(f"\nAgent ID: workflow-orchestrator")
    print(f"Model: {AI_MODEL}")
    print(f"Server: {AGENTFIELD_SERVER}")
    print("\nWorkflow Structure:")
    print("  workflow-orchestrator (parent)")
    print("  ├── medical-reasoner.evaluate_medical_necessity")
    print("  ├── fraud-detector.detect_fraud_patterns")
    print("  ├── policy-checker.verify_policy_coverage")
    print("  └── cost-analyzer.evaluate_cost_reasonableness")
    print("\nThis creates a visual DAG with 5 boxes in AgentField UI!")
    print("\nEndpoint:")
    print("  - adjudicate_claim ⭐ MAIN WORKFLOW")
    print("\n" + "=" * 70)
    print("Starting workflow orchestrator...\n")

    orchestrator.run()
