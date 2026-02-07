"""
Fraud Detector - AI-powered fraud detection with vector search
"""

from agentfield import Agent
from models.claim import Claim
from models.decision import FraudAssessment
from skills.fraud_scoring import calculate_fraud_score
from skills.data_extraction import get_claim_description


async def detect_fraud_patterns(app: Agent, claim: Claim) -> FraudAssessment:
    """
    Detect fraud using deterministic scoring, AI analysis, and vector search.
    
    Args:
        app: AgentField Agent instance
        claim: Claim object to evaluate
        
    Returns:
        FraudAssessment with fraud risk analysis
    """
    
    await app.note(f"🔍 Fraud detector analyzing {claim.claim_id}")
    
    # Get deterministic fraud indicators
    indicators = calculate_fraud_score(claim)
    
    # Retrieve medical assessment from shared memory
    medical_data = await app.memory.get(f"claim:{claim.claim_id}:medical_assessment")
    
    # Create semantic representation for vector search
    claim_description = get_claim_description(claim)
    
    # Store this claim with vector embedding for future searches
    await app.memory.set_vector(
        id=claim.claim_id,
        embedding=claim_description,
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
    similar_claims = await app.memory.similarity_search(
        query=claim_description,
        top_k=5
    )
    
    # Analyze similar claims for fraud patterns
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
    
    result = await app.ai(
        prompt=prompt,
        schema=FraudAssessment
    )
    
    result.claim_id = claim.claim_id
    result.similar_fraud_cases_found = fraud_pattern_count
    
    if fraud_pattern_count > 2:
        result.pattern_analysis = f"HIGH RISK: {fraud_pattern_count}/5 similar claims were fraud"
    elif fraud_pattern_count > 0:
        result.pattern_analysis = f"MODERATE RISK: {fraud_pattern_count}/5 similar claims were fraud"
    else:
        result.pattern_analysis = "LOW PATTERN RISK: No similar fraud cases found"
    
    # Store in shared memory
    await app.memory.set(
        key=f"claim:{claim.claim_id}:fraud_assessment",
        value=result.model_dump()
    )
    
    await app.note(
        f"✅ Fraud analysis complete: "
        f"Risk={result.fraud_risk_score:.2f}, "
        f"Similar fraud={fraud_pattern_count}"
    )
    
    return result