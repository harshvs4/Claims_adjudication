"""
Fraud scoring skills - deterministic fraud detection logic
"""

from datetime import datetime
from models.claim import Claim
from config import FRAUD_SCORE_THRESHOLDS


def calculate_fraud_score(claim: Claim) -> dict:
    """
    Calculate deterministic fraud indicators based on claim patterns.
    
    Args:
        claim: Claim object
        
    Returns:
        Dictionary with fraud score and flags
    """
    score = 0.0
    flags = []
    
    # Provider reputation check
    if claim.provider.reputation == 'suspicious':
        score += 0.4
        flags.append('Provider has suspicious reputation history')
    
    # Cost inflation check
    typical_costs = {
        'mild': 3000,
        'moderate': 15000,
        'severe': 50000
    }
    expected = typical_costs.get(claim.severity, 15000)
    
    if claim.total_claimed_amount > expected * 2:
        score += 0.3
        flags.append(
            f'Cost ${claim.total_claimed_amount:,.0f} exceeds '
            f'typical ${expected:,.0f} by >100%'
        )
    
    # Claim frequency check
    if claim.policyholder.prior_claims_count > 5:
        score += 0.2
        flags.append(
            f'High claim frequency: {claim.policyholder.prior_claims_count} prior claims'
        )
    
    # Filing speed check
    incident = datetime.strptime(claim.incident_date, '%Y-%m-%d')
    submission = datetime.strptime(claim.claim_submission_date, '%Y-%m-%d')
    days_to_file = (submission - incident).days
    
    if days_to_file <= 1:
        score += 0.1
        flags.append(f'Claim filed within {days_to_file} day(s) - unusually rapid')
    
    return {
        'fraud_score': min(score, 1.0),
        'flags': flags,
        'days_to_file': days_to_file
    }


def assess_fraud_risk_level(fraud_score: float) -> str:
    """
    Categorize fraud risk based on score.
    
    Args:
        fraud_score: Fraud score from 0-1
        
    Returns:
        Risk level: LOW, MEDIUM, or HIGH
    """
    if fraud_score >= FRAUD_SCORE_THRESHOLDS['high']:
        return 'HIGH'
    elif fraud_score >= FRAUD_SCORE_THRESHOLDS['medium']:
        return 'MEDIUM'
    else:
        return 'LOW'