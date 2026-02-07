"""
Claims Adjudication Agent - Unified multi-reasoner agent
All specialist logic embedded in one agent for unified workflow
"""

import sys
from pathlib import Path
import time

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agentfield import Agent, AIConfig
from config import AGENTFIELD_SERVER, AI_MODEL, AI_TEMPERATURE, DEV_MODE
from models.claim import Claim
from models.decision import (
    MedicalAssessment,
    FraudAssessment,
    PolicyAssessment,
    CostAssessment,
    FinalDecision,
    AdjudicationResult
)
from skills.data_extraction import load_claim, get_claim_description
from skills.fraud_scoring import calculate_fraud_score
from skills.cost_benchmarks import get_cost_benchmarks, calculate_cost_variance
from fastembed import TextEmbedding

# Initialize embedding model for fraud detection
_embed_model = TextEmbedding("BAAI/bge-small-en-v1.5")


def _embed(text: str) -> list:
    """Generate embedding vector from text."""
    return list(_embed_model.embed([text]))[0].tolist()


# Create single unified agent
agent = Agent(
    node_id="claims-adjudicator",
    agentfield_server=AGENTFIELD_SERVER,
    version="1.0.0",
    dev_mode=DEV_MODE,
    ai_config=AIConfig(
        model=AI_MODEL,
        temperature=AI_TEMPERATURE,
    ),
)


# ============================================================================
# INTERNAL REASONER FUNCTIONS (not exposed as endpoints)
# ============================================================================

async def _evaluate_medical_necessity(claim: Claim) -> MedicalAssessment:
    """Internal: Evaluate medical necessity."""
    agent.note(f"🏥 Evaluating medical necessity for {claim.claim_id}")

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

EVALUATE:
1. Is this treatment medically necessary?
2. Are the procedures appropriate for the diagnosis and severity?
3. Are there any signs of over-treatment?
4. What is your confidence level (0-1)?
5. Provide detailed medical reasoning
"""

    result = await agent.ai(prompt, schema=MedicalAssessment)
    result.claim_id = claim.claim_id

    # Store in memory for other reasoners
    await agent.memory.set(
        key=f"claim:{claim.claim_id}:medical_assessment",
        data=result.model_dump()
    )

    agent.note(f"✅ Medical: Necessary={result.is_medically_necessary}, Confidence={result.confidence:.2f}")
    return result


async def _detect_fraud_patterns(claim: Claim) -> FraudAssessment:
    """Internal: Detect fraud with vector search."""
    agent.note(f"🔍 Detecting fraud patterns for {claim.claim_id}")

    # Get deterministic fraud indicators
    indicators = calculate_fraud_score(claim)

    # Retrieve medical assessment from memory
    medical_data = await agent.memory.get(f"claim:{claim.claim_id}:medical_assessment")

    # Create semantic representation for vector search
    claim_description = get_claim_description(claim)
    claim_embedding = _embed(claim_description)

    # Store claim with vector embedding
    await agent.memory.set_vector(
        key=claim.claim_id,
        embedding=claim_embedding,
        metadata={
            "claim_id": claim.claim_id,
            "diagnosis": claim.diagnosis_name,
            "provider": claim.provider.name,
            "provider_reputation": claim.provider.reputation,
            "amount": claim.total_claimed_amount,
            "fraud_score": indicators['fraud_score'],
            "actual_type": getattr(claim, 'claim_type', 'UNKNOWN')
        }
    )

    # Search for similar historical claims
    similar_claims = await agent.memory.similarity_search(
        query_embedding=claim_embedding,
        top_k=5
    )

    fraud_pattern_count = 0
    similar_details = []

    if similar_claims:
        for idx, similar in enumerate(similar_claims, 1):
            metadata = similar.get('metadata', {})
            is_fraud = metadata.get('actual_type') == 'FRAUD'
            if is_fraud:
                fraud_pattern_count += 1

            similar_details.append(
                f"{idx}. {metadata.get('diagnosis', 'Unknown')} - "
                f"${metadata.get('amount', 0):,.0f} at {metadata.get('provider', 'Unknown')} "
                f"[{'FRAUD' if is_fraud else 'LEGITIMATE'}]"
            )

    # AI fraud analysis
    prompt = f"""You are a fraud investigation specialist with expertise in healthcare fraud.

CLAIM UNDER REVIEW: {claim.claim_id}

CLAIM DETAILS:
- Diagnosis: {claim.diagnosis_name} ({claim.severity} severity)
- Provider: {claim.provider.name} (Reputation: {claim.provider.reputation})
- Amount Claimed: ${claim.total_claimed_amount:,.2f}

PROCEDURES BILLED:
{chr(10).join([f"  • {p.name}: ${p.cost:,.2f}" for p in claim.procedures])}

MEDICAL REVIEW FINDINGS:
{f"✓ Medical Necessity: {medical_data.get('is_medically_necessary')}" if medical_data else "⚠ Medical review pending"}
{f"  Reasoning: {medical_data.get('reasoning', 'N/A')[:200]}" if medical_data else ""}

FRAUD INDICATORS:
- Preliminary Score: {indicators['fraud_score']:.2f} / 1.0
- Red Flags: {len(indicators['flags'])}
{chr(10).join([f"  • {flag}" for flag in indicators['flags']]) if indicators['flags'] else "  • No red flags"}

HISTORICAL PATTERN ANALYSIS:
Found {len(similar_claims)} similar claims:
{chr(10).join(similar_details) if similar_details else '  • No similar claims found'}

⚠ CRITICAL: {fraud_pattern_count} of these similar claims were confirmed FRAUD

EVALUATE:
1. What is the final fraud risk score (0-1)?
2. What specific red flags exist?
3. Recommendation: APPROVE, INVESTIGATE, or DENY?
4. Detailed reasoning considering ALL context

Be thorough but fair. Catch fraud without denying legitimate care.
"""

    result = await agent.ai(prompt, schema=FraudAssessment)
    result.claim_id = claim.claim_id
    result.similar_fraud_cases_found = fraud_pattern_count

    if fraud_pattern_count > 2:
        result.pattern_analysis = f"HIGH RISK: {fraud_pattern_count}/5 similar claims were fraud"
    elif fraud_pattern_count > 0:
        result.pattern_analysis = f"MODERATE RISK: {fraud_pattern_count}/5 similar claims were fraud"
    else:
        result.pattern_analysis = "LOW PATTERN RISK: No similar fraud cases found"

    # Store in memory
    await agent.memory.set(
        key=f"claim:{claim.claim_id}:fraud_assessment",
        data=result.model_dump()
    )

    agent.note(f"✅ Fraud: Risk={result.fraud_risk_score:.2f}, Similar fraud={fraud_pattern_count}")
    return result


async def _verify_policy_coverage(claim: Claim) -> PolicyAssessment:
    """Internal: Verify policy coverage."""
    agent.note(f"📄 Verifying policy coverage for {claim.claim_id}")

    prompt = f"""You are a policy compliance specialist reviewing claim {claim.claim_id}.

POLICY INFORMATION:
- Policy Type: {claim.policyholder.policy_type}
- Coverage Limit: ${claim.policyholder.coverage_limit:,}
- Claimed Amount: ${claim.total_claimed_amount:,.2f}

CLAIM DETAILS:
- Diagnosis: {claim.diagnosis_name}
- Treatment: {', '.join([p.name for p in claim.procedures[:5]])}
- Provider Type: {claim.provider.type}

EVALUATE:
1. Is this diagnosis/treatment covered under a {claim.policyholder.policy_type} plan?
2. Are there any exclusions that apply?
3. Does the claimed amount exceed policy limits?

Common Coverage Rules:
- PPO plans: Comprehensive coverage, in-network preferred
- HMO plans: Requires network providers
- High-deductible plans: Coverage after deductible met

Provide detailed reasoning for coverage determination.
"""

    result = await agent.ai(prompt, schema=PolicyAssessment)
    result.claim_id = claim.claim_id

    # Store in memory
    await agent.memory.set(
        key=f"claim:{claim.claim_id}:policy_assessment",
        data=result.model_dump()
    )

    agent.note(f"✅ Policy: {'COVERED' if result.covered_under_policy else 'NOT COVERED'}")
    return result


async def _evaluate_cost_reasonableness(claim: Claim) -> CostAssessment:
    """Internal: Evaluate cost reasonableness."""
    agent.note(f"💰 Evaluating cost reasonableness for {claim.claim_id}")

    # Get cost benchmarks
    benchmarks = get_cost_benchmarks(claim.diagnosis_code, claim.severity)
    variance = calculate_cost_variance(claim.total_claimed_amount, benchmarks['typical'])

    # Retrieve other assessments from memory
    medical_data = await agent.memory.get(f"claim:{claim.claim_id}:medical_assessment")
    fraud_data = await agent.memory.get(f"claim:{claim.claim_id}:fraud_assessment")

    prompt = f"""You are a cost analyst evaluating claim {claim.claim_id}.

COST INFORMATION:
- Claimed Amount: ${claim.total_claimed_amount:,.2f}
- Expected Range: ${benchmarks['min']:,.2f} - ${benchmarks['max']:,.2f}
- Typical Cost: ${benchmarks['typical']:,.2f}
- Variance: {variance:.1f}%

PROCEDURES:
{chr(10).join([f"- {p.name}: ${p.cost:,.2f}" for p in claim.procedures])}

CONTEXT FROM OTHER ASSESSMENTS:
Medical: {"Necessary" if medical_data and medical_data.get('is_medically_necessary') else "Pending"}
Fraud Risk: {f"{fraud_data.get('fraud_risk_score'):.2f}" if fraud_data else "Pending"}

EVALUATE:
1. Is the cost reasonable given the diagnosis and severity?
2. Does provider reputation explain any cost variance?
3. Are there legitimate reasons for costs above typical range?
4. Does medical necessity support the cost level?

Provide detailed reasoning for cost assessment.
"""

    result = await agent.ai(prompt, schema=CostAssessment)
    result.claim_id = claim.claim_id
    result.expected_range_min = benchmarks['min']
    result.expected_range_max = benchmarks['max']
    result.variance_percentage = variance

    # Store in memory
    await agent.memory.set(
        key=f"claim:{claim.claim_id}:cost_assessment",
        data=result.model_dump()
    )

    agent.note(f"✅ Cost: {'REASONABLE' if result.cost_reasonable else 'QUESTIONABLE'}")
    return result


# ============================================================================
# PUBLIC ENDPOINT - Main Adjudication
# ============================================================================

@agent.reasoner(tags=["main", "adjudication", "coordinator"])
async def adjudicate_claim(claim_id: str) -> dict:
    """
    MAIN ENDPOINT: Complete claims adjudication

    Runs all specialist assessments in sequence and synthesizes final decision.
    Shows as single unified workflow in AgentField UI.

    Args:
        claim_id: The claim ID to adjudicate

    Returns:
        Complete AdjudicationResult with all assessments
    """
    start_time = time.time()

    agent.note(f"🎯 Starting unified adjudication for {claim_id}")

    # Load claim
    claim = load_claim(claim_id)

    # Run all specialist assessments (internal functions)
    agent.note("🔄 Running specialist assessments...")

    medical = await _evaluate_medical_necessity(claim)
    fraud = await _detect_fraud_patterns(claim)
    policy = await _verify_policy_coverage(claim)
    cost = await _evaluate_cost_reasonableness(claim)

    # Synthesize final decision
    agent.note("🤔 Synthesizing final decision...")

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

    decision = await agent.ai(decision_prompt, schema=FinalDecision)
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
        agents_consulted=['medical', 'fraud', 'policy', 'cost', 'coordinator']
    )

    # Store in global memory for audit trail
    await agent.memory.global_scope.set(
        key=f"adjudication:{claim_id}:final",
        data=result.model_dump()
    )

    agent.note(
        f"✅ ADJUDICATION COMPLETE: {decision.decision} "
        f"(confidence: {decision.confidence:.2f}, time: {processing_time}ms)"
    )

    return result.model_dump()


# ============================================================================
# OPTIONAL: Individual Assessment Endpoints (for testing)
# ============================================================================

@agent.reasoner(tags=["medical"])
async def assess_medical_necessity(claim_id: str) -> dict:
    """Individual medical assessment endpoint."""
    claim = load_claim(claim_id)
    result = await _evaluate_medical_necessity(claim)
    return result.model_dump()


@agent.reasoner(tags=["fraud"])
async def analyze_fraud_risk(claim_id: str) -> dict:
    """Individual fraud detection endpoint."""
    claim = load_claim(claim_id)
    result = await _detect_fraud_patterns(claim)
    return result.model_dump()


@agent.reasoner(tags=["policy"])
async def check_policy_coverage(claim_id: str) -> dict:
    """Individual policy check endpoint."""
    claim = load_claim(claim_id)
    result = await _verify_policy_coverage(claim)
    return result.model_dump()


@agent.reasoner(tags=["cost"])
async def analyze_cost(claim_id: str) -> dict:
    """Individual cost analysis endpoint."""
    claim = load_claim(claim_id)
    result = await _evaluate_cost_reasonableness(claim)
    return result.model_dump()


# ============================================================================
# RUN AGENT
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🏥 CLAIMS ADJUDICATION AGENT (Unified)")
    print("=" * 70)
    print(f"\nAgent: claims-adjudicator")
    print(f"Model: {AI_MODEL}")
    print(f"Temperature: {AI_TEMPERATURE}")
    print("\nFeatures:")
    print("  ✅ Unified workflow (single execution flow)")
    print("  ✅ Memory-based coordination")
    print("  ✅ Vector search for fraud detection")
    print("  ✅ Multi-step reasoning (medical, fraud, policy, cost)")
    print("  ✅ Structured outputs via Pydantic")
    print("\nMain Endpoint:")
    print("  - adjudicate_claim ⭐ (runs all assessments)")
    print("\nIndividual Endpoints (optional):")
    print("  - assess_medical_necessity")
    print("  - analyze_fraud_risk")
    print("  - check_policy_coverage")
    print("  - analyze_cost")
    print("\n" + "=" * 70)
    print("Starting agent...\n")

    agent.run()
