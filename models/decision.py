"""
Pydantic models for adjudication decisions and assessments
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class DecisionType(str, Enum):
    APPROVE = "APPROVE"
    DENY = "DENY"
    INVESTIGATE = "INVESTIGATE"
    APPROVE_WITH_REVIEW = "APPROVE_WITH_REVIEW"


class MedicalAssessment(BaseModel):
    """Medical necessity evaluation"""
    claim_id: str
    is_medically_necessary: bool
    treatment_appropriate: bool
    reasoning: str
    confidence: float = Field(ge=0, le=1)
    over_treatment_detected: bool = False


class FraudAssessment(BaseModel):
    """Fraud risk evaluation"""
    claim_id: str
    fraud_risk_score: float = Field(ge=0, le=1)
    red_flags: List[str]
    reasoning: str
    recommendation: str
    similar_fraud_cases_found: int = 0
    pattern_analysis: Optional[str] = None


class PolicyAssessment(BaseModel):
    """Policy coverage evaluation"""
    claim_id: str
    covered_under_policy: bool
    exclusions_apply: List[str]
    coverage_limits_exceeded: bool
    reasoning: str


class CostAssessment(BaseModel):
    """Cost reasonableness evaluation"""
    claim_id: str
    cost_reasonable: bool
    expected_range_min: float
    expected_range_max: float
    variance_percentage: float
    reasoning: str


class FinalDecision(BaseModel):
    """Final adjudication decision"""
    claim_id: str
    decision: DecisionType
    approved_amount: Optional[float] = None
    denial_reason: Optional[str] = None
    investigation_required: bool = False
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    key_factors: List[str]


class AdjudicationResult(BaseModel):
    """Complete adjudication result with all assessments"""
    claim_id: str
    final_decision: FinalDecision
    medical_assessment: MedicalAssessment
    fraud_assessment: FraudAssessment
    policy_assessment: PolicyAssessment
    cost_assessment: CostAssessment
    processing_time_ms: int
    agents_consulted: List[str]