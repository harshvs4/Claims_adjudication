"""
Utility helper functions
"""

from datetime import datetime


def format_currency(amount: float) -> str:
    """Format amount as currency string."""
    return f"${amount:,.2f}"


def calculate_days_between(date1_str: str, date2_str: str, date_format: str = "%Y-%m-%d") -> int:
    """Calculate days between two date strings."""
    date1 = datetime.strptime(date1_str, date_format)
    date2 = datetime.strptime(date2_str, date_format)
    return abs((date2 - date1).days)


def get_claim_age_days(claim_submission_date: str) -> int:
    """Get age of claim in days from submission to now."""
    submission = datetime.strptime(claim_submission_date, "%Y-%m-%d")
    return (datetime.now() - submission).days


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format float as percentage string."""
    return f"{value:.{decimals}f}%"