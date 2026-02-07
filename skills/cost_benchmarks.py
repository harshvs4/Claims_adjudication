"""
Cost benchmarking skills - deterministic cost analysis
"""

from config import COST_BENCHMARKS, SEVERITY_MULTIPLIERS


def get_cost_benchmarks(diagnosis_code: str, severity: str) -> dict:
    """
    Get typical cost ranges for a given diagnosis and severity.
    
    Args:
        diagnosis_code: ICD-10 diagnosis code
        severity: Severity level (mild, moderate, severe)
        
    Returns:
        Dictionary with min, max, and typical costs
    """
    # Get base cost for diagnosis
    base_cost = COST_BENCHMARKS.get(diagnosis_code, 15000)
    
    # Adjust for severity
    multiplier = SEVERITY_MULTIPLIERS.get(severity, 1.0)
    adjusted_cost = base_cost * multiplier
    
    # Calculate range (±30%)
    return {
        'min': adjusted_cost * 0.7,
        'max': adjusted_cost * 1.3,
        'typical': adjusted_cost
    }


def calculate_cost_variance(claimed_amount: float, typical_cost: float) -> float:
    """
    Calculate percentage variance from typical cost.
    
    Args:
        claimed_amount: The amount claimed
        typical_cost: The typical/expected cost
        
    Returns:
        Percentage variance (positive = over typical, negative = under)
    """
    if typical_cost == 0:
        return 0.0
    
    return ((claimed_amount - typical_cost) / typical_cost) * 100


def is_cost_reasonable(claimed_amount: float, cost_range: dict) -> bool:
    """
    Check if claimed amount falls within reasonable range.
    
    Args:
        claimed_amount: The amount claimed
        cost_range: Dictionary with 'min' and 'max' keys
        
    Returns:
        True if cost is within range, False otherwise
    """
    return cost_range['min'] <= claimed_amount <= cost_range['max']