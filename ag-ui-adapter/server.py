"""
AG-UI Adapter for AgentField
Converts AgentField REST API to AG-UI event-based protocol
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
import asyncio
import json
import uuid
from datetime import datetime
import logging
import os
from anthropic import Anthropic
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file in parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AG-UI Adapter for Claims Adjudication")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AgentField configuration
AGENTFIELD_API = "http://localhost:8080/api/v1"


class ClaimRequest(BaseModel):
    claim_id: str
    session_id: Optional[str] = None


class IntentDetectionRequest(BaseModel):
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class IntentDetectionResponse(BaseModel):
    claim_id: Optional[str]
    intent_type: str  # 'full', 'medical', 'fraud', 'policy', 'cost', or 'unknown'
    requested_assessments: List[str]  # List of assessments to run
    confidence: float  # 0.0 to 1.0
    explanation: str  # Human-readable explanation


class AGUIEvent(BaseModel):
    """AG-UI protocol event"""
    type: str
    session_id: str
    timestamp: str
    data: Dict[str, Any]


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"✅ WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"❌ WebSocket disconnected: {session_id}")

    async def send_event(self, session_id: str, event: AGUIEvent):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(event.model_dump())
            logger.debug(f"📤 Sent event {event.type} to {session_id}")


manager = ConnectionManager()


def create_event(event_type: str, session_id: str, data: Dict[str, Any]) -> AGUIEvent:
    """Create an AG-UI event"""
    return AGUIEvent(
        type=event_type,
        session_id=session_id,
        timestamp=datetime.utcnow().isoformat(),
        data=data
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check AgentField connectivity
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{AGENTFIELD_API}/nodes")
            agentfield_status = "connected" if response.status_code == 200 else "error"
            agent_count = len(response.json()) if response.status_code == 200 else 0
    except Exception as e:
        agentfield_status = "disconnected"
        agent_count = 0
        logger.error(f"AgentField health check failed: {e}")

    return {
        "status": "healthy",
        "service": "ag-ui-adapter",
        "agentfield": {
            "status": agentfield_status,
            "url": AGENTFIELD_API,
            "agents": agent_count
        },
        "websocket_connections": len(manager.active_connections)
    }


@app.post("/api/detect-intent")
async def detect_intent(request: IntentDetectionRequest) -> IntentDetectionResponse:
    """
    LLM-powered intent detection endpoint
    Uses Claude to parse user queries and extract claim ID + requested assessments
    """
    try:
        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not set")
            return IntentDetectionResponse(
                claim_id=None,
                intent_type="unknown",
                requested_assessments=[],
                confidence=0.0,
                explanation="API key not configured"
            )

        client = Anthropic(api_key=api_key)

        # Build the prompt for Claude
        system_prompt = """You are an intent detection system for a health insurance claims adjudication platform.

Your job is to parse user queries and extract:
1. The claim ID (format: CLM followed by digits, e.g., CLM10001)
2. What specific assessments the user wants to run

Available assessments:
- medical: Medical necessity assessment
- fraud: Fraud detection analysis
- policy: Policy coverage verification
- cost: Cost reasonableness analysis

Respond with a JSON object:
{
  "claim_id": "CLM10001" or null,
  "intent_type": "multi" | "medical" | "fraud" | "policy" | "cost" | "full" | "unknown",
  "requested_assessments": ["fraud", "cost"],
  "confidence": 0.0 to 1.0,
  "explanation": "Brief explanation of what was detected"
}

Rules:
- If user asks for ALL assessments or "complete/full adjudication", set intent_type="full" and requested_assessments=["medical", "fraud", "policy", "cost"]
- If user asks for 2-3 specific assessments (e.g., "fraud and cost"), set intent_type="multi" and list only those in requested_assessments (e.g., ["fraud", "cost"])
- If user asks for 1 specific assessment, set intent_type to that assessment (e.g., "fraud") and requested_assessments=[that assessment]
- If unclear or no claim ID, set intent_type="unknown" and requested_assessments=[]
- Only include assessments that were explicitly requested or clearly implied
- confidence should reflect how certain you are about the parsing

Examples:
- "show me fraud and cost analysis of CLM10001" → intent_type="multi", requested_assessments=["fraud", "cost"]
- "check medical necessity for CLM10002" → intent_type="medical", requested_assessments=["medical"]
- "run full adjudication on CLM10003" → intent_type="full", requested_assessments=["medical", "fraud", "policy", "cost"]
- "fraud, policy, and cost for CLM10004" → intent_type="multi", requested_assessments=["fraud", "policy", "cost"]"""

        user_message = f"User query: {request.query}"

        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )

        # Parse response
        response_text = message.content[0].text
        logger.info(f"Claude response: {response_text}")

        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            intent_data = json.loads(json_match.group())
            return IntentDetectionResponse(**intent_data)
        else:
            logger.error(f"Failed to parse JSON from Claude response: {response_text}")
            return IntentDetectionResponse(
                claim_id=None,
                intent_type="unknown",
                requested_assessments=[],
                confidence=0.0,
                explanation="Failed to parse intent"
            )

    except Exception as e:
        logger.error(f"Intent detection failed: {e}", exc_info=True)
        return IntentDetectionResponse(
            claim_id=None,
            intent_type="unknown",
            requested_assessments=[],
            confidence=0.0,
            explanation=f"Error: {str(e)}"
        )


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for AG-UI protocol"""
    await manager.connect(session_id, websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") == "start_adjudication":
                claim_id = data.get("claim_id")
                intent_type = data.get("intent_type", "full")  # Default to full workflow
                requested_assessments = data.get("requested_assessments", [])  # List of specific assessments

                # Send acknowledgment
                await manager.send_event(
                    session_id,
                    create_event("session_started", session_id, {
                        "claim_id": claim_id,
                        "intent_type": intent_type,
                        "requested_assessments": requested_assessments,
                        "message": f"Starting {intent_type} adjudication for claim {claim_id}"
                    })
                )

                # Start adjudication in background
                asyncio.create_task(
                    run_adjudication(session_id, claim_id, intent_type, requested_assessments)
                )

            elif data.get("type") == "ping":
                await manager.send_event(
                    session_id,
                    create_event("pong", session_id, {})
                )

    except WebSocketDisconnect:
        manager.disconnect(session_id)


async def run_adjudication(session_id: str, claim_id: str, intent_type: str = "full", requested_assessments: list = None):
    """Run the claims adjudication workflow and stream events

    Args:
        session_id: WebSocket session ID
        claim_id: Claim ID to process
        intent_type: Type of analysis - 'full', 'multi', 'medical', 'fraud', 'policy', or 'cost'
        requested_assessments: List of specific assessments to run (e.g., ['fraud', 'cost'])
    """

    try:
        # Determine which assessments to run
        if intent_type == "full":
            # Full workflow: all 4 agents + final decision
            assessments_to_run = ['medical', 'fraud', 'policy', 'cost']
            run_final_decision = True
        elif intent_type == "multi":
            # Multi-agent: only the requested assessments, no final decision
            assessments_to_run = requested_assessments or []
            run_final_decision = False
        elif intent_type in ['medical', 'fraud', 'policy', 'cost']:
            # Single assessment
            assessments_to_run = [intent_type]
            run_final_decision = False
        else:
            # Default fallback
            assessments_to_run = ['medical', 'fraud', 'policy', 'cost']
            run_final_decision = True

        stages = assessments_to_run + (['decision'] if run_final_decision else [])

        # Send workflow started event
        await manager.send_event(
            session_id,
            create_event("workflow_started", session_id, {
                "claim_id": claim_id,
                "workflow": f"{intent_type}_adjudication",
                "stages": stages,
                "requested_assessments": assessments_to_run
            })
        )

        # Agent mapping
        agent_map = {
            'medical': ('medical-reasoner', 'evaluate_medical_necessity'),
            'fraud': ('fraud-detector', 'detect_fraud_patterns'),
            'policy': ('policy-checker', 'verify_policy_coverage'),
            'cost': ('cost-analyzer', 'evaluate_cost_reasonableness'),
        }

        async with httpx.AsyncClient(timeout=120.0) as client:

            if run_final_decision:
                # Full workflow: Call workflow orchestrator
                url = f"{AGENTFIELD_API}/execute/workflow-orchestrator.adjudicate_claim"

                await manager.send_event(
                    session_id,
                    create_event("stage_started", session_id, {
                        "stage": "full",
                        "agent": "workflow-orchestrator",
                        "message": "Running full adjudication with all agents..."
                    })
                )

                response = await client.post(url, json={"input": {"claim_id": claim_id}})

                if response.status_code != 200:
                    await manager.send_event(
                        session_id,
                        create_event("error", session_id, {
                            "error": f"AgentField API error: {response.status_code}",
                            "details": response.text
                        })
                    )
                    return

                result = response.json()
                if result.get("status") == "succeeded":
                    assessment_result = result.get("result", {})

                    # Parse all assessments
                    stage_pairs = [
                        ("medical", "medical_assessment"),
                        ("fraud", "fraud_assessment"),
                        ("policy", "policy_assessment"),
                        ("cost", "cost_assessment"),
                    ]

                    for stage_name, assessment_key in stage_pairs:
                        assessment = assessment_result.get(assessment_key, {})
                        await manager.send_event(
                            session_id,
                            create_event("stage_completed", session_id, {
                                "stage": stage_name,
                                "assessment": assessment
                            })
                        )
                        await asyncio.sleep(0.5)  # Simulate streaming

                    # Send final decision
                    final_decision = assessment_result.get("final_decision", {})
                    await manager.send_event(
                        session_id,
                        create_event("workflow_completed", session_id, {
                            "claim_id": claim_id,
                            "decision": final_decision.get("decision"),
                            "approved_amount": final_decision.get("approved_amount"),
                            "confidence": final_decision.get("confidence"),
                            "reasoning": final_decision.get("reasoning"),
                            "key_factors": final_decision.get("key_factors", []),
                            "full_result": assessment_result
                        })
                    )
                else:
                    await manager.send_event(
                        session_id,
                        create_event("error", session_id, {
                            "error": "Full adjudication failed",
                            "details": result.get("error", "Unknown error")
                        })
                    )

            else:
                # Multi-agent or single agent: Call each requested agent sequentially
                all_assessments = {}

                for assessment_type in assessments_to_run:
                    if assessment_type not in agent_map:
                        continue

                    agent_id, reasoner = agent_map[assessment_type]
                    url = f"{AGENTFIELD_API}/execute/{agent_id}.{reasoner}"

                    # Send stage started event
                    await manager.send_event(
                        session_id,
                        create_event("stage_started", session_id, {
                            "stage": assessment_type,
                            "agent": agent_id,
                            "message": f"Running {assessment_type} assessment..."
                        })
                    )

                    # Call the agent
                    response = await client.post(url, json={"input": {"claim_id": claim_id}})

                    if response.status_code != 200:
                        await manager.send_event(
                            session_id,
                            create_event("error", session_id, {
                                "error": f"{assessment_type} agent error: {response.status_code}",
                                "details": response.text
                            })
                        )
                        continue

                    result = response.json()
                    if result.get("status") == "succeeded":
                        assessment_result = result.get("result", {})
                        all_assessments[assessment_type] = assessment_result

                        # Send stage completed event
                        await manager.send_event(
                            session_id,
                            create_event("stage_completed", session_id, {
                                "stage": assessment_type,
                                "assessment": assessment_result
                            })
                        )
                        await asyncio.sleep(0.5)  # Simulate streaming
                    else:
                        await manager.send_event(
                            session_id,
                            create_event("error", session_id, {
                                "error": f"{assessment_type} assessment failed",
                                "details": result.get("error", "Unknown error")
                            })
                        )

                # Send workflow completed (no final decision)
                await manager.send_event(
                    session_id,
                    create_event("workflow_completed", session_id, {
                        "claim_id": claim_id,
                        "intent_type": intent_type,
                        "assessments": all_assessments,
                        "requested_assessments": assessments_to_run
                    })
                )

    except Exception as e:
        await manager.send_event(
            session_id,
            create_event("error", session_id, {
                "error": str(e),
                "traceback": str(e.__traceback__)
            })
        )


@app.post("/adjudicate")
async def adjudicate_claim(request: ClaimRequest):
    """
    REST endpoint for claim adjudication (non-streaming)
    For compatibility with non-WebSocket clients
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{AGENTFIELD_API}/execute/workflow-orchestrator.adjudicate_claim",
                json={"input": {"claim_id": request.claim_id}}
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"AgentField API error: {response.status_code}",
                    "details": response.text
                }

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("🔌 AG-UI ADAPTER SERVER")
    print("=" * 70)
    print("\nStarting AG-UI adapter for Claims Adjudication...")
    print("\nEndpoints:")
    print("  WebSocket: ws://localhost:8000/ws/{session_id}")
    print("  REST API:  http://localhost:8000/adjudicate")
    print("  Health:    http://localhost:8000/health")
    print("\nCORS enabled for: http://localhost:3000")
    print("=" * 70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
