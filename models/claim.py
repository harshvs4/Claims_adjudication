"""
Pydantic models for claim data structures
"""

from pydantic import BaseModel
from typing import List, Optional


class Policyholder(BaseModel):
    policyholder_id: str
    name: str
    age: int
    gender: str
    policy_type: str
    coverage_limit: int
    policy_start_date: str
    prior_claims_count: int


class Provider(BaseModel):
    id: str
    name: str
    type: str
    reputation: str


class Procedure(BaseModel):
    code: str
    name: str
    cost: float


class Claim(BaseModel):
    claim_id: str
    claim_type: Optional[str] = None
    policyholder: Policyholder
    incident_date: str
    claim_submission_date: str
    diagnosis_code: str
    diagnosis_name: str
    severity: str
    provider: Provider
    procedures: List[Procedure]
    total_claimed_amount: float
    medical_notes: str
    fraud_indicators: Optional[List[str]] = []
    complexity_factors: Optional[List[str]] = []
    expected_outcome: Optional[str] = None