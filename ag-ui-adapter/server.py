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

                # Send acknowledgment
                await manager.send_event(
                    session_id,
                    create_event("session_started", session_id, {
                        "claim_id": claim_id,
                        "intent_type": intent_type,
                        "message": f"Starting {intent_type} adjudication for claim {claim_id}"
                    })
                )

                # Start adjudication in background
                asyncio.create_task(
                    run_adjudication(session_id, claim_id, intent_type)
                )

            elif data.get("type") == "ping":
                await manager.send_event(
                    session_id,
                    create_event("pong", session_id, {})
                )

    except WebSocketDisconnect:
        manager.disconnect(session_id)


async def run_adjudication(session_id: str, claim_id: str, intent_type: str = "full"):
    """Run the claims adjudication workflow and stream events

    Args:
        session_id: WebSocket session ID
        claim_id: Claim ID to process
        intent_type: Type of analysis - 'full', 'medical', 'fraud', 'policy', or 'cost'
    """

    try:
        # Map intent types to stages
        stage_map = {
            'full': ['medical', 'fraud', 'policy', 'cost', 'decision'],
            'medical': ['medical'],
            'fraud': ['fraud'],
            'policy': ['policy'],
            'cost': ['cost'],
        }

        stages = stage_map.get(intent_type, ['medical', 'fraud', 'policy', 'cost', 'decision'])

        # Send workflow started event
        await manager.send_event(
            session_id,
            create_event("workflow_started", session_id, {
                "claim_id": claim_id,
                "workflow": f"{intent_type}_adjudication",
                "stages": stages
            })
        )

        # Call AgentField API
        async with httpx.AsyncClient(timeout=120.0) as client:

            # Determine which endpoint to call based on intent
            if intent_type == "full":
                # Call full workflow orchestrator
                url = f"{AGENTFIELD_API}/execute/workflow-orchestrator.adjudicate_claim"
                agent_name = "workflow-orchestrator"
            else:
                # Call individual agent
                agent_map = {
                    'medical': ('medical-reasoner', 'evaluate_medical_necessity'),
                    'fraud': ('fraud-detector', 'detect_fraud_patterns'),
                    'policy': ('policy-checker', 'verify_policy_coverage'),
                    'cost': ('cost-analyzer', 'evaluate_cost_reasonableness'),
                }
                agent_id, reasoner = agent_map[intent_type]
                url = f"{AGENTFIELD_API}/execute/{agent_id}.{reasoner}"
                agent_name = agent_id

            # Send stage started event
            stage_name = stages[0] if stages else intent_type
            await manager.send_event(
                session_id,
                create_event("stage_started", session_id, {
                    "stage": stage_name,
                    "agent": agent_name,
                    "message": f"Processing {intent_type} assessment..."
                })
            )

            # Start the execution
            response = await client.post(
                url,
                json={"input": {"claim_id": claim_id}}
            )

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

                if intent_type == "full":
                    # Full workflow - parse all assessments
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
                    # Individual agent - send single stage completion
                    await manager.send_event(
                        session_id,
                        create_event("stage_completed", session_id, {
                            "stage": intent_type,
                            "assessment": assessment_result
                        })
                    )

                    # Send workflow completed (no final decision for individual assessments)
                    await manager.send_event(
                        session_id,
                        create_event("workflow_completed", session_id, {
                            "claim_id": claim_id,
                            "intent_type": intent_type,
                            "assessment": assessment_result
                        })
                    )

            else:
                # Handle failure
                await manager.send_event(
                    session_id,
                    create_event("error", session_id, {
                        "error": "Adjudication failed",
                        "details": result.get("error", "Unknown error")
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
