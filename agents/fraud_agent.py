"""
Fraud Detector Agent - Independent agent for fraud detection with vector search
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentfield import Agent, AIConfig
from config import AGENTFIELD_SERVER, AI_MODEL, AI_TEMPERATURE, DEV_MODE
from models.claim import Claim
from models.decision import FraudAssessment
from skills.data_extraction import load_claim, get_claim_description
from skills.fraud_scoring import calculate_fraud_score
from fastembed import TextEmbedding

# Initialize embedding model
_embed_model = TextEmbedding("BAAI/bge-small-en-v1.5")


def _embed(text: str) -> list:
    """Generate embedding vector from text."""
    return list(_embed_model.embed([text]))[0].tolist()


# Create independent fraud agent
fraud_agent = Agent(
    node_id="fraud-detector",
    agentfield_server=AGENTFIELD_SERVER,
    version="1.0.0",
    dev_mode=DEV_MODE,
    ai_config=AIConfig(
        model=AI_MODEL,
        temperature=AI_TEMPERATURE,
    ),
)


@fraud_agent.reasoner(tags=["fraud", "detection", "vector-search"])
async def detect_fraud_patterns(claim_id: str) -> dict:
    """
    Detect fraud using deterministic scoring, AI analysis, and vector search.

    Args:
        claim_id: The claim ID to evaluate

    Returns:
        FraudAssessment as dict
    """
    fraud_agent.note(f"🔍 Fraud detector analyzing {claim_id}")

    # Load claim
    claim = load_claim(claim_id)

    # Get deterministic fraud indicators
    indicators = calculate_fraud_score(claim)

    # Retrieve medical assessment from shared memory
    medical_data = await fraud_agent.memory.get(f"claim:{claim_id}:medical_assessment")

    # Create semantic representation for vector search
    claim_description = get_claim_description(claim)

    # Vector-based similar claim search using fastembed
    similar_claims = []
    fraud_pattern_count = 0
    similar_details = []

    claim_embedding = _embed(claim_description)

    await fraud_agent.memory.set_vector(
        key=claim_id,
        embedding=claim_embedding,
        metadata={
            "claim_id": claim_id,
            "diagnosis": claim.diagnosis_name,
            "provider": claim.provider.name,
            "provider_reputation": claim.provider.reputation,
            "amount": claim.total_claimed_amount,
            "fraud_score": indicators['fraud_score'],
            "actual_type": getattr(claim, 'claim_type', 'UNKNOWN')
        }
    )

    similar_claims = await fraud_agent.memory.similarity_search(
        query_embedding=claim_embedding,
        top_k=5
    )

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

CLAIM UNDER REVIEW: {claim_id}

CLAIM DETAILS:
- Diagnosis: {claim.diagnosis_name} ({claim.severity} severity)
- Provider: {claim.provider.name} (Reputation: {claim.provider.reputation})
- Amount Claimed: ${claim.total_claimed_amount:,.2f}
- Patient: {claim.policyholder.age} years old

PROCEDURES BILLED:
{chr(10).join([f"  • {p.name}: ${p.cost:,.2f}" for p in claim.procedures])}

MEDICAL REVIEW FINDINGS:
{f"✓ Medical Necessity: {medical_data.get('is_medically_necessary')}" if medical_data else "⚠ Medical review pending"}
{f"  Medical Reasoning: {medical_data.get('reasoning', 'N/A')[:300]}" if medical_data else ""}

FRAUD INDICATORS:
- Preliminary Score: {indicators['fraud_score']:.2f} / 1.0
- Red Flags: {len(indicators['flags'])}
{chr(10).join([f"  • {flag}" for flag in indicators['flags']]) if indicators['flags'] else "  • No automatic red flags"}

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

    result = await fraud_agent.ai(
        prompt,
        schema=FraudAssessment
    )

    result.claim_id = claim_id
    result.similar_fraud_cases_found = fraud_pattern_count

    if fraud_pattern_count > 2:
        result.pattern_analysis = f"HIGH RISK: {fraud_pattern_count}/5 similar claims were fraud"
    elif fraud_pattern_count > 0:
        result.pattern_analysis = f"MODERATE RISK: {fraud_pattern_count}/5 similar claims were fraud"
    else:
        result.pattern_analysis = "LOW PATTERN RISK: No similar fraud cases found"

    # Store in shared memory
    await fraud_agent.memory.set(
        key=f"claim:{claim_id}:fraud_assessment",
        data=result.model_dump()
    )

    fraud_agent.note(
        f"✅ Fraud analysis complete: "
        f"Risk={result.fraud_risk_score:.2f}, "
        f"Similar fraud={fraud_pattern_count}"
    )

    return result.model_dump()


if __name__ == "__main__":
    print("=" * 70)
    print("🔍 FRAUD DETECTOR AGENT")
    print("=" * 70)
    print(f"\nAgent ID: fraud-detector")
    print(f"Model: {AI_MODEL}")
    print(f"Server: {AGENTFIELD_SERVER}")
    print("\nFeatures:")
    print("  ✅ Deterministic fraud scoring")
    print("  ✅ Vector similarity search")
    print("  ✅ AI pattern analysis")
    print("\nEndpoints:")
    print("  - detect_fraud_patterns")
    print("\n" + "=" * 70)
    print("Starting fraud detector agent...\n")

    fraud_agent.run()
