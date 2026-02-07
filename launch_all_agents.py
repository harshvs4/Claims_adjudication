#!/usr/bin/env python
"""
Launch all claims adjudication agents in one process
Starts all 5 agents as background threads
"""

import sys
from pathlib import Path
import asyncio
import signal
from threading import Thread
import time

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agentfield import Agent, AIConfig
from config import AGENTFIELD_SERVER, AI_MODEL, AI_TEMPERATURE, DEV_MODE

# Import all agent modules
from agents.medical_agent import medical_agent
from agents.fraud_agent import fraud_agent
from agents.policy_agent import policy_agent
from agents.cost_agent import cost_agent
from agents.workflow_orchestrator import orchestrator


def run_agent(agent: Agent, name: str):
    """Run an agent in a separate thread."""
    try:
        print(f"🚀 Starting {name}...")
        agent.run()
    except Exception as e:
        print(f"❌ Error in {name}: {e}")


def main():
    """Launch all agents."""
    print("=" * 70)
    print("🏥 CLAIMS ADJUDICATION - MULTI-AGENT LAUNCHER")
    print("=" * 70)
    print("\nStarting all agents:")
    print("  1. medical-reasoner")
    print("  2. fraud-detector")
    print("  3. policy-checker")
    print("  4. cost-analyzer")
    print("  5. workflow-orchestrator")
    print("\n" + "=" * 70)
    print("Press Ctrl+C to stop all agents")
    print("=" * 70 + "\n")

    # Create threads for each agent
    threads = []

    agents_config = [
        (medical_agent, "medical-reasoner"),
        (fraud_agent, "fraud-detector"),
        (policy_agent, "policy-checker"),
        (cost_agent, "cost-analyzer"),
    ]

    # Start specialist agents first
    for agent, name in agents_config:
        thread = Thread(target=run_agent, args=(agent, name), daemon=True)
        thread.start()
        threads.append(thread)
        time.sleep(1)  # Stagger startup

    # Start orchestrator last (needs specialists to be ready)
    print("\n⏳ Waiting for specialist agents to initialize...")
    time.sleep(3)

    print("🚀 Starting workflow-orchestrator...")
    orchestrator_thread = Thread(target=run_agent, args=(orchestrator, "workflow-orchestrator"), daemon=True)
    orchestrator_thread.start()
    threads.append(orchestrator_thread)

    print("\n" + "=" * 70)
    print("✅ ALL AGENTS RUNNING!")
    print("=" * 70)
    print("\n📊 AgentField UI: http://localhost:8080")
    print("\n🧪 Test command:")
    print("curl -X POST http://localhost:8080/api/v1/execute/workflow-orchestrator.adjudicate_claim \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"input\": {\"claim_id\": \"CLM10001\"}}'")
    print("\n" + "=" * 70)
    print("📝 Logs will appear below...")
    print("=" * 70 + "\n")

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down all agents...")
        print("✅ Agents stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
