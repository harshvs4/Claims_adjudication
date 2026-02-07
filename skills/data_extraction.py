"""
Data extraction skills - deterministic functions for loading and extracting claim data
"""

import json
from models.claim import Claim
from config import DATA_PATH


def load_claim(claim_id: str, data_path: str = None) -> Claim:
    """
    Load a claim by ID from the dataset.
    
    Args:
        claim_id: The claim ID to load
        data_path: Optional custom path to claims data
        
    Returns:
        Claim object
        
    Raises:
        ValueError: If claim not found
    """
    path = data_path or DATA_PATH
    
    with open(path, 'r') as f:
        claims = json.load(f)
    
    claim_data = next((c for c in claims if c['claim_id'] == claim_id), None)
    
    if not claim_data:
        raise ValueError(f"Claim {claim_id} not found in dataset")
    
    return Claim(**claim_data)


def extract_claim_summary(claim: Claim) -> dict:
    """
    Extract key claim information for quick reference.
    
    Args:
        claim: Claim object
        
    Returns:
        Dictionary with key claim details
    """
    return {
        'claim_id': claim.claim_id,
        'patient_age': claim.policyholder.age,
        'diagnosis': claim.diagnosis_name,
        'diagnosis_code': claim.diagnosis_code,
        'severity': claim.severity,
        'provider_name': claim.provider.name,
        'provider_reputation': claim.provider.reputation,
        'total_amount': claim.total_claimed_amount,
        'num_procedures': len(claim.procedures),
        'prior_claims': claim.policyholder.prior_claims_count,
    }


def get_claim_description(claim: Claim) -> str:
    """
    Create semantic description for vector search.
    
    Args:
        claim: Claim object
        
    Returns:
        String description suitable for embedding
    """
    return f"""
Diagnosis: {claim.diagnosis_name} ({claim.diagnosis_code})
Severity: {claim.severity}
Provider: {claim.provider.name} (Reputation: {claim.provider.reputation})
Cost: ${claim.total_claimed_amount:,.2f}
Procedures: {', '.join([p.name for p in claim.procedures[:3]])}
Patient Age: {claim.policyholder.age}
Prior Claims: {claim.policyholder.prior_claims_count}
""".strip()