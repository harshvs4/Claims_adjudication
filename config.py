"""
Configuration for Claims Adjudication System
"""

import os
from dotenv import load_dotenv

load_dotenv()

# AgentField Configuration
AGENTFIELD_SERVER = os.getenv("AGENTFIELD_SERVER", "http://localhost:8080")
AGENT_NODE_ID = "claims-adjudicator"
AGENT_VERSION = "1.0.0"
DEV_MODE = True

# AI Model Configuration
AI_MODEL = os.getenv("AI_MODEL", "anthropic/claude-sonnet-4-20250514")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.3"))

# Data Configuration
DATA_PATH = os.getenv("DATA_PATH", "data/synthetic_claims.json")

# Cost Benchmarks (typical costs by diagnosis)
COST_BENCHMARKS = {
    'J18.9': 8000,      # Pneumonia
    'I21.9': 45000,     # Acute Myocardial Infarction
    'S72.001A': 35000,  # Femur Fracture
    'M54.5': 2500,      # Low Back Pain
    'K80.20': 15000,    # Gallstone
    'E11.9': 3000,      # Type 2 Diabetes
    'J45.909': 1500,    # Asthma
    'N18.3': 25000,     # Chronic Kidney Disease
    'C50.919': 85000,   # Breast Cancer
    'M17.11': 18000,    # Knee Osteoarthritis
}

# Severity Multipliers
SEVERITY_MULTIPLIERS = {
    'mild': 0.7,
    'moderate': 1.0,
    'severe': 1.5
}

# Fraud Detection Thresholds
FRAUD_SCORE_THRESHOLDS = {
    'low': 0.3,
    'medium': 0.5,
    'high': 0.7
}

# Memory Scopes
MEMORY_SCOPE_SESSION = "session"
MEMORY_SCOPE_GLOBAL = "global"